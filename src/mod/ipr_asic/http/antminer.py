# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from string import Template

import httpx
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
)

from mod.ipr_asic import settings
from mod.ipr_asic.data import MinerConfPool
from mod.ipr_asic.errors import (
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
    firmware_type: str = ""
    serinum: str = ""
    algorithm: str | None = Field(None, alias="Algorithm")
    cgminer_version: str | None = None


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
    fan_ctrl: bool | None = Field(None, alias="bitmain-fan-ctrl")
    fan_pwm: int | None = Field(None, alias="bitmain-fan-pwm")
    freq_level: int | None = Field(
        None, validation_alias="bitmain-freq-level", serialization_alias="freq-level"
    )
    freq: int | None = Field(
        None, validation_alias="bitmain-freq", serialization_alias="freq"
    )
    voltage: float | None = Field(None, alias="bitmain-voltage")
    hashrate_per: int | None = Field(None, alias="bitmain-hashrate-percent")
    user_ip_cat: bool | None = Field(None, alias="bitmain-user-ip-cat")
    miner_mode: int | None = Field(
        None, validation_alias="bitmain-work-mode", serialization_alias="miner-mode"
    )
    pools: list[MinerConfPool]


class APIInfoResponse(BaseModel):
    miner_version: str
    compile_time: str = Field(alias="CompileTime")
    type: str


class APIStatusResponse(BaseModel):
    status: str = Field(alias="STATUS")
    when: int
    msg: str = Field(alias="Msg")
    api_version: str


class MinerStatus(BaseModel):
    type: str
    status: str
    code: int
    msg: str


class MinerSummary(BaseModel):
    elapsed: int = Field(validation_alias="elapsed", serialization_alias="Elapsed")
    rate_5s: float
    rate_30m: float
    rate_avg: float
    rate_ideal: float
    rate_unit: str
    hw_all: int
    bestshare: int
    status: list[MinerStatus]


class PoolInfo(BaseModel):
    index: int
    url: str = Field(validation_alias="url", serialization_alias="URL")
    user: str = Field(validation_alias="user", serialization_alias="User")
    status: str = Field(validation_alias="status", serialization_alias="Status")
    priority: int
    getworks: int
    accepted: int
    rejected: int
    discarded: int
    stale: int
    diff: str
    diffa: int
    diffr: int
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
    pools: list[PoolInfo] = Field(alias="POOLS")


class AntminerHTTPClient(BaseHTTPClient):
    def __init__(self, ip: str, port: int = 80, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port)

        self.command_path = Template("cgi-bin/${command}.cgi")

        self.username: str = "root"
        if alt_pwd:
            settings.set_alt_auth("antminer", alt_pwd)
        self.passwds = settings.get_auth_list("antminer")

    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            try:
                async with httpx.AsyncClient(
                    auth=httpx.DigestAuth(self.username, pwd),
                    timeout=settings.get("api_function_timeout", 5),
                ) as client:
                    resp = await client.get(url=self.base_url)
                    resp.raise_for_status()
            except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as ex:
                if isinstance(ex, (httpx.ConnectError, httpx.TimeoutException)):
                    raise FailedConnectionError("Failed to connect or timeout occurred")
                elif isinstance(ex, httpx.HTTPError):
                    continue
            else:
                if resp.status_code == 200:
                    self.authed = True
                    self.digest = client.auth
                    self.pwd = pwd
                    break
        if not self.digest:
            raise AuthenticationError("Failed to authenticate")

    async def get_system_info(self) -> dict:
        resp = await self.send_command(method="GET", command="get_system_info")
        try:
            resobj = SystemInfo.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True, exclude_none=True)
