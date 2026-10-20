# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import json
import re
from abc import ABC
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Self

from pydantic_core import from_json

from mod.ipr_asic.errors import APIError, APIInvalidResponse, FailedConnectionError
from mod.ipr_asic.schemas.models import (
    APIObject,
)
from mod.ipr_asic.settings import get as get_setting

from .base import BaseClient


class BaseRPCClient(BaseClient, ABC):
    """Base client for async JSON-RPC (CGMiner-family) APIs over TCP.

    Mirrors the synchronous apiv2 transport: a fresh connection is opened per
    command (no persistent socket). The JSON-repair heuristics in
    ``_load_api_data`` are ported verbatim.
    """

    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port)

        self._timeout: float = get_setting("rpc_blocking_timeout", 10.0)
        self.connected: bool = False

    def __new__(cls, ip: str, port: int = 4028, alt_pwd: str | None = None) -> Self:
        if cls is BaseRPCClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    @asynccontextmanager
    async def _rpc_connection(
        self, timeout: float | None = None
    ) -> AsyncGenerator[tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=self._timeout if timeout is None else timeout,
            )
        except (TimeoutError, OSError) as e:
            raise FailedConnectionError("Failed to connect or timeout occurred") from e

        self.connected = True
        try:
            yield reader, writer
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (OSError, TimeoutError):
                pass

    async def _do_rpc(self, command: str) -> APIObject:
        async with self._rpc_connection() as (reader, writer):
            writer.write(command.encode("utf-8"))
            await writer.drain()
            data = await asyncio.wait_for(
                self._recv_all(reader, 4000), timeout=self._timeout
            )
            if data is None:
                raise APIError("Failed to receive API response")

            if data == b"Socket connect failed: Connection refused\n":
                raise APIError("Connection Failed: connection refused.")

            return self._unmarshal_data(data)

    @staticmethod
    def _json_object_end(data: bytes | bytearray) -> int | None:
        depth = 0
        in_string = False
        escaped = False
        started = False

        for index, byte in enumerate(data):
            if not started:
                if chr(byte).isspace():
                    continue
                if byte != ord("{"):
                    raise APIInvalidResponse("Expected a JSON object")
                started = True

            if in_string:
                if escaped:
                    escaped = False
                elif byte == ord("\\"):
                    escaped = True
                elif byte == ord('"'):
                    in_string = False
                continue

            if byte == ord('"'):
                in_string = True
            elif byte == ord("{"):
                depth += 1
            elif byte == ord("}"):
                depth -= 1
                if depth == 0:
                    return index + 1

        return None

    async def _recv_json_object(
        self,
        reader: asyncio.StreamReader,
        timeout: float,
        max_size: int = 65536,
    ) -> tuple[APIObject, bytes]:
        response = bytearray()
        response_end: int | None = None

        while response_end is None:
            try:
                chunk = await asyncio.wait_for(reader.read(4096), timeout)
            except TimeoutError as e:
                raise FailedConnectionError("Timed out waiting for RPC response") from e
            if not chunk:
                raise APIInvalidResponse("Connection closed before RPC response")
            response.extend(chunk)
            if len(response) > max_size:
                raise APIInvalidResponse("RPC response header is too large")
            response_end = self._json_object_end(response)

        trailing = bytes(response[response_end:])
        if trailing.startswith(b"\x00"):
            trailing = trailing[1:]
        return self._unmarshal_data(bytes(response[:response_end])), trailing

    @staticmethod
    async def _recv_all(reader: asyncio.StreamReader, buf_size: int) -> bytes | None:
        data = b""
        while len(data) < buf_size:
            packet = await reader.read(buf_size - len(data))
            if not packet:
                if data:
                    return data
                return None
            data += packet
        return data

    @staticmethod
    def _unmarshal_data(raw: bytes) -> APIObject:
        # some json from the API returns with a null byte (\x00) on the end
        if raw.endswith(b"\x00"):
            data = raw.decode("utf-8", errors="replace")[:-1]
        else:
            data = raw.decode("utf-8", errors="replace")
        # fix an error with a btminer return having an extra comma that breaks json.loads()
        data = data.replace(",}", "}")
        # fix an error with a btminer return having a newline that breaks json.loads()
        data = data.replace("\n", "")
        # fix an error with a bmminer return not having a specific comma that breaks json.loads()
        data = data.replace("}{", "},{")
        # fix an error with a bmminer return having a specific comma that breaks json.loads()
        data = data.replace("[,{", "[{")
        # fix an error with a btminer return having a missing comma. (2023-01-06 version)
        data = data.replace('""temp0', '","temp0')

        # try to fix an error with overflowing the receive buffer
        # this can happen in cases such as bugged btminers returning arbitrary length error info with 100s of errors.
        if not data.endswith("}"):
            data = ",".join(data.split(",")[:-1]) + "}"

        # fix a really nasty bug with whatsminer API v2.0.4 where they return a list structured like a dict
        if re.search(r"\"error_code\":\[\".+\"\]", data):
            data = data.replace("[", "{").replace("]", "}")

        try:
            data_obj = from_json(data)
        except ValueError:
            raise APIError("Failed to unmarshal API response")
        return data_obj

    async def send_command(
        self, command: str, parameters: str | int | bool | None = None, **kwargs
    ) -> APIObject:
        cmd = {"command": command, **kwargs}
        if parameters:
            cmd["parameter"] = parameters
        return await self._do_rpc(json.dumps(cmd))

    async def send_privileged_command(self, *args, **kwargs) -> APIObject:
        return await self.send_command(*args, **kwargs)
