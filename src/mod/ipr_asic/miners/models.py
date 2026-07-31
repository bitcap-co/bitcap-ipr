# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class MinerSnapshot(BaseModel):
    """Raw multi-protocol snapshot for one physical miner."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ip: str
    http: ProtocolResult | None = None
    rpc: ProtocolResult | None = None

    @property
    def ok(self) -> bool:
        results = (self.http, self.rpc)
        return any(result is not None and bool(result.data) for result in results)

    @property
    def errors(self) -> dict[str, Exception]:
        errors: dict[str, Exception] = {}
        for protocol, result in (("http", self.http), ("rpc", self.rpc)):
            if result is None:
                continue
            errors.update(
                {
                    f"{protocol}.{command}": error
                    for command, error in result.errors.items()
                }
            )
        return errors


class MinerPool(BaseModel):
    url: str
    user: str
    priority: int
    type: int
    active: bool
    accepted: int
    rejected: int
    stale: int
    difficulty: float
    difficulty_accepted: float
    difficulty_rejected: float


class MinerStatus(BaseModel):
    pass


class MinerStats(BaseModel):
    pass


class MinerSummary(BaseModel):
    pass


class Hashboard(BaseModel):
    pass


class PSU(BaseModel):
    pass


class Firmware(BaseModel):
    pass


class MinerPreset(BaseModel):
    pass
