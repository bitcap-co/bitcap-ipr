from typing import Any

from pydantic import BaseModel, Field, field_validator

from .cgminer import BaseCGMinerResponse
from .models import (
    ActionResultModel,
    BlinkStatusModel,
    MinerConfigModel,
    MinerPoolModel,
    NetworkInfoModel,
    PoolConfig,
    SummaryModel,
    SystemInfoModel,
)


class ActionResult(ActionResultModel):
    stats: str
    status: str | None = None
    code: str

    def error(self) -> str | None:
        if self.status != "success" and self.stats != "success" or self.msg == "FAIL!":
            return f"API error ({self.code}): {self.stats} - {self.msg}"


class StatusResponse(BaseModel):
    status: str = Field(alias="STATUS")
    when: int
    msg: str = Field(alias="Msg")
    api_version: str


class InfoResponse(BaseModel):
    miner_version: str
    compile_time: str = Field(alias="CompileTime")
    type: str


class MinerPool(MinerPoolModel):
    index: int
    url: str
    status: str
    user: str
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


class PoolsResponse(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    pools: list[MinerPool] = Field(alias="POOLS")


class MinerStatus(BaseModel):
    type: str
    status: str
    code: int
    msg: str


class MinerSummary(SummaryModel):
    elapsed: int
    rate_5s: float
    rate_30m: float
    rate_avg: float
    rate_ideal: float
    rate_unit: str
    hw_all: int
    bestshare: int
    status: list[MinerStatus]


class SummaryResponse(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    summary: list[MinerSummary] = Field(alias="SUMMARY", default_factory=list)

    @field_validator("summary", mode="before")
    @classmethod
    def validate_summary(cls, v: list[MinerSummary]) -> list[MinerSummary]:
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


class StatsResponse(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    stats: list[MinerStat] = Field(alias="STATS")


class WarningResponse(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    error_message: str


class MinerInfo(BaseModel):
    miner_type: str
    subtype: str
    fw_version: str
    product_type: str | None = None


class SystemInfo(SystemInfoModel):
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
    cgminer_version: str | None = None


class NetworkInfo(NetworkInfoModel):
    nettype: str
    netdevice: str
    macaddr: str
    ipaddress: str
    netmask: str
    conf_nettype: str
    conf_netdevice: str
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


class MinerConfig(MinerConfigModel):
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
    pools: PoolConfig


class MinerPasswdConfig(BaseModel):
    curr_passwd: str = Field(default="", serialization_alias="curPwd")
    new_passwd: str = Field(default="", serialization_alias="newPwd")
    confirm_passwd: str = Field(default="", serialization_alias="confirmPwd")


class OldBlinkStatus(BlinkStatusModel):
    blink: bool = Field(validation_alias="isBlinking")


class OldMinerPasswdConfig(BaseModel):
    curr_passwd: str = Field(serialization_alias="current_pw")
    new_passwd: str = Field(serialization_alias="new_pw")
    confirm_new_passwd: str = Field(serialization_alias="new_pw_ctrl")


class OldMinerPool(MinerPoolModel):
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


class CGMinerResponse(BaseCGMinerResponse):
    summary: list[dict[str, Any]] | None = Field(default=None, alias="SUMMARY")
    pools: list[OldMinerPool] | None = Field(default=None, alias="POOLS")
