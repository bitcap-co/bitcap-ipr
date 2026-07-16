# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import logging
from abc import abstractmethod
from string import Template
from typing import Any

import httpx
from httpx import Auth, BasicAuth, DigestAuth

from mod.ipr_asic import settings
from mod.ipr_asic.errors import APIError, AuthenticationError, FailedConnectionError
from mod.ipr_asic.protocol import BaseClient

logger = logging.getLogger(__name__)


class BaseHTTPClient(BaseClient):
    """Base client for async HTTP APIs (httpx) for handling requests/commands."""

    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port)
        self.base_url = f"http://{self.ip}:{self.port}/"
        self.command_path: Template | None = None

        self.digest: Auth | DigestAuth | BasicAuth | None = None
        self.token: str | None = None
        self.cookies: str | None = None

        # optional injectable transport (e.g. httpx.MockTransport in tests)
        self._transport = transport

    def _new_client(self, **kwargs: Any) -> httpx.AsyncClient:
        """Build an AsyncClient, injecting the shared transport/timeout.

        When a transport is injected (tests), it takes precedence over any
        ``verify`` option (httpx ignores verify when a transport is supplied).
        """
        kwargs.setdefault("timeout", settings.get("api_function_timeout", 5))
        if self._transport is not None:
            kwargs["transport"] = self._transport
            kwargs.pop("verify", None)
        return httpx.AsyncClient(**kwargs)

    @abstractmethod
    async def authenticate(self) -> None:
        pass

    async def _do_http(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: float | None = None,
        verify: bool = True,
    ) -> httpx.Response:
        if timeout is None:
            timeout = settings.get("api_function_timeout", 5)
        async with self._new_client(verify=verify, timeout=timeout) as c:
            if self.token:
                c.headers.update({"Authorization": "Bearer " + self.token})
            if self.digest:
                c.auth = self.digest
            if payload:
                c.headers.update({"Content-Type": "application/json"})
            if data:
                c.headers.update(
                    {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
                )
            if headers:
                c.headers.update(headers)
            req = httpx.Request(
                method=method,
                url=self.base_url + path,
                headers=c.headers,
                params=params,
                json=payload,
                data=data,
            )
            resp = await c.send(req)
            return resp

    async def send_command(
        self,
        method: str,
        command: str,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict:
        if not self.authed:
            try:
                await self.authenticate()
            except (
                FailedConnectionError,
                AuthenticationError,
                httpx.RequestError,
            ) as ex:
                self._ex = ex
                raise ex
        headers = {}
        if self.cookies:
            headers.update({"Cookie": self.cookies})
        path = self.command_path.substitute(command=command)
        try:
            resp = await self._do_http(
                method=method,
                headers=headers,
                path=path,
                params=params,
                payload=payload,
                data=data,
            )
            resp.raise_for_status()
        except httpx.HTTPError as ex:
            if isinstance(ex, (httpx.ConnectTimeout, httpx.ReadTimeout)):
                logger.error(
                    f"{self.__repr__()} : request {method} {self.base_url + path} timed out! {str(ex)}"
                )
                return {}
            elif isinstance(ex, httpx.HTTPStatusError):
                logger.error(
                    f"{self.__repr__()} : request {method} {self.base_url + path} failed: {ex.response.status_code} {ex.response.reason_phrase}"
                )
            else:
                logger.error(
                    f"{self.__repr__()} : request {method} {self.base_url + path} failed! {str(ex)}"
                )
            raise APIError("Failed to send command")
        else:
            if resp.status_code == 200:
                try:
                    return resp.json()
                except json.JSONDecodeError:
                    return {"text": resp.content.decode()}
        logger.error(
            f"{self.__repr__()} : request {method} {self.base_url + path} failed! Unknown error occurred!"
        )
        raise APIError("Unknown error")

    @abstractmethod
    async def get_hostname(self) -> str:
        """Get miner hostname from network configuration."""
        raise NotImplementedError

    @abstractmethod
    async def get_mac_addr(self) -> str:
        """Get miner MAC address."""
        raise NotImplementedError

    @abstractmethod
    async def get_api_version(self) -> str:
        """Get miner API version."""
        raise NotImplementedError

    @abstractmethod
    async def get_system_info(self) -> dict:
        """Get miner system information."""
        raise NotImplementedError

    @abstractmethod
    async def get_network_info(self) -> dict:
        """Get miner network information."""
        raise NotImplementedError

    @abstractmethod
    async def log(self, *args, **kwargs) -> dict:
        """Get miner log."""
        raise NotImplementedError

    @abstractmethod
    async def summary(self) -> dict:
        """Get miner status information."""
        raise NotImplementedError

    @abstractmethod
    async def get_miner_conf(self) -> dict:
        """Get current miner configuration."""
        raise NotImplementedError

    @abstractmethod
    async def set_miner_conf(self, *args, **kwargs) -> dict:
        """Set miner configuration."""
        raise NotImplementedError

    @abstractmethod
    async def pools(self) -> list[dict]:
        """Get miner pool status information."""
        raise NotImplementedError

    @abstractmethod
    async def get_pool_conf(self) -> list[dict]:
        """Get current miner pool configuration."""
        raise NotImplementedError

    @abstractmethod
    async def get_miner_status(self) -> dict:
        """Get current miner status"""
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

    def _close(self, ex: Exception | None = None) -> None:
        if ex:
            self._ex = ex
            raise ex
