# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from string import Template
from typing import Any

import httpx
from pydantic import (
    BaseModel,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
)

from mod.ipr_asic import settings
from mod.ipr_asic.data import BlinkStatus, MinerConfPool
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient
from mod.ipr_asic.rpc.cgminer import Status

logger = logging.getLogger(__name__)


class ActionResponse(BaseModel):
    stats: str
    status: str | None = None
    code: str
    msg: str

    def error(self) -> str | None:
        if self.status != "success" and self.stats != "success" or self.msg == "FAIL!":
            return f"received API Error ({self.code}): {self.stats} - {self.msg}"


class StatusResponse(BaseModel):
    status: str = Field(alias="STATUS")
    when: int
    msg: str = Field(alias="Msg")
    api_version: str


class InfoResponse(BaseModel):
    miner_version: str
    compile_time: str = Field(alias="CompileTime")
    type: str


class MinerPool(BaseModel):
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
    diff1: int
    diffa: int
    diffr: int
    diffs: int
    lsdiff: int
    lstime: str


class Pools(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    pools: list[MinerPool] = Field(alias="POOLS")


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


class Summary(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    summary: list[MinerSummary] = Field(alias="SUMMARY")

    @field_validator("summary", mode="before")
    @classmethod
    def ensure_summary_length(cls, v: list) -> list:
        if len(v) != 1:
            raise ValueError
        return v


class MinerChain(BaseModel):
    index: int
    freq_avg: int
    rate_ideal: float
    rate_real: float
    asic_num: int
    asic: str
    temp_pic: list[int]
    temp_pcb: list[int]
    temp_chip: list[int]
    hw: int
    hwp: float | None = None
    eeprom_loaded: bool
    sn: str
    eeprom_level: int | None = None
    eeprom_vol: int | None = None
    eeprom_freq: int | None = None
    eeprom_bin: int | None = None
    eeprom_ft: str | None = None
    tpl: list[list[int]] | None = None


class MinerStat(BaseModel):
    elapsed: int
    rate_5s: float
    rate_30m: float
    rate_avg: float
    rate_ideal: float
    rate_sale: int | None = None
    rate_unit: str
    chain_num: int
    fan_num: int
    fan: list[int]
    hwp_total: float
    miner_mode: int | None = Field(None, alias="miner-mode")
    freq_level: int | None = Field(None, alias="freq-level")
    watt: int | None = None
    jt: float | None = None
    ambient_temp: float | None = None
    chain: list[MinerChain]


class Stats(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    stats: list[MinerStat] = Field(alias="STATS")


class Warning(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    error_message: str


class MinerType(BaseModel):
    miner_type: str
    subtype: str
    fw_version: str
    product_type: str | None = None


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


class MinerNetworkConfig(BaseModel):
    ip_address: str = Field(
        "", validation_alias="conf_ipaddress", serialization_alias="ipAddress"
    )
    ip_dns: str = Field(
        "", validation_alias="conf_dnsservers", serialization_alias="ipDns"
    )
    ip_gateway: str = Field(
        "", validation_alias="conf_gateway", serialization_alias="ipGateway"
    )
    ip_host: str = Field(
        "", validation_alias="conf_hostname", serialization_alias="ipHost"
    )
    ip_pro: int = Field(
        1, gt=0, le=2, validation_alias="conf_nettype", serialization_alias="ipPro"
    )
    ip_sub: str = Field(
        "", validation_alias="conf_netmask", serialization_alias="ipSub"
    )


class MinerConfig(BaseModel):
    algo: str | None = Field(None, exclude=True)
    fan_ctrl: bool | None = Field(None, alias="bitmain-fan-ctrl")
    fan_pwm: int | None = Field(None, alias="bitmain-fan-pwm")
    freq_level: int | None = Field(
        None, validation_alias="bitmain-freq-level", serialization_alias="freq-level"
    )
    freq: int | None = Field(
        None, validation_alias="bitmain-freq", serialization_alias="freq"
    )
    voltage: str | None = Field(None, alias="bitmain-voltage")
    hashrate_per: str | None = Field(None, alias="bitmain-hashrate-percent")
    user_ip_cat: str | None = Field(None, alias="bitmain-user-ip-cat")
    miner_mode: str = Field(
        validation_alias="bitmain-work-mode", serialization_alias="miner-mode"
    )
    pools: list[MinerConfPool]


class MinerConfigPasswd(BaseModel):
    curr_passwd: str = Field("", serialization_alias="curPwd")
    new_passwd: str = Field("", serialization_alias="newPwd")
    confirm_passwd: str = Field("", serialization_alias="confirmPwd")


class AntminerHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, transport=transport)

        self.command_path = Template("cgi-bin/${command}.cgi")

        self.username: str = "root"
        if alt_pwd:
            settings.set_alt_auth("antminer", alt_pwd)
        self.passwds = settings.get_auth_list("antminer")

    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            digest = httpx.DigestAuth(self.username, pwd)
            try:
                async with self._new_client(auth=digest) as client:
                    resp = await client.get(url=self.base_url)
                    resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
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
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True, exclude_none=True)

    async def get_network_info(self) -> dict:
        resp = await self.send_command("GET", command="get_network_info")
        try:
            resobj = NetInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def log(self) -> dict:
        return await self.send_command("GET", command="log")

    async def summary(self) -> dict:
        resp = await self.send_command("GET", command="summary")
        try:
            resobj = Summary.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.summary[0].model_dump(by_alias=True)

    async def get_miner_conf(self) -> dict:
        resp = await self.send_command("GET", command="get_miner_conf")
        try:
            resobj = MinerConfig.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump(exclude_none=True)

    async def set_miner_conf(self, conf: dict[str, Any]) -> dict:
        resp = await self.send_command("POST", command="set_miner_conf", payload=conf)
        try:
            resobj = ActionResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
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
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            ta = TypeAdapter(list[MinerPool])
            return ta.dump_python(resobj.pools, by_alias=True)

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
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def blink(self, enabled: bool) -> dict:
        blink = BlinkStatus(blink=enabled)
        payload = blink.model_dump(mode="json")
        return await self.send_command("POST", command="blink", payload=payload)

    async def set_miner_mode(self, mode: int = 0) -> dict:
        resp = await self.get_miner_conf()
        conf = MinerConfig.model_construct(**resp)
        conf.miner_mode = f"{mode}"
        ta = TypeAdapter(list[MinerConfPool])
        pools = ta.validate_python(resp["pools"], by_name=True)
        conf.pools = pools

        return await self.set_miner_conf(
            conf=conf.model_dump(mode="json", by_alias=True, exclude_none=True)
        )

    async def start(self) -> dict:
        return await self.set_miner_mode(mode=0)

    async def stop(self) -> dict:
        return await self.set_miner_mode(mode=1)

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
        conf = MinerConfig.model_construct(**resp)
        ta = TypeAdapter(list[MinerConfPool])
        pool_conf: list[dict[str, str]] = ta.dump_python(conf.pools, by_alias=True)

        for i in range(len(urls)):
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


class OldBlinkStatus(BaseModel):
    blink: bool = Field(alias="isBlinking")


class Pool(BaseModel):
    url: str = Field(alias="URL")
    status: str = Field(alias="Status")
    user: str = Field(alias="User")
    diff: str = Field(alias="Diff")
    pool: int = Field(alias="POOL")
    priority: int = Field(alias="Priority")
    quota: int = Field(alias="Quota")
    getworks: int = Field(alias="Getworks")
    accepted: int = Field(alias="Accepted")
    rejected: int = Field(alias="Rejected")
    stale: int = Field(alias="Stale")
    diffa: float | None = Field(None, alias="Difficulty Accepted")
    diffr: float | None = Field(None, alias="Difficulty Rejected")
    stratum_diff: float | None = Field(None, alias="Stratum Difficulty")
    stratum_active: bool = Field(alias="Stratum Active")


class Response(BaseModel):
    id: int
    status: list[Status] = Field(alias="STATUS")
    summary: list[dict[str, Any]] | None = Field(None, alias="SUMMARY")
    pools: list[Pool] | None = Field(None, alias="POOLS")

    def error(self) -> str | None:
        for status in self.status:
            match status.status:
                case "E" | "F":
                    return f"received API error ({status.code}) {status.msg} - {status.description}"
                case _:
                    return None


class AntminerOldHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, transport=transport)

        self.command_path = Template("cgi-bin/${command}.cgi")

        self.username: str = "root"
        if alt_pwd:
            settings.set_alt_auth("antminer", alt_pwd)
        self.passwds = settings.get_auth_list("antminer")

    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            digest = httpx.DigestAuth(self.username, pwd)
            try:
                async with self._new_client(auth=digest) as client:
                    resp = await client.get(url=self.base_url)
                    resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
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

    def _validate_response(self, data: dict) -> Response:
        try:
            resobj = Response.model_validate(obj=data, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {APIError(err)!s}")
                raise APIError("Command failed!")
            return resobj

    async def get_hostname(self) -> str:
        resp = await self.get_system_info()
        return resp["hostname"]

    async def get_mac_addr(self) -> str:
        resp = await self.get_system_info()
        return resp["macaddr"]

    async def get_api_version(self) -> str:
        resp = await self.get_system_info()
        return resp["cgminer_version"]

    async def get_system_info(self) -> dict:
        resp = await self.send_command("GET", command="get_system_info")
        try:
            resobj = SystemInfo.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True, exclude_none=True)

    async def get_network_info(self) -> dict:
        resp = await self.send_command("GET", command="get_network_info")
        try:
            resobj = NetInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def log(self) -> dict:
        return await self.send_command("GET", command="get_kernel_log")

    async def summary(self) -> dict:
        resp = await self.send_command("GET", command="miner_summary")
        valid = self._validate_response(resp)
        if valid.summary is None or len(valid.summary) != 1:
            raise APIInvalidResponse(reason="Malformed")
        else:
            return valid.summary[0]

    async def get_miner_conf(self) -> dict:
        resp = await self.send_command("GET", command="get_miner_conf")
        try:
            resobj = MinerConfig.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump(exclude_none=True, by_alias=True)

    async def set_miner_conf(self, conf: dict) -> dict:
        return await self.send_command("POST", command="set_miner_conf", data=conf)

    async def pools(self) -> list[dict]:
        resp = await self.send_command("GET", command="miner_pools")
        valid = self._validate_response(resp)
        if valid.pools is None:
            raise APIInvalidResponse(reason="Malformed")
        else:
            ta = TypeAdapter(list[Pool])
            pools = ta.validate_python(valid.pools, by_alias=True)
            return ta.dump_python(pools, by_alias=True)

    async def get_pool_conf(self) -> list[dict]:
        pools = await self.pools()
        pool_conf = []
        for pool in pools:
            pool_conf.append(
                MinerConfPool(url=pool["URL"], user=pool["User"]).model_dump(
                    by_alias=True
                )
            )
        return pool_conf

    async def get_miner_status(self) -> dict:
        return await super().get_miner_status()

    async def get_blink_status(self) -> dict:
        resp = await self.send_command(
            "GET", command="blink", data={"action": "onPageLoaded"}
        )
        try:
            resobj = OldBlinkStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def blink(self, enabled: bool) -> dict:
        data = {"action": "startBlink" if enabled else "stopBlink"}
        return await self.send_command("POST", command="blink", data=data)

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
        conf = MinerConfig.model_construct(**resp)

        data: dict[str, Any] = {}
        for i in range(len(urls)):
            data[f"_ant_pool{i + 1}url"] = urls[i]
            data[f"_ant_pool{i + 1}user"] = users[i]
            data[f"_ant_pool{i + 1}pw"] = passwds[i]

        data["_ant_nobeeper"] = "false"
        data["_ant_notempcontrol"] = "false"
        if conf.fan_ctrl:
            data["_ant_fan_customize_switch"] = "true"
            data["_ant_fan_customize_value"] = conf.fan_pwm
        else:
            data["_ant_fan_customize_switch"] = "false"
            data["_ant_fan_customize_value"] = ""
        data["_ant_freq"] = conf.freq

        return await self.set_miner_conf(conf=data)
