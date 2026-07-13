# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import logging
from string import Template
from typing import Any

import httpx
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from mod.ipr_asic import settings
from mod.ipr_asic.data import BlinkStatus
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient

logger = logging.getLogger(__name__)


class ActionResponse(BaseModel):
    error: int
    message: str
    data: dict[str, Any] = Field(default_factory=dict)

    def error_(self) -> str | None:
        if self.error != 0:
            return f"receieved API Error ({self.error}): {self.message}"


class NetInfo(BaseModel):
    nic: str
    mac: str
    ip: str
    netmask: str
    host: str
    dhcp: bool
    gateway: str
    dns: str


class Pool(BaseModel):
    no: int
    addr: str
    user: str
    passwd: str = Field(alias="pass")
    connect: int
    diff: str
    priority: int
    accepted: int
    rejected: int
    diffa: int
    diffr: int
    state: int
    lsdiff: int
    lstime: str


class Board(BaseModel):
    no: int
    chipnum: int
    chipsuc: int
    error: int
    freq: int
    rtpow: str
    avgpow: str
    idealpow: str
    pcbtemp: str
    intmp: int
    outtmp: int
    state: bool
    false: list[int]


class MinerConf(BaseModel):
    pools: list[Pool]
    ratio: int
    mode: int
    locate: int


class MinerStatus(BaseModel):
    netstate: bool
    powstate: bool
    tempstate: bool
    fanstate: bool


class UserPanel(BaseModel):
    nic: str
    mac: str
    ip: str
    netmask: str
    host: str
    dhcp: bool
    gateway: str
    dns: str
    model: str
    algo: str
    online: bool
    firmver1: str
    firmver2: str
    softver1: str
    softver2: str
    firmtype: str
    locate: bool
    rtpow: str
    avgpow: str
    reject: float
    runtime: str
    unit: str
    netstate: bool
    powstate: bool
    tempstate: bool
    fanstate: bool
    fans: list[int]
    pools: list[Pool]
    boards: list[Board]
    reftime: str = Field(alias="refTime")


class MinerConfPool(BaseModel):
    addr: str = ""
    user: str = ""
    passwd: str = Field(default="", alias="pass")


class IceriverHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, alt_pwd, transport)

        self.username: str = "admin"
        if alt_pwd:
            settings.set_alt_auth("iceriver", alt_pwd)
        self.passwds = settings.get_auth_list("iceriver")

        self.command_path = Template("user/${command}")

    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            try:
                async with self._new_client() as client:
                    resp = await client.post(
                        self.base_url + "user/loginpost",
                        data={"post": 6, "user": self.username, "pwd": pwd},
                    )
                    resp.raise_for_status()
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
            ):
                raise FailedConnectionError("Failed to connect or timeout occurred")
            except httpx.HTTPError:
                continue
            else:
                if resp.status_code == 200:
                    try:
                        resobj = resp.json()
                        action_resp = ActionResponse(**resobj)
                    except (json.JSONDecodeError, ValidationError):
                        break
                    else:
                        err = action_resp.error_()
                        if err:
                            continue
                        self.authed = True
                        self.pwd = pwd
                        break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    async def get_hostname(self) -> str:
        resp = await self.get_network_info()
        return resp["host"]

    async def get_mac_addr(self) -> str:
        resp = await self.get_network_info()
        return resp["mac"]

    async def get_api_version(self) -> str:
        return await super().get_api_version()

    async def get_system_info(self) -> dict:
        return await self.summary()

    async def get_network_info(self) -> dict:
        resp = await self.send_command("POST", command="ipconfig", data={"post": 1})
        try:
            resobj = NetInfo.model_validate(obj=resp["data"])
        except (ValidationError, KeyError) as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def log(self, *args, **kwargs) -> dict:
        return await super().log(*args, **kwargs)

    async def summary(self) -> dict:
        resp = await self.send_command("POST", command="userpanel", data={"post": 4})
        try:
            resobj = UserPanel.model_validate(obj=resp["data"], by_alias=True)
        except (ValidationError, KeyError) as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def get_miner_conf(self) -> dict:
        resp = await self.send_command(
            "POST", command="machineconfig", data={"post": 1}
        )
        try:
            resobj = MinerConf.model_validate(obj=resp["data"], by_alias=True)
        except (ValidationError, KeyError) as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True)

    async def set_miner_conf(self, conf: dict) -> dict:
        resp = await self.send_command("POST", command="machineconfig", data=conf)
        try:
            resobj = ActionResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            err = resobj.error_()
            if err:
                logger.error(f"{self.__repr__()} : {err}")
                raise APIError("Command failed!")
            return resobj.model_dump()

    async def pools(self) -> list[dict]:
        resp = await self.summary()
        ta = TypeAdapter(list[Pool])
        pools = ta.validate_python(resp["pools"], by_name=True)
        return ta.dump_python(pools, by_alias=True)

    async def get_pool_conf(self) -> list[dict]:
        resp = await self.get_miner_conf()
        ta = TypeAdapter(list[MinerConfPool])
        pools = ta.validate_python(resp["pools"], by_name=True)
        return ta.dump_python(pools, by_alias=True)

    async def get_miner_status(self) -> dict:
        return await super().get_miner_status()

    async def get_blink_status(self) -> dict:
        resp = await self.summary()
        user = UserPanel.model_construct(**resp)
        blink_status = BlinkStatus(blink=user.locate)
        return blink_status.model_dump()

    async def blink(self, enabled: bool, *args, **kwargs) -> dict:
        data = {"post": 5, "locate": 1 if enabled else 0}
        resp = await self.send_command("POST", command="userpanel", data=data)
        try:
            resobj = ActionResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            err = resobj.error_()
            if err:
                logger.error(f"{self.__repr__()} : {err}")
                raise APIError("Command failed!")
            return resobj.model_dump()

    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        resp = await self.get_miner_conf()
        conf = MinerConf.model_construct(**resp)
        pool_conf: list[dict[str, str]] = await self.get_pool_conf()

        data: dict[str, Any] = {"post": 2}
        data["fanratio"] = f"{conf.ratio}"
        match conf.mode:
            case 0:
                data["fanmode"] = "sleep"
            case 1:
                data["fanmode"] = "normal"

        for i in range(0, len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            idx = i + 1
            data[f"pool{idx}address"] = urls[i]
            data[f"pool{idx}miner"] = users[i]
            data[f"pool{idx}pwd"] = passwds[i]
        return await self.set_miner_conf(conf=data)
