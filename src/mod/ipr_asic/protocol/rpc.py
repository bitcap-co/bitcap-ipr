# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import json
import re
from abc import abstractmethod
from typing import Self

from mod.ipr_asic import settings
from mod.ipr_asic.errors import APIError, FailedConnectionError
from mod.ipr_asic.protocol import BaseClient


class BaseRPCClient(BaseClient):
    """Base client for async JSON-RPC (CGMiner-family) APIs over TCP.

    Mirrors the synchronous apiv2 transport: a fresh connection is opened per
    command (no persistent socket). The JSON-repair heuristics in
    ``_load_api_data`` are ported verbatim.
    """

    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port)

        self._timeout = settings.get("rpc_blocking_timeout", 10.0)
        self.connected: bool = False

    def __new__(cls, *args, **kwargs) -> Self:
        if cls is BaseRPCClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    async def _do_rpc(self, command: str) -> dict:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port), timeout=self._timeout
            )
        except (asyncio.TimeoutError, OSError):
            raise FailedConnectionError("Failed to connect or timeout occurred")
        self.connected = True
        try:
            writer.write(command.encode("utf-8"))
            await writer.drain()
            data = await asyncio.wait_for(
                self._recv_all(reader, 4000), timeout=self._timeout
            )
            if data is None:
                raise APIError("Failed to receive API response")

            if data == b"Socket connect failed: Connection refused\n":
                raise APIError("Connection Failed: connection refused.")

            resp = self._load_api_data(data)
            return resp
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (OSError, asyncio.TimeoutError):
                pass

    def _load_api_data(self, data: bytes) -> dict:
        # some json from the API returns with a null byte (\x00) on the end
        if data.endswith(b"\x00"):
            str_data = data.decode("utf-8", errors="replace")[:-1]
        else:
            str_data = data.decode("utf-8", errors="replace")
        # fix an error with a btminer return having an extra comma that breaks json.loads()
        str_data = str_data.replace(",}", "}")
        # fix an error with a btminer return having a newline that breaks json.loads()
        str_data = str_data.replace("\n", "")
        # fix an error with a bmminer return not having a specific comma that breaks json.loads()
        str_data = str_data.replace("}{", "},{")
        # fix an error with a bmminer return having a specific comma that breaks json.loads()
        str_data = str_data.replace("[,{", "[{")
        # fix an error with a btminer return having a missing comma. (2023-01-06 version)
        str_data = str_data.replace('""temp0', '","temp0')

        # try to fix an error with overflowing the receive buffer
        # this can happen in cases such as bugged btminers returning arbitrary length error info with 100s of errors.
        if not str_data.endswith("}"):
            str_data = ",".join(str_data.split(",")[:-1]) + "}"

        # fix a really nasty bug with whatsminer API v2.0.4 where they return a list structured like a dict
        if re.search(r"\"error_code\":\[\".+\"\]", str_data):
            str_data = str_data.replace("[", "{").replace("]", "}")

        try:
            api_data = json.loads(str_data)
        except json.JSONDecodeError:
            raise APIError("Failed to decode JSON from API response")
        return api_data

    async def send_command(
        self, command: str, parameters: str | int | bool | None = None, **kwargs
    ) -> dict:
        cmd = {"command": command, **kwargs}
        if parameters:
            cmd["parameter"] = parameters
        return await self._do_rpc(json.dumps(cmd))

    async def send_privileged_command(self, *args, **kwargs) -> dict:
        return await self.send_command(*args, **kwargs)

    @abstractmethod
    async def version(self) -> dict:
        """Get miner version information."""
        raise NotImplementedError

    @abstractmethod
    async def summary(self) -> dict:
        """Get miner status information."""
        raise NotImplementedError

    @abstractmethod
    async def stats(self) -> list[dict]:
        """Get miner statistics."""
        raise NotImplementedError

    @abstractmethod
    async def devs(self) -> list[dict]:
        """Get miner device information."""
        raise NotImplementedError

    @abstractmethod
    async def devdetails(self) -> list[dict]:
        """Get miner device details."""
        raise NotImplementedError

    @abstractmethod
    async def pools(self) -> list[dict]:
        """Get miner pool status information."""
        raise NotImplementedError

    @abstractmethod
    async def get_system_info(self) -> dict:
        """Get miner system information."""
        raise NotImplementedError

    @abstractmethod
    async def get_pool_conf(self) -> list[dict]:
        """Get current miner pool configuration."""
        raise NotImplementedError

    @abstractmethod
    async def get_blink_status(self) -> dict:
        """Get miner LED blink status."""
        raise NotImplementedError

    @abstractmethod
    async def blink(self, enabled: bool, *args, **kwargs) -> dict:
        """Blink miner LEDS for locating."""
        raise NotImplementedError

    @abstractmethod
    async def set_miner_mode(self, *args, **kwargs) -> dict:
        """Set mining mode."""
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> dict:
        """Start mining."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> dict:
        """Stop mining."""
        raise NotImplementedError

    @abstractmethod
    async def restart(self) -> dict:
        """Restart mining."""
        raise NotImplementedError

    @abstractmethod
    async def reboot(self) -> dict:
        """Reboot miner."""
        raise NotImplementedError

    @abstractmethod
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        """Update the current miner pool configuration."""
        raise NotImplementedError

    @staticmethod
    async def _recv_all(reader: asyncio.StreamReader, buf_size: int) -> bytes | None:
        data = bytes()
        while len(data) < buf_size:
            packet = await reader.read(buf_size - len(data))
            if not packet:
                if data:
                    return data
                return None
            data += packet
        return data

    def _close(self, ex: Exception | None = None) -> None:
        if ex:
            self._ex = ex
