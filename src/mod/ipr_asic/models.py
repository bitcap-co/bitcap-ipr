# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mod.ipr_asic.data import MinerAlgorithm, MinerPlatform, MinerType


# Common API dataclasses
class MinerConfPool(BaseModel):
    url: str = ""
    user: str = ""
    passwd: str = Field(default="", alias="pass")


class BlinkStatus(BaseModel):
    blink: bool


class ActionResponse(BaseModel):
    success: bool
    msg: str = ""


# Miner backend dataclasses
class ProtocolResult(BaseModel):
    """Raw data and endpoint errors collected from one miner protocol."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: dict[str, Any] = Field(default_factory=dict)
    errors: dict[str, Exception] = Field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def partial(self) -> bool:
        return bool(self.data) and bool(self.errors)


class MinerInfo(BaseModel):
    type: MinerType
    subtype: str | None = None
    algorithm: MinerAlgorithm | None = None
    hostname: str | None = None
    mac: str | None = None
    serial: str | None = None
    platform: MinerPlatform | None = None


class MinerPool(BaseModel):
    url: str
    user: str
    passwd: str | None = None
    priority: int | None = None
    type: int | None = None
    active: bool | None = None
    accepted: int | None = None
    rejected: int | None = None
    stale: int | None = None
    difficulty: float | None = None
    difficulty_accepted: float | None = None
    difficulty_rejected: float | None = None


class MinerStatus(BaseModel):
    state: str | None = None
    message: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class MinerStats(BaseModel):
    accepted: int | None = None
    rejected: int | None = None
    stale: int | None = None
    hw_errors: int | None = None


class MinerSummary(BaseModel):
    elapsed: int | None = None
    hashrate: float | None = None
    hashrate_ideal: float | None = None
    hashrate_unit: str | None = None
    accepted: int | None = None
    rejected: int | None = None
    stale: int | None = None
    hw_errors: int | None = None
    pcb_temp: int | None = None
    chip_temp: int | None = None
    voltage: float | None = None
    frequency: float | None = None
    power: float | None = None
    fans: list[int] = Field(default_factory=list)


class Hashboard(BaseModel):
    id: int
    name: str | None = None
    serial: str | None = None
    status: str | None = None
    error: str | None = None
    enabled: bool | None = None
    has_pic: bool | None = None
    chip_bin: int | None = None
    chip_count: int | None = None
    chip_count_healthy: int | None = None
    hashrate: float | None = None
    hashrate_ideal: float | None = None
    voltage: float | None = None
    power: float | None = None
    frequency: float | None = None
    pcb_temp: int | None = None
    chip_temp: int | None = None
    hw_errors: int | None = None


class PSU(BaseModel):
    model: str | None = None
    serial: str | None = None
    current: float | None = None
    voltage: float | None = None
    power: float | None = None


class Firmware(BaseModel):
    type: str | None = None
    version: str | None = None
    build: str | None = None
    install_type: str | None = None
    platform: str | None = None


class MinerPreset(BaseModel):
    pass


class MinerSnapshot(BaseModel):
    """Normalized point-in-time view of one physical miner."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ip: str
    info: MinerInfo | None = None
    summary: MinerSummary | None = None
    status: MinerStatus | None = None
    stats: MinerStats | None = None
    pools: list[MinerPool] = Field(default_factory=list)
    hashboards: list[Hashboard] = Field(default_factory=list)
    psu: PSU | None = None
    firmware: Firmware | None = None
    preset: MinerPreset | None = None
    errors: dict[str, Exception] = Field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return any(
            (
                self.summary is not None,
                self.status is not None,
                self.stats is not None,
                bool(self.pools),
                bool(self.hashboards),
                self.psu is not None,
                self.firmware is not None,
                self.preset is not None,
            )
        )

    @property
    def partial(self) -> bool:
        return self.ok and bool(self.errors)
