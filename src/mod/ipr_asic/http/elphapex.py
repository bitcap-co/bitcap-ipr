# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from string import Template

import httpx
from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator

from mod.ipr_asic import settings
from mod.ipr_asic.data import BlinkStatus, MinerConfPool
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient

logger = logging.getLogger(__name__)


class ActionResponse(BaseModel):
    stats: str
    status: str | None = None
    code: str
    msg: str

    def error(self) -> str | None:
        if self.status != "success" and self.stats != "success" or self.msg == "FAIL!":
            return f"received API Error ({self.code}): {self.stats} - {self.msg}"


class SystemInfo(BaseModel):
    minertype: str
    algorithm: str = Field(alias="Algorithm")
    nettype: str
    netdevice: str
    macaddr: str
    hostname: str
    ipaddress: str
    netmask: str
    gateway: str
    dnsservers: str
    system_mode: str
    system_kernel_version: str
    system_filesystem_version: str
    firmware_type: str


class NetInfo(BaseModel):
    nettype: str
    netdevice: str
    macaddr: str
    ipaddress: str
    netmask: str
    conf_nettype: str
    conf_hostname: str
    conf_ipaddress: str
    conf_netmask: str
    conf_gateway: str
    conf_dnsservers: str


class MinerConf(BaseModel):
    fan_ctrl: bool = Field(alias="fc-fan-ctrl")
    fan_pwm: str = Field(alias="fc-fan-pwm")
    freq: str = Field(alias="fc-freq")
    freq_level: str = Field(alias="fc-freq-level")
    voltage: str = Field(alias="fc-voltage")
    miner_mode: int = Field(alias="fc-work-mode")
    algo: str
    pools: list[MinerConfPool]


class APIInfoResponse(BaseModel):
    miner_version: str
    compile_time: str = Field(alias="CompileTime")
    dev_sn: str
    type: str
    hw_version: str


class APIStatusResponse(BaseModel):
    status: str = Field(alias="STATUS")
    when: int
    timestamp: int
    api_version: str
    msg: str = Field(alias="Msg")


class MinerStatus(BaseModel):
    status: str
    type: str
    msg: str
    code: int


class MinerSummary(BaseModel):
    elapsed: int
    rate_5s: float
    rate_30m: float
    rate_avg: float
    rate_ideal: float
    rate_unit: str
    bestshare: int
    hw_all: float
    status: list[MinerStatus]


class PoolInfo(BaseModel):
    index: int
    url: str
    user: str
    status: str
    priority: int
    getworks: int
    accepted: int
    rejected: int
    discarded: int | None = None
    stale: int
    diff: str
    diff1: int
    diffa: int
    diffr: int
    diffs: int
    lsdiff: int
    lstime: str


class Summary(BaseModel):
    status: APIStatusResponse = Field(alias="STATUS")
    info: APIInfoResponse = Field(alias="INFO")
    summary: list[MinerSummary] = Field(alias="SUMMARY")

    @field_validator("summary", mode="before")
    @classmethod
    def ensure_summary_length(cls, v: list) -> list:
        if len(v) != 1:
            raise ValueError
        return v


class Pools(BaseModel):
    status: APIStatusResponse = Field(alias="STATUS")
    info: APIInfoResponse = Field(alias="INFO")
    rejected_per: float = Field(alias="Device Rejected%")
    rejected_total: int = Field(alias="Device Total Rejected")
    total_work: int = Field(alias="Device Total Work")
    pools: list[PoolInfo] = Field(alias="POOLS")


class ElphapexHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, alt_pwd, transport)

        self.username: str = "root"
        if alt_pwd:
            settings.set_alt_auth("elphapex", alt_pwd)
        self.passwds = settings.get_auth_list("elphapex")

        self.command_path = Template("cgi-bin/${command}.cgi")

    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            digest = httpx.BasicAuth(self.username, pwd)
            try:
                async with self._new_client(auth=digest) as client:
                    resp = await client.get(self.base_url)
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
                    self.authed = True
                    self.digest = digest
                    self.pwd = pwd
                    break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    async def get_hostname(self) -> str:
        resp = await self.get_system_info()
        return resp["hostname"]

    async def get_mac_addr(self) -> str:
        resp = await self.get_system_info()
        return resp["macaddr"]

    async def get_api_version(self) -> str:
        return await super().get_api_version()

    async def get_system_info(self) -> dict:
        resp = await self.send_command("GET", command="get_system_info")
        try:
            resobj = SystemInfo.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def get_network_info(self) -> dict:
        resp = await self.send_command("GET", command="get_network_info")
        try:
            resobj = NetInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def log(self, num: int = -1) -> dict:
        """Get miner log

        Args:
        num: get history log number. -1 is current log
        """
        return await self.send_command(
            "GET", command="hlog", payload={"key": "log", "body": {"num": num}}
        )

    async def summary(self) -> dict:
        resp = await self.send_command("GET", command="summary")
        try:
            resobj = Summary.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True)

    async def get_miner_conf(self) -> dict:
        resp = await self.send_command("GET", command="get_miner_conf")
        try:
            resobj = MinerConf.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(exclude_none=True)

    async def set_miner_conf(self, conf: dict) -> dict:
        resp = await self.send_command("POST", command="set_miner_conf", payload=conf)
        try:
            resobj = ActionResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {err}")
                raise APIError("Command failed!")
            return resobj.model_dump(exclude_none=True)

    async def pools(self) -> list[dict]:
        resp = await self.send_command("GET", command="pools")
        try:
            resobj = Pools.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            ta = TypeAdapter(list[PoolInfo])
            pools = ta.validate_python(resobj.pools)
            return ta.dump_python(pools, by_alias=True)

    async def get_pool_conf(self) -> list[dict]:
        resp = await self.get_miner_conf()
        ta = TypeAdapter(list[MinerConfPool])
        pools = ta.validate_python(resp["pools"], by_name=True)
        return ta.dump_python(pools, by_alias=True)

    async def get_miner_status(self) -> dict:
        return await super().get_miner_status()

    async def get_blink_status(self) -> dict:
        resp = await self.send_command("GET", command="get_blink_status")
        try:
            resobj = BlinkStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def blink(self, enabled: bool) -> dict:
        blink = BlinkStatus(blink=enabled)
        payload = blink.model_dump(mode="json")
        return await self.send_command("POST", command="blink", payload=payload)

    async def set_miner_mode(self, *args, **kwargs) -> dict:
        return await super().set_miner_mode(*args, **kwargs)

    async def start(self) -> dict:
        return await super().start()

    async def stop(self) -> dict:
        return await super().stop()

    async def restart(self) -> dict:
        return await self.reboot()

    async def reboot(self) -> dict:
        return await self.send_command("POST", command="reboot")

    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        resp = await self.get_miner_conf()
        conf = MinerConf.model_construct(**resp)
        ta = TypeAdapter(list[MinerConfPool])
        pool_conf: list[dict[str, str]] = ta.dump_python(conf.pools, by_alias=True)

        for i in range(0, len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            pool_conf[i] = {
                "url": urls[i],
                "user": users[i],
                "pass": passwds[i],
            }

        conf.pools = ta.validate_python(pool_conf)

        new_conf = conf.model_dump(mode="json", by_alias=True, exclude_none=True)
        return await self.set_miner_conf(conf=new_conf)
