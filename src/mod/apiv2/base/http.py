import logging
from abc import abstractmethod
from string import Template
from typing import Any, Self

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from mod.apiv2 import settings
from mod.apiv2.base import BaseClient
from mod.apiv2.errors import APIError, AuthenticationError, FailedConnectionError

logger = logging.getLogger(__name__)


class BaseHTTPClient(BaseClient):
    """Base client for HTTP APIs for handling requests/commands"""

    def __init__(self, ip: str, port: int = 80, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port)
        self.base_url = f"http://{self.ip}:{self.port}/"
        self.command_path: Template | None = None

        self.session: requests.Session = requests.Session()

        self.digest: HTTPDigestAuth | HTTPBasicAuth | None = None
        self.token: str | None = None

    def __new__(cls, *args, **kwargs) -> Self:
        if cls is BaseHTTPClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    @abstractmethod
    def authenticate(self) -> None:
        pass

    def _do_http(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: float = settings.get("http_request_timeout", 5.0),
        verify: bool = True,
    ) -> requests.Response:
        self.session.verify = verify
        if self.token:
            self.session.headers.update({"Authorization": "Bearer " + self.token})
        if headers:
            self.session.headers.update(headers)
        req = requests.Request(
            method=method,
            url=self.base_url + path,
            headers=self.session.headers,
            cookies=self.session.cookies,
        )
        if self.digest:
            req.auth = self.digest
        if params:
            req.params = params
        if payload:
            req.headers.update({"Content-Type": "application/json"})
            req.json = payload
        if data:
            req.headers.update(
                {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            req.data = data
        r = req.prepare()
        resp = self.session.send(r, timeout=timeout, verify=self.session.verify)
        return resp

    def send_command(
        self,
        method: str,
        command: str,
        params: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict:
        if not self.authed:
            try:
                self.authenticate()
            except (
                FailedConnectionError,
                AuthenticationError,
                requests.exceptions.RequestException,
                requests.exceptions.Timeout,
            ) as ex:
                self.session.close()
                self._ex = ex
                raise ex
        path = self.command_path.substitute(command=command)
        try:
            resp = self._do_http(
                method, path=path, params=params, payload=payload, data=data
            )
            resp.raise_for_status()
        except requests.HTTPError as ex:
            logger.error(
                f"{self.__repr__()} : request {ex.request.method} {ex.request.url} failed: {ex.response.status_code} {ex.response.reason}"
            )
            raise APIError("failed to send command")
        else:
            if resp.status_code == 200:
                try:
                    return resp.json()
                except requests.exceptions.JSONDecodeError:
                    return {"text": resp.text}
        logger.error(f"{self.__repr__()} : unknown error occurred.")
        raise APIError("failed to send command")

    @abstractmethod
    def get_hostname(self) -> str:
        """Get miner hostname from network configuration."""
        raise NotImplementedError

    @abstractmethod
    def get_mac_addr(self) -> str:
        """Get miner MAC address."""
        raise NotImplementedError

    @abstractmethod
    def get_api_version(self) -> str:
        """Get miner API version."""
        raise NotImplementedError

    @abstractmethod
    def get_system_info(self) -> dict:
        """Get miner system information."""
        raise NotImplementedError

    @abstractmethod
    def get_network_info(self) -> dict:
        """Get miner network information."""
        raise NotImplementedError

    @abstractmethod
    def log(self, *args, **kwargs) -> dict:
        """Get miner log."""
        raise NotImplementedError

    @abstractmethod
    def summary(self) -> dict:
        """Get miner status information."""
        raise NotImplementedError

    @abstractmethod
    def get_miner_conf(self) -> dict:
        """Get current miner configuration."""
        raise NotImplementedError

    @abstractmethod
    def set_miner_conf(self, *args, **kwargs) -> dict:
        """Set miner configuration."""
        raise NotImplementedError

    @abstractmethod
    def pools(self) -> list[dict]:
        """Get miner pool status information."""
        raise NotImplementedError

    @abstractmethod
    def get_pool_conf(self) -> list[dict]:
        """Get current miner pool configuration."""
        raise NotImplementedError

    @abstractmethod
    def get_miner_status(self) -> dict:
        """Get current miner status"""
        raise NotImplementedError

    @abstractmethod
    def get_blink_status(self) -> dict:
        """Get miner LED blink status."""
        raise NotImplementedError

    @abstractmethod
    def blink(self, enabled: bool, *args, **kwargs) -> dict:
        """Blink miner LEDS for locating."""
        raise NotImplementedError

    @abstractmethod
    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        """Update the current miner pool configuration."""
        raise NotImplementedError

    def _close(self, ex: Exception | None = None) -> None:
        if ex:
            self._ex = ex
        self.session.close()
