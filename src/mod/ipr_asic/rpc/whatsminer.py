# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import base64
import binascii
import datetime
import hashlib
import json
import logging
import re
from typing import Literal, TypeVar, final, override

from Crypto.Cipher import AES
from passlib.hash import md5_crypt
from pydantic import TypeAdapter, ValidationError
from pydantic_core import from_json

from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
)
from mod.ipr_asic.protocol.tcp import BaseTCPClient
from mod.ipr_asic.rpc.cgminer import CGMinerRPCLayer
from mod.ipr_asic.schemas.cgminer import Status
from mod.ipr_asic.schemas.models import (
    ActionResult,
    APIObject,
    BlinkStatus,
    MinerPoolConfig,
    PoolConfig,
)
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerCommand,
    BTMinerDevDetails,
    BTMinerDevice,
    BTMinerEncryptedCommand,
    BTMinerPool,
    BTMinerSummary,
    BTMinerSystemInfo,
    BTMinerV3Command,
    BTMinerV3CommandResponse,
    BTMinerV3DeviceInfo,
    BTMinerV3NetworkInfo,
    BTMinerV3Pool,
    BTMinerV3PoolConfig,
    BTMinerV3Status,
    BTMinerV3Summary,
    BTMinerV3SystemInfo,
    BTMinerVersion,
    Token,
    TokenResponse,
)
from mod.ipr_asic.settings import get_auth_list, set_alt_auth

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _crypt(word: str, salt: str) -> str:
    stdsalt = re.compile(r"\s*\$(\d+)\$([\w\./]*)\$")
    match = stdsalt.match(salt)
    if not match:
        raise ValueError("Invalid salt format")
    new_salt = match.group(2)
    return md5_crypt.hash(word, salt=new_salt)


def _add_to_16(s: str) -> bytes:
    while len(s) % 16 != 0:
        s += "\0"
    return str.encode(s)


def create_privileged_cmd(token: Token, command: BTMinerCommand) -> str:
    command.token = token.sign
    aeskey = hashlib.sha256(token.key.encode()).hexdigest()
    aeskey = binascii.unhexlify(aeskey.encode())
    aes = AES.new(aeskey, AES.MODE_ECB)
    enc_data = str(
        base64.encodebytes(aes.encrypt(_add_to_16(command.model_dump_json()))),
        encoding="utf-8",
    ).replace("\n", "")
    return BTMinerEncryptedCommand(data=enc_data).model_dump_json()


def parse_priviledge_data(token: Token, data: APIObject) -> APIObject:
    if "enc" in data:
        enc_data = data["enc"]
        aeskey = hashlib.sha256(token.key.encode()).hexdigest()
        aeskey = binascii.unhexlify(aeskey.encode())
        aes = AES.new(aeskey, AES.MODE_ECB)
        return from_json(
            aes.decrypt(base64.decodebytes(bytes(enc_data, encoding="utf-8")))
            .rstrip(b"\0")
            .decode("utf-8")
        )
    return data


@final
class WhatsminerRPCClient(CGMinerRPCLayer):
    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)

        self.username: str = "admin"
        if alt_pwd:
            set_alt_auth("whatsminer", alt_pwd)
        self.passwds: list[str] = get_auth_list("whatsminer")

        self.token: Token | None = None

    @override
    async def send_privileged_command(
        self, command: str, **kwargs: str | int
    ) -> APIObject:
        cmd: BTMinerCommand = BTMinerCommand(cmd=command, token=None, **kwargs)
        for pwd in self.passwds:
            if not pwd:
                continue
            self.pwd = pwd
            token_data = await self.get_token()
            priv_cmd = create_privileged_cmd(token_data, cmd)
            data = await self._do_rpc(priv_cmd)
            if not data:
                return {}
            try:
                data = parse_priviledge_data(token_data, data)
            except ValueError as e:
                logger.error(
                    f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}"
                )
                raise APIInvalidResponse
            else:
                cmd_resp = self._unmarshal_status(data)
                cmd_err = cmd_resp.error()
                if cmd_err is not None:
                    if cmd_resp.code == 23:
                        self.token = None
                        continue
                    elif cmd_resp.code != 131:
                        logger.error(f"{self.__repr__()} : {APIError(cmd_err)!s}")
                        raise APIError("Command failed!")
            return data
        if not self.token:
            raise AuthenticationError("Failed to authenticate")
        raise APIError("Unknown error occurred")

    async def get_token(self) -> Token:
        """
        Encryption algorithm:
        Ciphertext = aes256(plaintext), ECB mode
        Encode text = base64(ciphertext)

        (1)api_cmd = token,$sign|api_str    # api_str is API command plaintext
        (2)enc_str = aes256(api_cmd, $key)  # ECB mode
        (3)tran_str = base64(enc_str)

        Final assembly: enc|base64(aes256("token,sign|set_led|auto", $aeskey))
        """
        if (
            self.token
            and self.token.timestamp
            > datetime.datetime.now() - datetime.timedelta(minutes=30)
        ):
            return self.token

        data = await self.send_command("get_token")
        token_data = self._unmarshal_msg(data, TypeAdapter(TokenResponse))

        pwd = _crypt(self.pwd, "$1$" + token_data.salt + "$")
        pwd = pwd.split("$")
        key = pwd[3]

        tmp = _crypt(key + token_data.time, "$1$" + token_data.newsalt + "$")
        tmp = tmp.split("$")
        sign = tmp[3]

        self.token = Token(sign=sign, key=key, timestamp=datetime.datetime.now())
        return self.token

    @override
    def _unmarshal_status(self, data: APIObject) -> Status:
        try:
            return Status.model_validate(data, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self!r} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse from e

    def _unmarshal_msg(self, data: APIObject, adapter: TypeAdapter[T]) -> T:
        resobj = self._unmarshal_status(data)
        err = resobj.error()
        if err is not None:
            logger.error(f"{self.__repr__()} : {APIError(err)!s}")
            raise APIError("Command failed!")
        if not isinstance(resobj.msg, dict):
            logger.error(
                f"{self.__repr__()} : {APIInvalidResponse(reason='expected API object')!s}"
            )
            raise APIInvalidResponse()
        try:
            return adapter.validate_python(resobj.msg)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse()

    @override
    async def get_api_version(self) -> int:
        version = await self.version()
        return self._parse_api_version(version.api_ver)

    async def version(self) -> BTMinerVersion:
        resp = await self.send_command("get_version")
        return self._unmarshal_msg(resp, TypeAdapter(BTMinerVersion))

    async def devs(self) -> list[BTMinerDevice]:
        return await self._get_many("edevs", "DEVS", TypeAdapter(list[BTMinerDevice]))

    async def devdetails(self) -> list[BTMinerDevDetails]:
        return await self._get_many(
            "devdetails", "DEVDETAILS", TypeAdapter(list[BTMinerDevDetails])
        )

    async def summary(self) -> BTMinerSummary:
        if await self.get_api_version() <= 205:
            return await self._get_one(
                "summary", "SUMMARY", TypeAdapter(BTMinerSummary)
            )
        resp = await self.send_command("summary")
        return self._unmarshal_msg(resp, TypeAdapter(BTMinerSummary))

    async def pools(self) -> list[BTMinerPool]:
        return await self._get_many("pools", "POOLS", TypeAdapter(list[BTMinerPool]))

    async def get_pool_conf(self) -> PoolConfig:
        pools = await self.pools()
        pool_conf: list[MinerPoolConfig] = []
        for pool in pools:
            pool_conf.append(MinerPoolConfig(url=pool.url, user=pool.user))
        return PoolConfig(pool_conf)

    async def get_system_info(self) -> BTMinerSystemInfo:
        resp = await self.send_command("get_miner_info")
        return self._unmarshal_msg(resp, TypeAdapter(BTMinerSystemInfo))

    async def get_blink_status(self) -> BlinkStatus:
        resp = await self.get_system_info()
        blink = BlinkStatus(blink=bool(resp.ledstat) and resp.ledstat != "auto")
        return blink

    @override
    async def blink(
        self,
        enabled: bool,
        auto: bool = True,
        color: str = "red",
        period: int = 1000,
        duration: int = 500,
        start: int = 0,
    ) -> APIObject:
        if enabled:
            auto = False
        if auto:
            return await self.send_privileged_command("set_led", param="auto")
        else:
            return await self.send_privileged_command(
                "set_led", color=color, period=period, duration=duration, start=start
            )

    @override
    async def restart(self) -> APIObject:
        return await self.send_privileged_command("restart_btminer")

    @override
    async def reboot(self) -> APIObject:
        return await self.send_privileged_command("reboot")

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        # check if password length is greater than 8 bytes.
        if len(new_passwd.encode("utf-8")) > 8:
            raise APIError("Password must be 8 characters or less")

        return await self.send_privileged_command(
            "update_pwd", old=old_passwd, new=new_passwd
        )

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        params: dict[str, str] = {
            "pool1": urls[0],
            "worker1": users[0],
            "passwd1": passwds[0],
            "pool2": urls[1],
            "worker2": users[1],
            "passwd2": passwds[1],
            "pool3": urls[2],
            "worker3": users[2],
            "passwd3": passwds[2],
        }

        return await self.send_privileged_command("update_pools", **params)


def _btv3_encrypt_param(
    token_str: str, param: str | int | APIObject | list[APIObject]
) -> str:
    param_str = json.dumps(param)
    padding = 16 - len(param_str) % 16
    aligned = param_str + (chr(padding) * padding)
    cipher = AES.new(hashlib.sha256(token_str.encode("utf-8")).digest(), AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(aligned.encode("utf-8"))).decode("utf-8")


@final
class WhatsminerTCPClient(BaseTCPClient):
    def __init__(
        self,
        ip: str,
        port: int = 4433,
        username: str | None = None,
        alt_pwd: str | None = None,
    ) -> None:
        super().__init__(ip, port)
        if not username:
            self.username: str = "super"
        if alt_pwd:
            set_alt_auth("whatsminer_v3", alt_pwd)
        self.passwds: list[str] = get_auth_list("whatsminer_v3")
        # force set default password
        self.pwd: str = "super"
        self.salt: str | None = None

    # def _unmarshal_msg(self, resp: APIObject)

    async def send_command(
        self, command: str, param: str | int | APIObject | list[APIObject] | None = None
    ) -> APIObject:
        cmd: BTMinerV3Command

        if command.startswith("set."):
            salt = await self.get_salt()
            ts = int(datetime.datetime.now().timestamp())
            token_str = command + self.pwd + salt + str(ts)
            token_hashed = bytearray(
                base64.b64encode(hashlib.sha256(token_str.encode("utf-8")).digest())
            )
            b_arr = bytearray(token_hashed)
            b_arr[8] = 0
            str_token = b_arr.split(b"\x00")[0].decode("utf-8")

            cmd = BTMinerV3Command(
                cmd=command, param=param, ts=ts, account=self.username, token=str_token
            )
            # encrypt param for certain commands (set.miner.pools, set.user.change_passwd)
            if command == "set.miner.pools" and param is not None:
                try:
                    match command:
                        case "set.miner.pools":
                            _ = BTMinerV3PoolConfig.model_validate(param)
                        # case "set.user.change_passwd":
                        #     BTMinerV3PasswdChange.model_validate(param)
                except ValidationError:
                    raise APIError("Invalid param")
                else:
                    cmd.param = _btv3_encrypt_param(token_str, param)
        else:
            cmd = BTMinerV3Command(cmd=command, param=param)
        cmd_dict = cmd.model_dump()
        ser = json.dumps(cmd_dict)

        resp = await self.btv3_send(ser, len(ser))
        try:
            resobj = BTMinerV3CommandResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse()
        else:
            err = resobj.error()
            if err is not None:
                logger.error(f"{self.__repr__()} : {APIError(err)!s}")
                raise APIError("Command failed!")
            if isinstance(resobj.msg, dict):
                return resobj.msg
            return ActionResult(success=True, msg=resobj.msg).model_dump()

    async def get_salt(self) -> str:
        if self.salt:
            return self.salt
        resp = await self.get_device_info("salt")
        if resp.salt is None:
            logger.error(f"{self.__repr__()} : {APIError('Failed to get salt.')!s}")
            raise APIError("Failed to get salt.")
        self.salt = resp.salt
        return self.salt

    async def get_hostname(self) -> str:
        resp = await self.get_network_info()
        return resp.hostname

    async def get_mac_addr(self) -> str:
        resp = await self.get_network_info()
        return resp.mac

    async def get_api_version(self) -> int:
        resp = await self.get_system_info()
        return self._parse_api_version(resp.api)

    async def get_device_info(
        self,
        param: Literal["system", "network", "miner", "power", "salt", "error-code"]
        | None = None,
    ) -> BTMinerV3DeviceInfo:
        resp = await self.send_command("get.device.info", param)
        try:
            resobj = BTMinerV3DeviceInfo.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse()
        else:
            return resobj

    async def get_system_info(self) -> BTMinerV3SystemInfo:
        resp = await self.get_device_info("system")
        if resp.system is None:
            raise APIInvalidResponse()
        return resp.system

    async def get_network_info(self) -> BTMinerV3NetworkInfo:
        resp = await self.get_device_info("network")
        if resp.network is None:
            raise APIInvalidResponse()
        return resp.network

    async def summary(self) -> BTMinerV3Summary:
        resp = await self.send_command("get.miner.status", "summary")
        try:
            resobj = BTMinerV3Summary.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse()
        else:
            return resobj

    async def pools(self) -> list[BTMinerV3Pool]:
        resp = await self.send_command("get.miner.status", "pools")
        try:
            resobj = BTMinerV3Status.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse()
        else:
            if resobj.pools is None:
                return []
            return resobj.pools

    async def get_pool_conf(self) -> PoolConfig:
        pools = await self.pools()
        pool_conf: list[MinerPoolConfig] = []
        for pool in pools:
            pool_conf.append(MinerPoolConfig(url=pool.url, user=pool.account))
        return PoolConfig(pool_conf)

    async def get_blink_status(self) -> BlinkStatus:
        resp = await self.get_system_info()
        blink = BlinkStatus(blink=resp.ledstatus == "auto")
        return blink

    @override
    async def blink(
        self,
        enabled: bool,
        auto: bool = True,
        period: int = 1000,
        duration: int = 500,
        start: int = 0,
    ) -> APIObject:
        if enabled:
            auto = False
        if auto:
            return await self.send_command("set.system.led", "auto")
        else:
            param_data: list[APIObject] = [
                {
                    "color": "red",
                    "period": period,
                    "duration": duration,
                    "start": start,
                },
                {
                    "color": "green",
                    "period": period,
                    "duration": duration,
                    "start": start,
                },
            ]
            return await self.send_command("set.system.led", param_data)

    async def set_miner_mode(
        self, mode: Literal["start", "stop", "restart"]
    ) -> APIObject:
        return await self.send_command("set.miner.service", mode)

    @override
    async def start(self) -> APIObject:
        return await self.set_miner_mode("start")

    @override
    async def stop(self) -> APIObject:
        return await self.set_miner_mode("stop")

    @override
    async def restart(self) -> APIObject:
        return await self.set_miner_mode("restart")

    @override
    async def reboot(self) -> APIObject:
        return await self.send_command("set.system.reboot")

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        param_data: list[APIObject] = [
            {
                "pool": urls[0],
                "worker": users[0],
                "passwd": passwds[0],
            },
            {
                "pool": urls[1],
                "worker": users[1],
                "passwd": passwds[1],
            },
            {
                "pool": urls[2],
                "worker": users[2],
                "passwd": passwds[2],
            },
        ]
        return await self.send_command("set.miner.pools", param=param_data)
