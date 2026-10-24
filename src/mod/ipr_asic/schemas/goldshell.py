# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pydantic import BaseModel, Field, RootModel

from .models import (
    MinerConfigModel,
    MinerPoolModel,
    NetworkInfoModel,
    SummaryModel,
    SystemInfoModel,
    VersionInfoModel,
)


class PowerPlanMode(BaseModel):
    info: str
    level: int
    temp_target: int | None = None


class PowerPlan(BaseModel):
    algo: str | None = None
    mode: list[PowerPlanMode] | None = None
    info: str | None = None
    level: int | None = None


class Settings(MinerConfigModel):
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


class Status(SystemInfoModel, VersionInfoModel):
    firmware: str
    hardware: str
    mcbversion: str
    model: str


class MinerPool(MinerPoolModel):
    url: str = ""
    user: str = ""
    passwd: str = Field("", alias="pass")
    pool_priority: int = Field(alias="pool-priority")
    legal: bool
    active: bool
    dragid: int


class PoolsResponse(RootModel[list[MinerPool]]):
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
    adjustpower: int | None = None


class Devs(SummaryModel):
    status: int
    data: list[Chain]


class MinerPasswdConfig(BaseModel):
    curr_passwd: str = Field(serialization_alias="oldpassword")
    new_passwd: str = Field(serialization_alias="newpassword")
    confirm_passwd: str = Field(serialization_alias="cfmpassword")


class IPSettings(BaseModel):
    ip: str | None = Field(None, validation_alias="IPv4addr")
    mask: str | None = Field(None, validation_alias="Subnetmask")
    gateway: str | None = Field(None, validation_alias="Router")
    dns1: str | None = Field(None, validation_alias="DNS1")
    dns2: str | None = Field(None, validation_alias="DNS2")


class NetworkSettings(BaseModel):
    dhcp: bool = Field(validation_alias="useDHCP")
    auto: bool = Field(validation_alias="useAuto")
    set_ip: IPSettings = Field(validation_alias="setIP")


class NetworkInfo(NetworkInfoModel):
    ip: str = ""
    mac: str = ""
    net_settings: NetworkSettings
