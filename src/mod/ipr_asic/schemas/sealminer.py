# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pydantic import BaseModel, Field, field_validator

from .models import (
    MinerConfigModel,
    MinerPoolModel,
    NetworkInfoModel,
    PoolConfig,
    SummaryModel,
    SystemInfoModel,
)


class ActionResult(BaseModel):
    status: int | None = None
    result: int

    def error(self) -> str | None:
        if self.result != 0:
            return f"API error ({self.result}): non-zero result."


class ConfigResult(BaseModel):
    result: bool
    api: bool
    file_write: bool = Field(validation_alias="fileWrite")
    msg: str

    def error(self) -> str | None:
        if not self.result or not self.api or not self.file_write:
            return f"API Error: result {self.result} - {self.msg}"


class LoginResponse(BaseModel):
    state: int
    msg: str


class NetworkInfo(NetworkInfoModel):
    nettype: str
    conf_ipaddress: str
    conf_netmask: str
    conf_gateway: str
    conf_dnsservers: str
    conf_dnsservers_backup: str
    name: list[str]


class SystemInfo(SystemInfoModel):
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


class PoolConfigForm(BaseModel):
    poolurl1: str = ""
    poolurl2: str = ""
    poolurl3: str = ""
    pooluser1: str = ""
    pooluser2: str = ""
    pooluser3: str = ""
    poolpwd1: str = ""
    poolpwd2: str = ""
    poolpwd3: str = ""


class MinerConfig(MinerConfigModel):
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
    pools: PoolConfig


class MinerSummary(BaseModel):
    elapsed: int | None
    mhsav: float | None
    foundblocks: str | None
    rejected: float | None

    @field_validator("*", mode="before")
    @classmethod
    def _empty_to_none(cls, field_value):
        if field_value == "":
            return None
        return field_value


class MinerPool(MinerPoolModel):
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


class Summary(SummaryModel):
    summary: MinerSummary
    pools: list[MinerPool]


class MinerPasswdConfig(BaseModel):
    username: str = Field(serialization_alias="user_name")
    curr_passwd: str = Field(serialization_alias="origin_pwd")
    new_passwd: str = Field(serialization_alias="new_pwd")
    confirm_passwd: str = Field(serialization_alias="confirm_pwd")
