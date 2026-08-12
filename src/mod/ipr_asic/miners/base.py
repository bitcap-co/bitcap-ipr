# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, Self, TypeVar

from mod.ipr_asic.errors import APIError
from mod.ipr_asic.models import (
    PSU,
    Firmware,
    Hashboard,
    MinerInfo,
    MinerPool,
    MinerPreset,
    MinerSnapshot,
    MinerStats,
    MinerStatus,
    MinerSummary,
)
from mod.ipr_asic.protocol import BaseHTTPClient, BaseRPCClient, BaseTCPClient

T = TypeVar("T")


class BaseMiner(ABC):
    """Normalized interface for all APIs exposed by one physical miner.

    Transport clients remain responsible for communication and API response
    validation. Concrete miner backends translate those API-shaped responses
    into the standardized models returned by this interface.
    """

    def __init__(
        self,
        ip: str,
        *,
        http: BaseHTTPClient | None = None,
        rpc: BaseRPCClient | None = None,
        tcp: BaseTCPClient | None = None,
    ) -> None:
        self.ip = ip
        self.http = http
        self.rpc = rpc
        self.tcp = tcp
        self._collect_lock = asyncio.Lock()
        self._collection_errors: dict[str, Exception] = {}
        self._collection_tasks: dict[str, asyncio.Task[Any]] = {}
        self._collecting = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{self.ip}]"

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        self.close()

    async def collect(self) -> MinerSnapshot:
        """Collect every normalized section concurrently into one snapshot."""
        async with self._collect_lock:
            self._collection_errors.clear()
            self._collection_tasks.clear()
            self._collecting = True
            operations: dict[str, Awaitable[Any]] = {
                "summary": self.get_summary(),
                "status": self.get_status(),
                "stats": self.get_stats(),
                "pools": self.get_pools(),
                "hashboards": self.get_hashboards(),
                "psu": self.get_psu(),
                "firmware": self.get_firmware(),
                "preset": self.get_preset(),
            }
            try:
                results = await asyncio.gather(
                    *operations.values(), return_exceptions=True
                )

                data: dict[str, Any] = {}
                for section, result in zip(operations, results, strict=True):
                    if isinstance(result, Exception):
                        self._collection_errors[section] = result
                    elif isinstance(result, BaseException):
                        raise result
                    elif result is not None:
                        data[section] = result

                return MinerSnapshot(
                    ip=self.ip, errors=dict(self._collection_errors), **data
                )
            finally:
                self._collecting = False
                self._collection_tasks.clear()

    async def _cached_call(
        self, key: str, operation: Callable[[], Coroutine[Any, Any, T]]
    ) -> T:
        """Share one transport request across sections during collection."""
        if not self._collecting:
            return await operation()

        task = self._collection_tasks.get(key)
        if task is None:
            task = asyncio.create_task(operation())
            self._collection_tasks[key] = task
        return await task

    def _record_source_errors(self, section: str, **results: object) -> None:
        """Record failed API sources without discarding successful fallbacks."""
        for source, result in results.items():
            if isinstance(result, Exception):
                self._collection_errors[f"{section}.{source}"] = result

    def _check_sources(self, section: str, **results: object) -> None:
        """Record source errors and require at least one usable response."""
        self._record_source_errors(section, **results)
        errors = [
            result for result in results.values() if isinstance(result, Exception)
        ]
        if errors and len(errors) == len(results):
            raise errors[0]
        if not errors and not any(
            isinstance(result, (dict, list)) for result in results.values()
        ):
            raise APIError("Miner APIs returned no usable data")

    @staticmethod
    def _as_dict(result: object) -> dict[str, Any]:
        return result if isinstance(result, dict) else {}

    @staticmethod
    def _as_list(result: object) -> list[dict[str, Any]]:
        if not isinstance(result, list):
            return []
        return [item for item in result if isinstance(item, dict)]

    @staticmethod
    def _number(data: dict[str, Any], *keys: str) -> float | None:
        for key in keys:
            value = data.get(key)
            if value is None or isinstance(value, bool):
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _integer(data: dict[str, Any], *keys: str) -> int | None:
        value = BaseMiner._number(data, *keys)
        return int(value) if value is not None else None

    @staticmethod
    def _first(*values: Any) -> Any:
        return next((value for value in values if value is not None), None)

    @staticmethod
    def _numbers(value: object) -> list[float]:
        if value is None:
            return []
        return [float(number) for number in re.findall(r"-?\d+(?:\.\d+)?", str(value))]

    def _rpc_hashrate(self, data: dict[str, Any]) -> tuple[float | None, str | None]:
        """Extract hashrate from common CGMiner summary keys."""
        for key, unit in (
            ("THS av", "TH/s"),
            ("GHS av", "GH/s"),
            ("MHS av", "MH/s"),
            ("KHS av", "KH/s"),
            ("HS av", "H/s"),
            ("hashrate", None),
        ):
            value = self._number(data, key)
            if value is not None:
                return value, unit
        return None, None

    def _rpc_pool(self, data: dict[str, Any]) -> MinerPool | None:
        """Extract pool information from common CGMiner pool keys."""
        status = data.get("Status")
        return MinerPool(
            url=str(data.get("URL")),
            user=str(data.get("User")),
            priority=self._integer(data, "Priority"),
            type=self._integer(data, "POOL"),
            active=(str(status).casefold() == "active") if status is not None else None,
            accepted=self._integer(data, "Accepted"),
            rejected=self._integer(data, "Rejected"),
            stale=self._integer(data, "Stale"),
            difficulty=self._number(data, "Difficulty"),
            difficulty_accepted=self._number(data, "Difficulty Accepted"),
            difficulty_rejected=self._number(data, "Difficulty Rejected"),
        )

    async def get_info(self) -> MinerInfo | None:
        return None

    @abstractmethod
    async def get_summary(self) -> MinerSummary:
        """Return normalized realtime summary metrics, normally sourced from RPC."""
        raise NotImplementedError

    async def get_status(self) -> MinerStatus | None:
        """Return normalized operational state and readable errors."""
        return None

    async def get_stats(self) -> MinerStats | None:
        """Return normalized cumulative mining statistics, normally from RPC."""
        return None

    @abstractmethod
    async def get_pools(self) -> list[MinerPool]:
        """Return normalized pool performance metrics, normally sourced from RPC."""
        raise NotImplementedError

    async def get_hashboards(self) -> list[Hashboard]:
        """Return normalized hashboard telemetry."""
        return []

    async def get_psu(self) -> PSU | None:
        """Return normalized power-supply telemetry."""
        return None

    async def get_firmware(self) -> Firmware | None:
        """Return normalized firmware information."""
        return None

    async def get_preset(self) -> MinerPreset | None:
        """Return the active normalized mining preset or mode."""
        return None

    # async def get_pool_config(self) -> list[MinerConfPool]:
    #     ...

    # async def update_pool_config(...):
    #     ...

    # async def start(self):
    #     ...

    # async def stop(self):
    #     ...

    # async def restart(self):
    #     ...

    # async def reboot(self):
    #     ...

    # async def blink(self, enabled: bool):
    #     ...

    def close(self) -> None:
        """Close each configured transport once."""
        closed: set[int] = set()
        for client in (self.http, self.rpc, self.tcp):
            if client is not None and id(client) not in closed:
                client._close()
                closed.add(id(client))
