# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import json
import logging
import struct
from typing import Any, Self

from mod.ipr_asic import settings
from mod.ipr_asic.errors import APIError, APIInvalidResponse, FailedConnectionError
from mod.ipr_asic.protocol import BaseClient

logger = logging.getLogger(__name__)


class BaseTCPClient(BaseClient):
    """Base client for the async length-prefixed TCP API (Whatsminer V3).

    Unlike the synchronous apiv2 client (which connects in ``__init__``), the
    connection is established lazily via ``connect()`` on first use, since a
    coroutine cannot be awaited from ``__init__``.
    """

    def __init__(
        self,
        ip: str,
        port: int,
        username: str | None = None,
        alt_pwd: str | None = None,
    ) -> None:
        super().__init__(ip, port)

        self._timeout = settings.get("tcp_blocking_timeout", 10.0)
        self.connected: bool = False
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    def __new__(cls, *args, **kwargs) -> Self:
        if cls is BaseTCPClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    async def connect(self) -> bool:
        if not self.connected:
            try:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.ip, self.port), timeout=self._timeout
                )
            except (asyncio.TimeoutError, OSError):
                await self._aclose()
                raise FailedConnectionError("Failed to connect or timeout occurred")
            self.connected = True
        return self.connected

    # whatsminer v3 api methods
    async def btv3_send(self, msg: str, msg_len: int) -> dict[str, Any]:
        await self.connect()
        if self._reader is None or self._writer is None:
            return {}
        packed_size = struct.pack("<I", msg_len)
        self._writer.write(packed_size)
        self._writer.write(msg.encode())
        await self._writer.drain()
        data = await asyncio.wait_for(
            self._btv3_recv_all(self._reader), timeout=self._timeout
        )
        try:
            resp = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resp

    async def _btv3_recv_all(self, reader: asyncio.StreamReader) -> str:
        # get first 4 bytes for length
        try:
            packed_len = await reader.readexactly(4)
        except asyncio.IncompleteReadError:
            logger.error(
                f"{self.__repr__()} : {str(APIError('Failed to get response length'))}"
            )
            raise APIError("Invalid response length")

        msg_len = struct.unpack("<I", packed_len)[0]
        if msg_len > 8192:
            logger.error(
                f"{self.__repr__()} : {str(APIError(f'Invalid response length {msg_len}'))}"
            )
            raise APIError("Invalid response length")

        try:
            buffer = await reader.readexactly(msg_len)
        except asyncio.IncompleteReadError as e:
            buffer = e.partial
        return buffer.decode()

    async def _aclose(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (OSError, asyncio.TimeoutError):
                pass
        self._reader = None
        self._writer = None
        self.connected = False

    def _close(self, ex: Exception | None = None) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
            except OSError:
                pass
        self._reader = None
        self._writer = None
        self.connected = False
        if ex:
            self._ex = ex
