# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pydantic import BaseModel, Field, field_validator

from .antminer import MinerStatus
from .models import (
    MinerConfigModel,
    MinerPoolModel,
    PoolConfig,
    SummaryModel,
)


class InfoResponse(BaseModel):
    miner_version: str
    compile_time: str = Field(alias="CompileTime")
    dev_sn: str
    type: str
    hw_version: str


class StatusResponse(BaseModel):
    status: str = Field(alias="STATUS")
    when: int
    timestamp: int
    api_version: str
    msg: str = Field(alias="Msg")


class MinerPool(MinerPoolModel):
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


class PoolsResponse(BaseModel):
    status: StatusResponse = Field(alias="STATUS")
    info: InfoResponse = Field(alias="INFO")
    rejected_per: float = Field(alias="Device Rejected%")
    rejected_total: int = Field(alias="Device Total Rejected")
    total_work: int = Field(alias="Device Total Work")
    pools: list[MinerPool] = Field(alias="POOLS")


class MinerConfig(MinerConfigModel):
    fan_ctrl: bool = Field(alias="fc-fan-ctrl")
    fan_pwm: str = Field(alias="fc-fan-pwm")
    freq: str = Field(alias="fc-freq")
    freq_level: str = Field(alias="fc-freq-level")
    voltage: str = Field(alias="fc-voltage")
    miner_mode: int = Field(alias="fc-work-mode")
    algo: str
    pools: PoolConfig


class MinerSummary(SummaryModel):
    elapsed: int
    rate_5s: float
    rate_30m: float
    rate_avg: float
    rate_ideal: float
    rate_unit: str
    bestshare: int
    hw_all: float
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
