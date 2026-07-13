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
    def __init__(self, ip: str, port: int = 80, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port)
        self.base_url = f"http://{self.ip}:{self.port}/"
        self.command_path: Template | None = None

        self.digest: Auth | DigestAuth | BasicAuth | None = None
        self.token: str | None = None
        self.cookies: str | None = None

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
        timeout: int = settings.get("api_function_timeout", 5),
        verify: bool = True,
    ) -> httpx.Response:
        async with httpx.AsyncClient(verify=verify, timeout=timeout) as c:
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
        except httpx.RequestError as ex:
            if isinstance(ex, (httpx.ConnectTimeout, httpx.ReadTimeout)):
                logger.error(
                    f"{self.__repr__()} : request {method} {self.base_url + path} timed out! {str(ex)}"
                )
                return {}
            elif isinstance(ex, httpx.HTTPError):
                logger.error(
                    f"{self.__repr__()} : request {method} {self.base_url + path} failed: {ex.response.status_code} {ex.response.reason}"
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

    def _close(self, ex: Exception | None = None) -> None:
        if ex:
            self._ex = ex
            raise ex
