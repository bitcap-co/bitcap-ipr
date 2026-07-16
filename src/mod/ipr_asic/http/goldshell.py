# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import logging
from string import Template

import httpx
from Crypto.Cipher import AES
from pydantic import BaseModel, Field, RootModel, TypeAdapter, ValidationError

from mod.ipr_asic import settings
from mod.ipr_asic.data import ActionResponse, BlinkStatus, MinerConfPool
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient

logger = logging.getLogger(__name__)


class PowerPlan(BaseModel):
    info: str
    level: int


class Settings(BaseModel):
    ledcontrol: bool
    manual: bool
    manual_power_plan: str = Field(alias="manualPowerplan")
    name: str
    power_plans: list[PowerPlan] = Field(alias="powerplans")
    select: int
    temp_target: int | None = None
    temp_targets: list[float] | None = None
    tempcontrol: bool
    version: str


class Status(BaseModel):
    firmware: str
    hardware: str
    mcbversion: str
    model: str


class Pool(BaseModel):
    url: str = ""
    user: str = ""
    passwd: str = Field("", alias="pass")
    pool_priority: int = Field(alias="pool-priority")
    legal: bool
    active: bool
    dragid: int


class PoolSettings(RootModel[list[Pool]]):
    pass


class Algo(BaseModel):
    name: str
    id: int


class AlgoSettings(BaseModel):
    algos: list[Algo]
    version: str
    algo_select: int


class Chain(BaseModel):
    id: int
    valid: int
    time: int
    powerplan: int
    av_hashrate: float
    accepted: int
    rejected: int
    hwerrors: int
    hwerr_ration: float
    hashrate: float
    nonces: int
    temp: str
    fanspeed: str
    minerstatus: int
    adjustpower: int


class Devs(BaseModel):
    status: int
    data: list[Chain]


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
        self.passwds = settings.get_auth_list("goldshell")

        self.command_path = Template("mcb/${command}")
        self.token = None

    async def authenticate(self) -> None:
        try:
            resp = await self._do_http("GET", path="user/logout")
            resp.raise_for_status()
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

    async def get_hostname(self) -> str:
        return await super().get_hostname()

    async def get_mac_addr(self) -> str:
        resp = await self.get_miner_conf()
        return resp["name"]

    async def get_api_version(self) -> str:
        return await super().get_api_version()

    async def get_system_info(self) -> dict:
        resp = await self.send_command("GET", command="status")
        try:
            resobj = Status.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def get_network_info(self) -> dict:
        return await super().get_network_info()

    async def log(self, *args, **kwargs) -> dict:
        return await super().log(*args, **kwargs)

    async def summary(self) -> dict:
        resp = await self.send_command(
            "GET", command="cgminer", params={"cgminercmd": "devs"}
        )
        try:
            resobj = Devs.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def get_miner_conf(self) -> dict:
        resp = await self.send_command("GET", command="setting")
        try:
            resobj = Settings.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True, exclude_none=True)

    async def set_miner_conf(self, conf: dict) -> dict:
        return await self.send_command("PUT", command="setting", payload=conf)

    async def get_algo(self) -> dict:
        resp = await self.send_command("GET", command="algosetting")
        try:
            resobj = AlgoSettings.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def pools(self) -> list[dict]:
        resp = await self.send_command("GET", command="pools")
        try:
            resobj = PoolSettings.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True)

    async def get_pool_conf(self) -> list[dict]:
        pools = await self.pools()
        ta = TypeAdapter(list[MinerConfPool])
        pool_conf = ta.validate_python(pools, by_name=True)
        return ta.dump_python(pool_conf, by_alias=True)

    async def get_miner_status(self) -> dict:
        return await super().get_miner_status()

    async def get_blink_status(self) -> dict:
        resp = await self.get_miner_conf()
        blink = BlinkStatus(blink=resp["ledcontrol"])
        return blink.model_dump()

    async def blink(self, enabled: bool, *args, **kwargs) -> dict:
        resp = await self.get_miner_conf()
        conf = Settings.model_construct(**resp)
        conf.ledcontrol = enabled
        payload = conf.model_dump(by_alias=True)
        return await self.set_miner_conf(conf=payload)

    async def set_miner_mode(self, *args, **kwargs) -> dict:
        return await super().set_miner_mode(*args, **kwargs)

    async def start(self) -> dict:
        return await super().start()

    async def stop(self) -> dict:
        return await super().stop()

    async def restart(self) -> dict:
        return await self.send_command("PUT", command="restart")

    async def reboot(self) -> dict:
        return await super().reboot()

    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        for i in range(0, len(urls)):
            if not len(urls[i]) and not len(users[i]):
                continue
            pool = {
                "url": urls[i],
                "user": users[i],
                "pass": passwds[i],
            }
            resp = await self.send_command("PUT", command="newpool", payload=pool)
            try:
                PoolSettings.model_validate(obj=resp, by_alias=True)
            except ValidationError as e:
                logger.error(
                    f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
                )
                raise APIInvalidResponse
        resobj = ActionResponse(success=True, msg="OK")
        return resobj.model_dump(mode="json")
