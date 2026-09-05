# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Self

import httpx
from httpx import Auth, BasicAuth, DigestAuth

from mod.ipr_asic import settings
from mod.ipr_asic.errors import APIError, AuthenticationError, FailedConnectionError
from mod.ipr_asic.schemas.models import (
    APIObject,
    ContentResponse,
)

from .base import BaseClient

logger = logging.getLogger(__name__)


class BaseHTTPClient(BaseClient, ABC):
    """Base client for async HTTP APIs (httpx) for handling requests/commands."""

    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port)
        self.base_url: str = f"http://{self.ip}:{self.port}/"
        # format string for command path, use "{command}" placeholder
        self.command_path: str = "{command}"

        self.digest: Auth | DigestAuth | BasicAuth | None = None
        self.token: str | None = None
        self.cookies: str | None = None

        # optional injectable transport (e.g. httpx.MockTransport in tests)
        self._transport: httpx.AsyncBaseTransport | None = transport

    def __new__(
        cls,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> Self:
        if cls is BaseHTTPClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def _new_client(self, **kwargs: Any) -> httpx.AsyncClient:
        """Build an AsyncClient, injecting the shared transport/timeout.

        When a transport is injected (tests), it takes precedence over any
        ``verify`` option (httpx ignores verify when a transport is supplied).
        """
        kwargs.setdefault("timeout", settings.get("api_function_timeout", 5.0))
        if self._transport is not None:
            kwargs["transport"] = self._transport
            kwargs.pop("verify", None)
        return httpx.AsyncClient(**kwargs)

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
            timeout = settings.get("api_function_timeout", 5.0)
        async with self._new_client(verify=verify, timeout=timeout) as c:
            if self.token:
                c.headers.update({"Token": self.token})
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
    ) -> APIObject:
        if not self.authed:
            try:
                await self.authenticate()
            except (
                FailedConnectionError,
                AuthenticationError,
                httpx.RequestError,
            ) as ex:
                self.set_error(ex)
                raise
        headers: dict[str, str] = {}
        if self.cookies:
            headers.update({"Cookie": self.cookies})
        path = self.command_path.format(command=command)
        try:
            resp = await self._do_http(
                method=method,
                headers=headers,
                path=path,
                params=params,
                payload=payload,
                data=data,
            )
            _ = resp.raise_for_status()
            if resp.status_code == 200:
                try:
                    return resp.json()
                except json.JSONDecodeError:
                    content = resp.content.decode().strip("\n")
                    if content == "Socket connect failed: Connection refused":
                        raise APIError("API not available: connection refused")
                    return ContentResponse(text=content).model_dump()
        except httpx.HTTPError as ex:
            if isinstance(ex, (httpx.ConnectTimeout, httpx.ReadTimeout)):
                logger.error(
                    f"{self.__repr__()} : request {method} {self.base_url + path} timed out! {ex!s}"
                )
                return {}
            elif isinstance(ex, httpx.HTTPStatusError):
                logger.error(
                    f"{self.__repr__()} : request {method} {self.base_url + path} failed: {ex.response.status_code} {ex.response.reason_phrase}"
                )
            else:
                logger.error(
                    f"{self.__repr__()} : request {method} {self.base_url + path} failed! {ex!s}"
                )
            raise APIError("Failed to send command")
        logger.error(
            f"{self.__repr__()} : request {method} {self.base_url + path} failed! Unknown error occurred!"
        )
        raise APIError("Unknown error")

    @abstractmethod
    async def authenticate(self) -> None:
        pass
