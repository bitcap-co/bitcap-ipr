import base64
import binascii
import datetime
import hashlib
import json
import logging
import re
from typing import Any

from Crypto.Cipher import AES
from passlib.hash import md5_crypt
from pydantic import BaseModel, Field, RootModel, TypeAdapter, ValidationError

from apiv2 import settings
from apiv2.base.rpc import BaseRPCClient
from apiv2.base.tcp import BaseTCPClient
from apiv2.errors import APIError, APIInvalidResponse, AuthenticationError
from apiv2.rpc.cgminer import Pool, Status

logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    sign: str
    key: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)


class TokenResponse(BaseModel):
    salt: str
    time: str
    newsalt: str

    class Config:
        extra = "allow"


class BTMinerResponse(BaseModel):
    status: list[Status] = Field(alias="STATUS")

    summary: list[dict[str, Any]] | None = Field(None, alias="SUMMARY")
    stats: list[dict[str, Any]] | None = Field(None, alias="STATS")
    devs: list[dict[str, Any]] | None = Field(None, alias="DEVS")
    dev_details: list[dict[str, Any]] | None = Field(None, alias="DEVDETAILS")
    pools: list[Pool] | None = Field(None, alias="POOLS")

    def error(self) -> str | None:
        for status in self.status:
            match status.status:
                case "E" | "F":
                    return f"received API error ({status.code}) {status.msg} - {status.description}"
                case _:
                    return None


class SystemInfo(BaseModel):
    ntp: list[str] = Field(default_factory=list)
    ip: str | None = None
    proto: str | None = None
    netmask: str | None = None
    gateway: str | None = None
    dns: str | None = None
    hostname: str | None = None
    mac: str | None = None
    ledstat: str | None = None
    minersn: str = ""
    powersn: str = ""
    upfreq_speed: str | None = None


class VersionInfo(BaseModel):
    api_ver: str
    fw_ver: str
    platform: str
    chip: str
    miner_type: str | None = None


class BlinkStatus(BaseModel):
    blink: bool


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


def create_privileged_cmd(token_data: TokenData, command: dict) -> str:
    command["token"] = token_data.sign
    aeskey = hashlib.sha256(token_data.key.encode()).hexdigest()
    aeskey = binascii.unhexlify(aeskey.encode())
    aes = AES.new(aeskey, AES.MODE_ECB)
    cmd_str = json.dumps(command)
    enc_cmd_str = str(
        base64.encodebytes(aes.encrypt(_add_to_16(cmd_str))),
        encoding="utf-8",
    ).replace("\n", "")
    data_enc = {"enc": 1, "data": enc_cmd_str}
    cmd = json.dumps(data_enc)
    return cmd


def parse_priviledge_data(token_data: TokenData, data: dict) -> dict:
    enc_data = data["enc"]
    aeskey = hashlib.sha256(token_data.key.encode()).hexdigest()
    aeskey = binascii.unhexlify(aeskey.encode())
    aes = AES.new(aeskey, AES.MODE_ECB)
    ret_msg = json.loads(
        aes.decrypt(base64.decodebytes(bytes(enc_data, encoding="utf-8")))
        .rstrip(b"\0")
        .decode("utf-8")
    )
    return ret_msg


class WhatsminerRPCClient(BaseRPCClient):
    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)

        self.username: str = "admin"
        if alt_pwd:
            settings.set_auth_alt("whatsminer", alt_pwd)
        self.passwds = settings.get_auth_list("whatsminer")

        self.token: TokenData | None = None

    def send_privileged_command(self, command: str, **kwargs) -> dict:
        cmd = {"cmd": command, **kwargs}
        for pwd in self.passwds:
            if not pwd:
                continue
            self.pwd = pwd
            token_data = self.get_token()
            priv_cmd = create_privileged_cmd(token_data, cmd)
            data = self._do_rpc(priv_cmd)
            if not data:
                return {}
            try:
                data = parse_priviledge_data(token_data, data)
            except json.JSONDecodeError as e:
                logger.error(
                    f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
                )
                raise APIInvalidResponse
            else:
                try:
                    resobj = Status.model_validate(obj=data, by_alias=True)
                except ValidationError as e:
                    logger.error(
                        f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
                    )
                    raise APIInvalidResponse
                else:
                    err = resobj.error()
                    if err:
                        if resobj.code == 23:
                            self.token = None
                            continue
                        elif resobj.code != 131:
                            logger.error(f"{self.__repr__()} : {str(APIError(err))}")
                            raise APIError("Command failed!")
            return resobj.model_dump(by_alias=True, exclude_none=True)
        if not self.token:
            raise AuthenticationError("Failed to authenticate")
        raise APIError("Unknown error occurred")

    def get_token(self) -> TokenData:
        """
        Encryption algorithm:
        Ciphertext = aes256(plaintext), ECB mode
        Encode text = base64(ciphertext)

        (1)api_cmd = token,$sign|api_str    # api_str is API command plaintext
        (2)enc_str = aes256(api_cmd, $key)  # ECB mode
        (3)tran_str = base64(enc_str)

        Final assembly: enc|base64(aes256("token,sign|set_led|auto", $aeskey))
        """
        if self.token:
            if self.token.timestamp > datetime.datetime.now() - datetime.timedelta(
                minutes=30
            ):
                return self.token

        data = self.send_command("get_token")
        try:
            resobj = TokenResponse.model_validate(data["Msg"])
        except ValidationError:
            raise APIInvalidResponse(reason=f'got "{data["Msg"]}" for token data')

        pwd = _crypt(self.pwd, "$1$" + resobj.salt + "$")
        pwd = pwd.split("$")
        key = pwd[3]

        tmp = _crypt(key + resobj.time, "$1$" + resobj.newsalt + "$")
        tmp = tmp.split("$")
        sign = tmp[3]

        self.token = TokenData(sign=sign, key=key, timestamp=datetime.datetime.now())
        return self.token

    def _validate_response(self, data: dict) -> BTMinerResponse:
        try:
            resobj = BTMinerResponse.model_validate(obj=data, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {str(APIError(err))}")
                raise APIError("Command failed!")
            return resobj

    def _validate_msg(self, data: dict) -> Status:
        try:
            resobj = Status.model_validate(obj=data, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {str(APIError(err))}")
                raise APIError("Command failed!")
            return resobj

    def version(self) -> dict:
        resp = self.send_command("get_version")
        resobj = self._validate_msg(resp)
        try:
            version = VersionInfo.model_validate(obj=resobj.msg)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return version.model_dump()

    def devs(self) -> list[dict]:
        resp = self.send_command("edevs")
        valid = self._validate_response(resp)
        if valid.devs is None:
            raise APIInvalidResponse(reason="malformed")
        return valid.devs

    def devdetails(self) -> list[dict]:
        resp = self.send_command("devdetails")
        valid = self._validate_response(resp)
        if valid.dev_details is None:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.dev_details

    def summary(self) -> dict:
        resp = self.send_command("summary")
        _ = self._validate_msg(resp)
        return resp["Msg"]

    def stats(self) -> list[dict]:
        return super().stats()

    def pools(self) -> list[dict]:
        resp = self.send_command("pools")
        valid = self._validate_response(resp)
        if valid.pools is None:
            raise APIInvalidResponse(reason="malformed")
        else:
            ta = TypeAdapter(list[Pool])
            pools = ta.validate_python(valid.pools, by_alias=True)
            return ta.dump_python(pools, by_alias=True)

    def get_system_info(self) -> dict:
        resp = self.send_command("get_miner_info")
        _ = self._validate_msg(resp)
        return resp["Msg"]

    def get_blink_status(self) -> dict:
        resp = self.get_system_info()
        try:
            resobj = SystemInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            blink = BlinkStatus(
                blink=True if resobj.ledstat and resobj.ledstat != "auto" else False
            )
            return blink.model_dump()

    def blink(
        self,
        enabled: bool,
        auto: bool = True,
        color: str = "red",
        period: int = 1000,
        duration: int = 500,
        start: int = 0,
    ) -> dict:
        if enabled:
            auto = False
        if auto:
            return self.send_privileged_command("set_led", param="auto")
        else:
            return self.send_privileged_command(
                "set_led", color=color, period=period, duration=duration, start=start
            )

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
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

        return self.send_privileged_command("update_pools", **params)


class BTMinerV3Command(BaseModel):
    cmd: str
    param: Any | None = None

    class Config:
        extra = "forbid"


class BTMinerV3PriviledgedCommand(BaseModel):
    cmd: str
    param: Any | None = None
    ts: int
    account: str
    token: str

    class Config:
        extra = "forbid"


class BTMinerV3Response(BaseModel):
    code: int
    when: int
    msg: str | dict
    desc: str

    def error(self) -> str | None:
        if self.code != 0:
            return f"received API error ({self.code}) {self.msg} - {self.desc}"


class BTMinerV3SystemInfo(BaseModel):
    api: str
    platform: str
    fwversion: str
    control_board_version: str = Field(alias="control-board-version")
    btrom: str | None = None
    apiswitch: str
    ledstatus: str


class BTMinerV3NetworkInfo(BaseModel):
    ip: str
    proto: str
    netmask: str
    dns: str
    mac: str
    gateway: str
    hostname: str


class BTMinerV3MinerInfo(BaseModel):
    working: str
    type: str
    hash_board: str = Field(alias="hash-board")
    detect_hash_rate: str = Field(alias="detect-hash-rate")
    cointype: str
    pool_strategy: str = Field(alias="pool-strategy")
    heatmode: str
    hash_percent: str = Field(alias="hash-percent")
    eeprom_liquid_cooling: str | None = Field(None, alias="eeprom-liquid-cooling")
    chipdata0: str
    chipdata1: str
    chipdata2: str
    fast_boot: str = Field(alias="fast-boot")
    board_num: int = Field(alias="board-num")
    pcbsn0: str
    pcbsn1: str
    pcbsn2: str
    miner_sn: str = Field(alias="miner-sn")
    power_limit_set: str = Field(alias="power-limit-set")
    web_pool: int = Field(alias="web-pool")


class BTMinerV3PowerInfo(BaseModel):
    type: str
    mode: int
    hwversion: str
    swversion: str
    model: str
    iin: float
    vin: float
    vout: int
    pin: int
    fanspeed: int
    temp0: float
    sn: str
    vendor: str


class BTMinerV3DeviceInfoResponse(BaseModel):
    network: BTMinerV3NetworkInfo | None = None
    miner: BTMinerV3MinerInfo | None = None
    system: BTMinerV3SystemInfo | None = None
    power: BTMinerV3PowerInfo | None = None
    salt: str | None = None


class BTMinerV3Pool(BaseModel):
    id: int
    url: str
    status: str
    account: str
    stratum_active: bool = Field(alias="stratum-active")
    reject_rate: int = Field(alias="reject-rate")
    last_share_time: float = Field(alias="last-share-time")


class MinerConfPool(BaseModel):
    pool: str
    worker: str
    passwd: str


class BTMinerV3PoolConf(RootModel[list[MinerConfPool]]):
    pass


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
            settings.set_auth_alt("whatsminer_v3", alt_pwd)
        self.passwds = settings.get_auth_list("whatsminer_v3")
        # force set default password
        self.pwd: str = "super"
        self.salt: str | None = None

    def _encrypt_param(self, param: str, command: str, ts: int) -> str:
        token_str = command + self.pwd + self.salt + str(ts)
        aes_key = hashlib.sha256(token_str.encode("utf-8")).digest()
        pad_len = 16 - (len(param) % 16)
        padded = param + (chr(pad_len) * pad_len)
        cipher = AES.new(aes_key, AES.MODE_ECB)
        return base64.b64encode(cipher.encrypt(padded.encode())).decode()

    def send_command(self, command: str, param: Any | None = None) -> dict:
        cmd: BTMinerV3Command | BTMinerV3PriviledgedCommand

        if command.startswith("set."):
            salt = self.get_salt()
            ts = int(datetime.datetime.now().timestamp())
            token_str = command + self.pwd + salt + str(ts)
            token_hashed = bytearray(
                base64.b64encode(hashlib.sha256(token_str.encode("utf-8")).digest())
            )
            b_arr = bytearray(token_hashed)
            b_arr[8] = 0
            str_token = b_arr.split(b"\x00")[0].decode("utf-8")

            cmd = BTMinerV3PriviledgedCommand(
                cmd=command, param=param, ts=ts, account=self.username, token=str_token
            )
            if command == "set.miner.pools" and param:
                try:
                    BTMinerV3PoolConf.model_validate(param)
                except ValidationError:
                    raise APIError("Invalid param")
                else:
                    param_str = json.dumps(param)
                    pad_len = 16 - (len(param) % 16)
                    padded = param_str + (chr(pad_len) * pad_len)
                    aes_key = hashlib.sha256(token_str.encode("utf-8")).digest()
                    cipher = AES.new(aes_key, AES.MODE_ECB)
                    param_hashed = base64.b64encode(
                        cipher.encrypt(padded.encode())
                    ).decode()
                    cmd.param = param_hashed
        else:
            cmd = BTMinerV3Command(cmd=command, param=param)
        cmd_dict = cmd.model_dump()
        ser = json.dumps(cmd_dict)

        resp = self.btv3_send(ser, len(ser))
        try:
            resobj = BTMinerV3Response.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {str(APIError(err))}")
                raise APIError("Command failed!")
            return resp["msg"]

    def get_salt(self) -> str:
        if self.salt is not None:
            return self.salt
        data = self.send_command("get.device.info", "salt")
        self.salt = data["salt"]
        return self.salt

    def get_hostname(self) -> str:
        resp = self.get_network_info()
        return resp["hostname"]

    def get_mac_addr(self) -> str:
        resp = self.get_network_info()
        return resp["mac"]

    def get_api_version(self) -> str:
        resp = self.get_system_info()
        return resp["system"]["api"]

    def get_system_info(self) -> dict:
        resp = self.send_command("get.device.info")
        try:
            resobj = BTMinerV3DeviceInfoResponse.model_validate(obj=resp, by_alias=True)
        except ValidationError:
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True, exclude_none=True)

    def get_network_info(self) -> dict:
        resp = self.send_command("get.device.info", "network")
        try:
            resobj = BTMinerV3NetworkInfo.model_validate(obj=resp)
        except ValidationError:
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def log(self, *args, **kwargs) -> dict:
        return super().log(*args, **kwargs)

    def summary(self) -> dict:
        return self.send_command("get.miner.status", "summary")

    def get_miner_conf(self) -> dict:
        return super().get_miner_conf()

    def set_miner_conf(self, *args, **kwargs) -> dict:
        return super().set_miner_conf(*args, **kwargs)

    def pools(self) -> list[dict]:
        resp = self.send_command("get.miner.status", "pools")
        ta = TypeAdapter(list[BTMinerV3Pool])
        pools = ta.validate_python(resp["pools"], by_alias=True)
        return ta.dump_python(pools, by_alias=True)

    def get_pool_conf(self) -> list[dict]:
        return super().get_pool_conf()

    def get_miner_status(self) -> dict:
        return self.send_command("get.miner.status", "pools+summary+edevs")

    def get_blink_status(self) -> dict:
        resp = self.get_system_info()
        blink = BlinkStatus(
            blink=True if resp["system"]["ledstatus"] == "auto" else False
        )
        return blink.model_dump()

    def blink(
        self,
        enabled: bool,
        auto: bool = True,
        period: int = 1000,
        duration: int = 500,
        start: int = 0,
    ) -> dict:
        if enabled:
            auto = False
        if auto:
            return self.send_command("set.system.led", "auto")
        else:
            param_data = [
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
            return self.send_command("set.system.led", param_data)

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        param_data = [
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
        return self.send_command("set.miner.pools", param=param_data)
