# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from string import Template

import requests
from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator

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
    status: int
    result: int


class LoginResponse(BaseModel):
    state: int
    msg: str


class ConfResponse(BaseModel):
    result: bool
    api: bool
    file_write: bool = Field(alias="fileWrite")
    msg: str

    def error(self) -> str | None:
        if not self.result or not self.api or not self.file_write:
            return f"received API Error: result {self.result} - {self.msg}"


class NetInfo(BaseModel):
    nettype: str
    conf_ipaddress: str
    conf_netmask: str
    conf_gateway: str
    conf_dnsservers: str
    conf_dnsservers_backup: str
    name: list[str]


class SystemInfo(BaseModel):
    low_power: int
    normal: int
    high_performance: int
    custom: int
    firmware_version: str
    ctrl_version: str
    miner_type: str
    brand: str
    psu_model: str
    macaddr: str
    ipaddress: str
    dhcp: str = Field(alias="DHCP")
    mining_mode: str = Field(alias="miningMode")
    rated_hashrate: int = Field(alias="ratedHashrate")
    crtl_sn: str
    system_time: str = Field(alias="systemTime")
    upgrade_result: str
    tuning_done: int
    led: str


class PoolFormConf(BaseModel):
    poolurl1: str = ""
    poolurl2: str = ""
    poolurl3: str = ""
    pooluser1: str = ""
    pooluser2: str = ""
    pooluser3: str = ""
    poolpwd1: str = ""
    poolpwd2: str = ""
    poolpwd3: str = ""


class MinerConf(BaseModel):
    miner_mode: str = Field(
        serialization_alias="minerMode", validation_alias="xk-h3x-miningmode"
    )
    psu_max_power: str = Field(
        serialization_alias="psuInputMaxpower",
        validation_alias="xk-h3x-psu-input-max-power",
    )
    # network_hashrate: str = Field(serialization_alias="networkHashrate", validation_alias="xk-h3x-network-hashrate")
    # block_reward: str = Field(serialization_alias="blockReward", validation_alias="xk-h3x-block-reward")
    # btc_price: str = Field(serialization_alias="btcPrice", validation_alias="xk-h3x-btc-price")
    # electric_price: str = Field(serialization_alias="electricPrice", validation_alias="xk-h3x-electric-price")
    # custom_expect_hashrate: str = Field(serialization_alias="CustomHashExpect", validation_alias="xk-h3x-custom-expect-hashrate")
    # custom_power_ratio_range: str = Field(serialization_alias="PoTValueRange", validation_alias="xk-h3x-custom-power-ratio-range")
    pools: list[MinerConfPool]


class Summary(BaseModel):
    elapsed: int
    mhsav: float
    foundblocks: str
    rejected: float


class Pool(BaseModel):
    id: int | None
    url: str | None
    user: str | None
    status: str | None
    is_active: bool | None = Field(alias="isActive")
    diff: float | None
    getworks: int | None
    priority: int | None
    accept: int | None
    rejected: int | None
    rejected_p: float | None = Field(alias="rejected%")
    stale: int | None
    diffa: float | None = Field(alias="diffA")
    diffr: float | None = Field(alias="diffR")
    lsdiff: float | None
    lstime: str | None

    @field_validator("*", mode="before")
    @classmethod
    def _emtpy_to_none(cls, field_value):
        if field_value == "":
            return None
        return field_value


class MinerStatus(BaseModel):
    summary: Summary
    pools: list[Pool]


class SealminerHTTPClient(BaseHTTPClient):
    def __init__(self, ip: str, port: int = 80, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)

        self.username: str = "seal"
        if alt_pwd:
            settings.set_auth_alt("sealminer", alt_pwd)
        self.passwds = settings.get_auth_list("sealminer")

        self.command_path = Template("cgi-bin/${command}.php")

    def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            data = {"username": self.username, "origin_pwd": pwd}
            try:
                resp = self._do_http(method="POST", path="cgi-bin/login.php", data=data)
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
                    try:
                        resobj = resp.json()
                        login_response = LoginResponse(**resobj)
                    except (requests.exceptions.JSONDecodeError, ValidationError):
                        break
                    else:
                        if login_response.state != 0:
                            continue
                        self.authed = True
                        self.pwd = pwd
                        break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    def get_hostname(self) -> str:
        return super().get_hostname()

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
            return resobj.model_dump()

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

    def log(self, *args, **kwargs) -> dict:
        return super().log(*args, **kwargs)

    def summary(self) -> dict:
        resp = self.send_command("GET", command="miner-status")
        try:
            resobj = MinerStatus.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def get_miner_conf(self) -> dict:
        resp = self.send_command("GET", command="get_miner_poolconf")
        try:
            resobj = MinerConf.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True)

    def set_miner_conf(self, conf: dict) -> dict:
        resp = self.send_command("POST", command="set_miner_poolconf", payload=conf)
        try:
            resobj = ConfResponse.model_validate(obj=resp, by_alias=True)
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
            return resobj.model_dump()

    def pools(self) -> list[dict]:
        resp = self.summary()
        ta = TypeAdapter(list[Pool])
        pools = ta.validate_python(resp["pools"], by_name=True)
        return ta.dump_python(pools, by_alias=True)

    def get_pool_conf(self) -> list[dict]:
        resp = self.get_miner_conf()
        ta = TypeAdapter(list[MinerConfPool])
        pools = ta.validate_python(resp["pools"], by_name=True)
        return ta.dump_python(pools, by_alias=True)

    def get_blink_status(self) -> dict:
        resp = self.get_system_info()
        blink = BlinkStatus(blink=True if resp["led"] == "on" else False)
        return blink.model_dump()

    def get_miner_status(self) -> dict:
        return super().get_miner_status()

    def blink(self, enabled: bool, *args, **kwargs) -> dict:
        data = '{"key":"led","value":"%s"}' % ("on" if enabled else "off")
        return self.send_command("POST", command="led_conf", data=data)

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        pool_conf: list[dict[str, str]] = self.get_pool_conf()

        new_conf = {
            "poolurl1": "",
            "pooluser1": "",
            "poolpwd1": "",
            "poolurl2": "",
            "pooluser2": "",
            "poolpwd2": "",
            "poolurl3": "",
            "pooluser3": "",
            "poolpwd3": "",
        }
        for i in range(0, len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            idx = i + 1
            new_conf[f"poolulr{idx}"] = urls[i]
            new_conf[f"pooluser{idx}"] = users[i]
            new_conf[f"poolpwd{idx}"] = passwds[i]
        return self.set_miner_conf(conf=new_conf)
