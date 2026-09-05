# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pydantic import BaseModel, Field, RootModel

from .models import (
    MinerConfigModel,
    MinerPoolModel,
    SummaryModel,
    SystemInfoModel,
)


class PowerPlan(BaseModel):
    info: str
    level: int


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


class Status(SystemInfoModel):
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
    adjustpower: int


class Devs(SummaryModel):
    status: int
    data: list[Chain]
