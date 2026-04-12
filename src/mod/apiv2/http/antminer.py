# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from string import Template
from typing import Any

import requests
from pydantic import (
    BaseModel,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
)
from requests.auth import HTTPDigestAuth

from mod.apiv2 import settings
from mod.apiv2.base import BaseHTTPClient
from mod.apiv2.data import BlinkStatus, MinerConfPool
from mod.apiv2.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)

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
    firmware_type: str
    serinum: str = ""
    algorithm: str | None = Field(None, alias="Algorithm")


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
    fan_ctrl: bool = Field(alias="bitmain-fan-ctrl")
    fan_pwm: int = Field(alias="bitmain-fan-pwm")
    freq_level: int | None = Field(
        None, validation_alias="bitmain-freq-level", serialization_alias="freq-level"
    )
    voltage: float | None = Field(None, alias="bitmain-voltage")
    hashrate_per: int | None = Field(None, alias="bitmain-hashrate-percent")
    user_ip_cat: bool | None = Field(None, alias="bitmain-user-ip-cat")
    miner_mode: int = Field(
        validation_alias="bitmain-work-mode", serialization_alias="miner-mode"
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
    elapsed: int
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
    url: str
    user: str
    status: str
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
            settings.set_auth_alt("antminer", alt_pwd)
        self.passwds = settings.get_auth_list("antminer")

    def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            try:
                self.session.auth = HTTPDigestAuth(self.username, pwd)
                resp = self.session.get(
                    self.base_url, timeout=settings.get("http_request_timeout", 5.0)
                )
                resp.raise_for_status()
            except (
                requests.HTTPError,
                requests.ConnectionError,
                requests.Timeout,
            ) as ex:
                if isinstance(ex, (requests.ConnectionError, requests.Timeout)):
                    raise FailedConnectionError("Failed to connect or timeout occurred")
                elif isinstance(ex, requests.HTTPError):
                    continue
            else:
                if resp.status_code == 200:
                    self.authed = True
                    self.pwd = pwd
                    self.digest = self.session.auth
                    break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    def get_hostname(self) -> str:
        resp = self.get_system_info()
        return resp["hostname"]

    def get_mac_addr(self) -> str:
        resp = self.get_system_info()
        return resp["macaddr"]

    def get_api_version(self) -> str:
        return super().get_api_version()

    def get_system_info(self) -> dict:
        resp = self.send_command("GET", command="get_system_info")
        try:
            resobj = SystemInfo.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True, exclude_none=True)

    def get_network_info(self) -> dict:
        resp = self.send_command("GET", command="get_network_info")
        try:
            resobj = NetInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def log(self) -> dict:
        return self.send_command("GET", command="log")

    def summary(self) -> dict:
        resp = self.send_command("GET", command="summary")
        try:
            resobj = Summary.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def get_miner_conf(self) -> dict:
        resp = self.send_command("GET", command="get_miner_conf")
        try:
            resobj = MinerConf.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(exclude_none=True, by_alias=True)

    def set_miner_conf(self, conf: dict[str, Any]) -> dict:
        resp = self.send_command("POST", command="set_miner_conf", payload=conf)
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

    def pools(self) -> list[dict]:
        resp = self.send_command("GET", command="pools")
        try:
            resobj = Pools.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            ta = TypeAdapter(list[PoolInfo])
            return ta.dump_python(resobj.pools)

    def get_pool_conf(self) -> list[dict]:
        resp = self.get_miner_conf()
        ta = TypeAdapter(list[MinerConfPool])
        pools = ta.validate_python(resp["pools"], by_name=True)
        return ta.dump_python(pools, by_alias=True)

    def get_miner_status(self) -> dict:
        return super().get_miner_status()

    def get_blink_status(self) -> dict:
        resp = self.send_command("GET", command="get_blink_status")
        try:
            resobj = BlinkStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def blink(self, enabled: bool) -> dict:
        blink = BlinkStatus(blink=enabled)
        payload = blink.model_dump(mode="json")
        return self.send_command("POST", command="blink", payload=payload)

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        resp = self.get_miner_conf()
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
        return self.set_miner_conf(conf=new_conf)
