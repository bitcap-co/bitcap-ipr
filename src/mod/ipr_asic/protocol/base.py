# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import re
from abc import ABC
from ipaddress import IPv4Address
from typing import Never, Self, override

from mod.ipr_asic.errors import UnsupportedOperationError
from mod.ipr_asic.schemas.models import APIObject, ContentResponse

_API_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


class BaseClient(ABC):
    def __init__(self, ip: str, port: int) -> None:
        self.ip: str = ip
        self.ip_addr: IPv4Address = IPv4Address(ip)
        self.port: int = port

        # authentication members
        self.authed: bool = False
        self.username: str = ""
        self.pwd: str | None = None
        self.passwds: list[str] = []

        # exception handling
        self._ex: Exception | None = None

    def __new__(cls, ip: str, port: int) -> Self:
        if cls is BaseClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{self.ip!s}]"

    @staticmethod
    def _parse_version(api_version: str = "") -> int:
        if not api_version:
            try:
                return int(api_version)
            except ValueError:
                return 0
        match = _API_VERSION_RE.match(api_version)
        if not match:
            return 0
        return int(match.group(1).replace(".", ""))

    def version_number(self, version_str: str) -> int:
        """Parses a version string as an integer."""
        return self._parse_version(version_str)

    async def hostname(self) -> str:
        """Returns the hostname of a miner."""
        return ""

    async def mac_address(self) -> str:
        """Returns the MAC address of a miner."""
        return ""

    def _unsupported(self, operation: str) -> Never:
        raise UnsupportedOperationError(
            f"Operation '{operation}' is not supported by {type(self).__name__}"
        )

    async def get_miner_log(self) -> ContentResponse:
        """Returns the current miner log from a miner."""
        self._unsupported("get_miner_log")

    async def get_log_list(self) -> list[str]:
        """Returns a list of available log files/archives from a miner."""
        self._unsupported("get_log_list")

    async def download_logs(self, log_list: list[str] | None = None) -> ContentResponse:
        """Downloads a log file/archive from a miner."""
        self._unsupported("download_logs")

    async def blink(self, enabled: bool) -> APIObject:
        """Locates a miner by blinking its LED."""
        self._unsupported("blink")

    async def start(self) -> APIObject:
        """Starts the miner."""
        self._unsupported("start")

    async def stop(self) -> APIObject:
        """Stops the miner."""
        self._unsupported("stop")

    async def restart(self) -> APIObject:
        """Restarts the miner."""
        self._unsupported("restart")

    async def reboot(self) -> APIObject:
        """Reboots the miner."""
        self._unsupported("reboot")

    async def reset_firmware(self) -> APIObject:
        """Resets the firmware to the default state."""
        self._unsupported("reset_firmware")

    async def rollback_firmware(self) -> APIObject:
        """Rolls back firmware to original stock firmware"""
        self._unsupported("rollback_firmware")

    async def update_firmware(
        self,
        firmware: bytes,
        filename: str,
        keep_settings: bool,
    ) -> APIObject:
        """Updates the firmware image of a miner. keep_settings is passed to keep the current configuration after update (if supported)."""
        self._unsupported("update_firmware")

    async def update_passwd(
        self,
        old_passwd: str,
        new_passwd: str,
    ) -> APIObject:
        """Updates the login password of a miner."""
        self._unsupported("password update")

    async def update_pool_conf(
        self,
        urls: list[str],
        users: list[str],
        passwds: list[str],
    ) -> APIObject:
        """Updates the pool configuration of a miner."""
        self._unsupported("pool configuration update")

    def error(self) -> Exception | None:
        """Return the last exception that occurred."""
        return self._ex

    def set_error(self, ex: Exception) -> None:
        """Set the last exception that occurred."""
        self._ex = ex

    def close(self, ex: Exception | None = None) -> None:
        """Close the client, optionally setting an exception."""
        if ex:
            self._ex = ex
