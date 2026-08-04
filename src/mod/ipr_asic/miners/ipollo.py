# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from mod.ipr_asic.errors import APIInvalidResponse
from mod.ipr_asic.http import IPolloHTTPClient
from mod.ipr_asic.models import Hashboard, MinerPool, MinerStats, MinerSummary
from mod.ipr_asic.protocol import BaseHTTPClient, BaseRPCClient
from mod.ipr_asic.rpc import IPolloRPCClient

from .base import BaseMiner

# multiplier to offset the standard unit of Gh/s
BASE_MULTIPLIER = 1_000_000_000


class BaseHashrate(BaseModel):
    mhs2_av: float = Field(alias="MHS2 av")
    multiplier: int = BASE_MULTIPLIER

    @property
    def hashrate(self) -> float:
        """Return the hashrate normalized to hashes per second."""
        return self.mhs2_av * self.multiplier


class Summary(BaseHashrate):
    elapsed: int = Field(alias="Elapsed")
    mhs_av: float = Field(alias="MHS av")
    mhs_5s: float = Field(alias="MHS 5s")
    mhs_1m: float = Field(alias="MHS 1m")
    mhs_5m: float = Field(alias="MHS 5m")
    mhs_15m: float = Field(alias="MHS 15m")
    found_blocks: int = Field(alias="Found Blocks")
    getworks: int = Field(alias="Getworks")
    accepted: int = Field(alias="Accepted")
    rejected: int = Field(alias="Rejected")
    hw_errors: int = Field(alias="Hardware Errors")
    utility: float = Field(alias="Utility")
    discarded: int = Field(alias="Discarded")
    stale: int = Field(alias="Stale")
    getfailures: int = Field(alias="Get Failures")
    local_work: int = Field(alias="Local Work")
    remote_failures: int = Field(alias="Remote Failures")
    network_blocks: int = Field(alias="Network Blocks")
    total_mh: float = Field(alias="Total MH")
    work_utility: float = Field(alias="Work Utility")
    diffa: float = Field(alias="Difficulty Accepted")
    diffr: float = Field(alias="Difficulty Rejected")
    diffs: float = Field(alias="Difficulty Stale")
    best_share: int = Field(alias="Best Share")
    device_hardware: float = Field(alias="Device Hardware%")
    device_rejected: float = Field(alias="Device Rejected%")
    pool_rejected: float = Field(alias="Pool Rejected%")
    pool_stale: float = Field(alias="Pool Stale%")
    last_getwork: int = Field(alias="Last getwork")


class Stats(BaseModel):
    stats: int | None = Field(None, alias="STATS")
    id: str | None = Field(None, alias="ID")
    elapsed: int | None = Field(None, alias="Elapsed")
    calls: int | None = Field(None, alias="Calls")
    wait: float | None = Field(None, alias="Wait")
    max: float | None = Field(None, alias="Max")
    min: float | None = Field(None, alias="Min")
    # Each UART value contains bracketed per-ASIC arrays. Example:
    # asic_count[10] chip_temp[55.10 ...] chip_status[1 ...]
    # asic_hash_rate[4.54 ...] asic_accepted[48416 ...]
    uart_id0: str | None = Field(None, alias="UART ID0")
    uart_id1: str | None = Field(None, alias="UART ID1")
    uart_id2: str | None = Field(None, alias="UART ID2")
    g_model: str | None = Field(None, alias="G-Model")
    enable_port: str | None = Field(None, alias="enable_port")
    algo: str | None = Field(None, alias="Algo")
    unit: str | None = Field(None, alias="Unit")
    hashrate: float | None = Field(None, alias="Hashrate")
    fan: str | None = Field(None, alias="Fan")  # Fan[5490 5550 5820 5699]
    temp: str | None = Field(None, alias="Temp")  # Temp[0.0 24.5 29.5 24.5 27.0]

    def uart_values(self) -> tuple[str | None, str | None, str | None]:
        return self.uart_id0, self.uart_id1, self.uart_id2


class _ParsedHashboard(BaseModel):
    hashboard: Hashboard
    accepted: int = 0
    rejected: int = 0


class IPolloMiner(BaseMiner):
    """Normalized iPollo backend composed from HTTP and CGMiner APIs."""

    def __init__(
        self,
        ip: str,
        *,
        alt_pwd: str | None = None,
        http_port: int = 80,
        rpc_port: int = 4028,
        http: BaseHTTPClient | None = None,
        rpc: BaseRPCClient | None = None,
    ) -> None:
        if http is None:
            http = IPolloHTTPClient(ip, port=http_port, alt_pwd=alt_pwd)
        if rpc is None:
            rpc = IPolloRPCClient(ip, port=rpc_port, alt_pwd=alt_pwd)
        super().__init__(ip, http=http, rpc=rpc)

    async def get_summary(self) -> MinerSummary:
        """Build normalized realtime summary metrics from CGMiner RPC."""
        assert self.rpc is not None
        rpc_summary, stats = await asyncio.gather(
            self.rpc.summary(), self._get_rpc_stats()
        )
        rpc_data = self._as_dict(rpc_summary)
        hashrate, unit = self._rpc_hashrate(rpc_data)
        fans = self._numbers(stats.fan)
        temperatures = self._numbers(stats.temp)

        return MinerSummary(
            elapsed=self._integer(rpc_data, "Elapsed", "elapsed"),
            hashrate=hashrate,
            hashrate_ideal=self._number(
                rpc_data, "MHS ideal", "GHS ideal", "KHS ideal", "hashrate_ideal"
            ),
            hashrate_unit=unit,
            accepted=self._integer(rpc_data, "Accepted", "accepted"),
            rejected=self._integer(rpc_data, "Rejected", "rejected"),
            stale=self._integer(rpc_data, "Stale", "stale"),
            hw_errors=self._integer(rpc_data, "Hardware Errors", "hw_errors"),
            chip_temp=int(max(temperatures)) if temperatures else None,
            fans=[int(fan) for fan in fans],
        )

    async def get_stats(self) -> MinerStats:
        """Aggregate per-ASIC accepted and rejected work from RPC stats."""
        boards = self._parse_hashboards(await self._get_rpc_stats())
        return MinerStats(
            accepted=sum(board.accepted for board in boards),
            rejected=sum(board.rejected for board in boards),
        )

    async def get_hashboards(self) -> list[Hashboard]:
        """Parse each UART's bracketed ASIC telemetry into a hashboard."""
        return [
            board.hashboard
            for board in self._parse_hashboards(await self._get_rpc_stats())
        ]

    async def get_pools(self) -> list[MinerPool]:
        """Build normalized realtime pool metrics from CGMiner RPC."""
        assert self.rpc is not None
        return [self._rpc_pool(pool) for pool in self._as_list(await self.rpc.pools())]

    async def _get_rpc_stats(self) -> Stats:
        assert self.rpc is not None
        raw_stats = self._as_list(await self._cached_call("rpc.stats", self.rpc.stats))
        for data in raw_stats:
            if any(key.startswith("UART ID") for key in data) or "Fan" in data:
                try:
                    return Stats.model_validate(data)
                except ValidationError as ex:
                    raise APIInvalidResponse(reason=str(ex)) from ex
        raise APIInvalidResponse(reason="iPollo RPC stats contained no miner data")

    def _parse_hashboards(self, stats: Stats) -> list[_ParsedHashboard]:
        boards: list[_ParsedHashboard] = []
        for board_id, raw_uart in enumerate(stats.uart_values()):
            if raw_uart:
                boards.append(self._parse_uart(board_id, raw_uart))
        return boards

    def _parse_uart(self, board_id: int, raw_uart: str) -> _ParsedHashboard:
        sections = {
            name: values for name, values in re.findall(r"(\w+)\[([^\]]*)\]", raw_uart)
        }
        chip_status = [
            int(value) for value in self._numbers(sections.get("chip_status"))
        ]
        chip_temps = self._numbers(sections.get("chip_temp"))
        chip_hashrates = self._numbers(sections.get("asic_hash_rate"))
        accepted = [
            int(value) for value in self._numbers(sections.get("asic_accepted"))
        ]
        rejected = [
            int(value) for value in self._numbers(sections.get("asic_rejected"))
        ]
        count_values = self._numbers(sections.get("asic_count"))
        chip_count = int(count_values[0]) if count_values else len(chip_status)
        healthy_count = sum(status > 0 for status in chip_status)
        inactive_count = max(chip_count - healthy_count, 0)

        return _ParsedHashboard(
            hashboard=Hashboard(
                id=board_id,
                name=f"UART ID{board_id}",
                status="Alive" if healthy_count else "Inactive",
                error=(f"{inactive_count} ASICs inactive" if inactive_count else None),
                enabled=healthy_count > 0,
                chip_count=chip_count,
                chip_count_healthy=healthy_count,
                hashrate=sum(chip_hashrates) * BASE_MULTIPLIER,
                chip_temp=int(max(chip_temps)) if chip_temps else None,
            ),
            accepted=sum(accepted),
            rejected=sum(rejected),
        )

    def _rpc_pool(self, data: dict[str, Any]) -> MinerPool:
        status = data.get("Status", data.get("status"))
        return MinerPool(
            url=str(data.get("URL", data.get("url", ""))).split(",", 1)[0],
            user=str(data.get("User", data.get("user", ""))),
            priority=self._integer(data, "Priority", "priority"),
            type=self._integer(data, "POOL", "pool"),
            active=(str(status).casefold() == "alive") if status is not None else None,
            accepted=self._integer(data, "Accepted", "accepted"),
            rejected=self._integer(data, "Rejected", "rejected"),
            stale=self._integer(data, "Stale", "stale"),
            difficulty=self._number(data, "Diff", "difficulty"),
            difficulty_accepted=self._number(
                data, "Difficulty Accepted", "difficulty_accepted"
            ),
            difficulty_rejected=self._number(
                data, "Difficulty Rejected", "difficulty_rejected"
            ),
        )

    def _rpc_hashrate(self, data: dict[str, Any]) -> tuple[float | None, str | None]:
        try:
            base_hashrate = BaseHashrate.model_validate(data)
        except ValidationError:
            return super()._rpc_hashrate(data)
        return base_hashrate.hashrate, "Gh/s"
