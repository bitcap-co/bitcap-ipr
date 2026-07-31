# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from __future__ import annotations

import asyncio
from typing import Self

from mod.ipr_asic.errors import APIError, AuthenticationError, FailedConnectionError
from mod.ipr_asic.protocol import (
    BaseClient,
    BaseHTTPClient,
    BaseRPCClient,
    BaseTCPClient,
)

from .models import MinerSnapshot, ProtocolResult

_COLLECTION_ERRORS = (
    FailedConnectionError,
    AuthenticationError,
    APIError,
    OSError,
    LookupError,
    NotImplementedError,
)


class BaseMiner:
    """A physical miner composed from all supported API transports.

    Protocols are queried independently so a failed or unavailable API does not
    discard data returned by another API. Concrete miner classes can override
    the collection hooks or normalize the raw snapshot into vendor-specific
    domain models later.
    """

    HTTP_COMMANDS = ("get_system_info", "get_miner_status")
    RPC_COMMANDS = ("version", "summary", "stats", "devs", "devdetails", "pools")

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{self.ip}]"

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        self.close()

    async def collect(self) -> MinerSnapshot:
        """Collect raw data from each configured protocol in parallel."""
        http_result, rpc_result = await asyncio.gather(
            self._collect_http(),
            self._collect_rpc(),
            return_exceptions=True,
        )
        return self._merge_results(http_result, rpc_result)

    async def _collect_http(self) -> ProtocolResult | None:
        if self.http is None:
            return None
        return await self._collect_commands(self.http, self.HTTP_COMMANDS)

    async def _collect_rpc(self) -> ProtocolResult | None:
        if self.rpc is None:
            return None
        return await self._collect_commands(self.rpc, self.RPC_COMMANDS)

    async def _collect_commands(
        self, client: BaseClient, commands: tuple[str, ...]
    ) -> ProtocolResult:
        """Collect commands sequentially while preserving partial results."""
        result = ProtocolResult()
        for command in commands:
            operation = getattr(client, command, None)
            if operation is None:
                result.errors[command] = NotImplementedError(
                    f"{client.__class__.__name__} does not implement {command}"
                )
                continue
            try:
                result.data[command] = await operation()
            except _COLLECTION_ERRORS as ex:
                result.errors[command] = ex
        return result

    def _merge_results(
        self,
        http_result: ProtocolResult | None | BaseException,
        rpc_result: ProtocolResult | None | BaseException,
    ) -> MinerSnapshot:
        """Build the raw snapshot; subclasses may override to normalize it."""
        return MinerSnapshot(
            ip=self.ip,
            http=self._coerce_result(http_result),
            rpc=self._coerce_result(rpc_result),
        )

    @staticmethod
    def _coerce_result(
        result: ProtocolResult | None | BaseException,
    ) -> ProtocolResult | None:
        if result is None or isinstance(result, ProtocolResult):
            return result
        if isinstance(result, Exception):
            return ProtocolResult(errors={"collect": result})
        raise result

    def close(self) -> None:
        """Close each configured transport once."""
        closed: set[int] = set()
        for client in (self.http, self.rpc, self.tcp):
            if client is not None and id(client) not in closed:
                client._close()
                closed.add(id(client))
