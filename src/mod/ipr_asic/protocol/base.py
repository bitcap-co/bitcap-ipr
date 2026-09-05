# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from abc import ABC
from ipaddress import IPv4Address
from typing import Never, Self, override

from mod.ipr_asic.errors import UnsupportedOperationError
from mod.ipr_asic.schemas.models import APIObject


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

    def _unsupported(self, operation: str) -> Never:
        raise UnsupportedOperationError(
            f"Operation '{operation}' is not supported by {type(self).__name__}"
        )

    async def blink(self, enabled: bool) -> APIObject:
        self._unsupported("blink")

    async def start(self) -> APIObject:
        self._unsupported("start")

    async def stop(self) -> APIObject:
        self._unsupported("stop")

    async def restart(self) -> APIObject:
        self._unsupported("restart")

    async def reboot(self) -> APIObject:
        self._unsupported("reboot")

    async def update_passwd(
        self,
        old_passwd: str,
        new_passwd: str,
    ) -> APIObject:
        self._unsupported("password update")

    async def update_pool_conf(
        self,
        urls: list[str],
        users: list[str],
        passwds: list[str],
    ) -> APIObject:
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
