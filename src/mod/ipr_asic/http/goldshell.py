# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import logging
from typing import final, override

import httpx
from Crypto.Cipher import AES
from pydantic import ValidationError

from mod.ipr_asic import settings
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient
from mod.ipr_asic.schemas.goldshell import (
    AlgoSettings,
    Devs,
    MinerPool,
    PoolsResponse,
    Settings,
    Status,
)
from mod.ipr_asic.schemas.models import (
    ActionResult,
    APIObject,
    BlinkStatus,
    MinerPoolConfig,
    PoolConfig,
)

logger = logging.getLogger(__name__)


def zero_pad(data: bytes, block_size: int) -> bytes:
    padding_len = block_size - len(data) % block_size
    padding = bytes([0]) * padding_len
    return data + padding


def encrypt(plain: str) -> str:
    cipher = AES.new(
        key=b"!!!!!!!!!!!!!!!!",
        mode=AES.MODE_CBC,
        iv=bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    )
    padded = zero_pad(plain.encode(), 16)
    return cipher.encrypt(padded).hex()


@final
class GoldshellHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, transport=transport)

        self.username: str = "admin"
        if alt_pwd:
            settings.set_alt_auth("goldshell", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("goldshell")

        self.command_path: str = "mcb/{command}"
        self.token: str | None = None

    @override
    async def authenticate(self) -> None:
        try:
            resp = await self._do_http("GET", path="user/logout")
            _ = resp.raise_for_status()
        except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException):
            raise FailedConnectionError("Failed to connect or timeout occurred.")
        for pwd in self.passwds:
            if not pwd:
                continue
            params = {"username": self.username, "password": pwd, "cipher": "false"}
            resp = await self._do_http("GET", path="user/login", params=params)
            if resp.status_code == 500:
                # login failed, try again with encryption
                params["password"] = encrypt(pwd)
                params["cipher"] = "true"
                resp = await self._do_http("GET", path="user/login", params=params)
                if resp.status_code == 500:
                    continue
            try:
                resobj = resp.json()
            except json.JSONDecodeError:
                break
            if "JWT Token" in resobj and resobj["JWT Token"] != "":
                self.authed = True
                self.token = resobj["JWT Token"]
                break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate.")

    async def get_mac_addr(self) -> str:
        resp = await self.get_miner_conf()
        return resp.name

    async def get_system_info(self) -> Status:
        resp = await self.send_command("GET", command="status")
        try:
            resobj = Status.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def summary(self) -> Devs:
        resp = await self.send_command(
            "GET", command="cgminer", params={"cgminercmd": "devs"}
        )
        try:
            resobj = Devs.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_miner_conf(self) -> Settings:
        resp = await self.send_command("GET", command="setting")
        try:
            resobj = Settings.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def set_miner_conf(self, conf: APIObject) -> APIObject:
        return await self.send_command("PUT", command="setting", payload=conf)

    async def get_algo(self) -> AlgoSettings:
        resp = await self.send_command("GET", command="algosetting")
        try:
            resobj = AlgoSettings.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def pools(self) -> list[MinerPool]:
        resp = await self.send_command("GET", command="pools")
        try:
            resobj = PoolsResponse.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.root

    async def get_pool_conf(self) -> PoolConfig:
        pools = await self.pools()
        pool_conf: list[MinerPoolConfig] = []
        for pool in pools:
            pool_conf.append(
                MinerPoolConfig(url=pool.url, user=pool.user, pwd=pool.passwd)
            )
        return PoolConfig(pool_conf)

    async def get_blink_status(self) -> BlinkStatus:
        resp = await self.get_miner_conf()
        blink = BlinkStatus(blink=resp.ledcontrol)
        return blink

    @override
    async def blink(self, enabled: bool) -> APIObject:
        conf = await self.get_miner_conf()
        conf.ledcontrol = enabled
        payload = conf.model_dump(by_alias=True)
        return await self.set_miner_conf(conf=payload)

    @override
    async def restart(self) -> APIObject:
        return await self.send_command("PUT", command="restart")

    @override
    async def reboot(self) -> APIObject:
        return await self.restart()

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        for i in range(len(urls)):
            if not len(urls[i]) and not len(users[i]):
                continue
            pool = {
                "url": urls[i],
                "user": users[i],
                "pass": passwds[i],
            }
            resp = await self.send_command("PUT", command="newpool", payload=pool)
            try:
                _ = PoolsResponse.model_validate(obj=resp, by_alias=True)
            except ValidationError as e:
                logger.error(
                    f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}"
                )
                raise APIInvalidResponse
        resobj = ActionResult(success=True, msg="OK")
        return resobj.model_dump(mode="json")
