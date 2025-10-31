import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPDigestAuth
from requests.adapters import HTTPAdapter

from mod.api import settings
from mod.api.errors import FailedConnectionError

logger = logging.getLogger(__name__)


class BaseHTTPClient(ABC):
    def __init__(self, ip: str, port: int = 80) -> None:
        self.ip = ip
        self.port = port
        self.url = ""
        self.username: Optional[str] = None
        self.passwd: Optional[str] = None
        self.passwds: Optional[List[str]] = None
        self.auth: Optional[HTTPDigestAuth] = None
        self.bearer: Optional[str] = None
        self.session = requests.Session()
        self.session.mount("http://", HTTPAdapter(max_retries=0))

        self.is_custom = False
        self.is_unlocked = False

        self._error: Optional[Exception] = None

        self.__max_retries: int = settings.get("http_max_retries")
        self.__max_delay: int = settings.get("http_max_delay")
        self.__jitter: bool = settings.get("http_jitter_delay")

    def __new__(cls, *args, **kwargs):
        if cls is BaseHTTPClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def __repr__(self):
        return f"{self.__class__.__name__}: {str(self.ip)}"

    def __delay_times(self, base_delay: int, jitter: bool = False) -> List[float]:
        delay_times: List[float] = []
        for retry in range(self.__max_retries):
            delay_time = float(base_delay * (2**retry))
            if jitter:
                delay_time *= random.uniform(0.8, 1.2)
            effective_delay = min(delay_time, self.__max_delay)
            delay_times.append(effective_delay)
        return delay_times

    @abstractmethod
    def _initialize_session(self) -> None:
        try:
            self._authenticate_session()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
        ):
            self._close_client(
                FailedConnectionError(
                    "Connection Failed: Failed to connect or timeout occured."
                )
            )

    @abstractmethod
    def _authenticate_session(self) -> None:
        pass

    def __retry_send(self, req: requests.PreparedRequest, **kwargs):
        success = False
        backoff = self.__delay_times(1, jitter=self.__jitter)
        for delay in backoff:
            try:
                res = self.session.send(req, **kwargs)
                success = True
                return res
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
            ) as e:
                if not isinstance(e, requests.exceptions.ChunkedEncodingError):
                    logger.warning(f"__retry_send : {e}. Ignore..")
                    success = True
                    break
                else:
                    logger.warning(
                        f" __retry_send : {e}. retry request in {delay} seconds."
                    )
                    time.sleep(delay)
        if not success:
            logger.error(" __retry_send : request failed after max retries.")
        return requests.Response()

    def _do_http(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: float = settings.get("http_request_timeout"),
    ) -> requests.Response:
        if self.bearer:
            self.session.headers.update({"Authorization": "Bearer " + self.bearer})
        req = requests.Request(
            method=method,
            url=self.url + path,
            headers=self.session.headers,
            cookies=self.session.cookies,
        )
        if self.auth:
            req.auth = self.auth
        if params:
            req.params = params
        if payload:
            self.session.headers.update({"Content-Type": "application/json"})
            req.json = payload
        if data:
            self.session.headers.update(
                {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            )
            req.data = data
        r = req.prepare()
        res = self.__retry_send(r, timeout=timeout, verify=self.session.verify)
        return res

    @abstractmethod
    def run_command(
        self,
        method: str,
        command: str,
        params: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        pass

    @abstractmethod
    def get_mac_addr(self) -> str:
        pass

    @abstractmethod
    def get_system_info(self) -> dict:
        pass

    @abstractmethod
    def get_miner_conf(self) -> dict:
        pass

    @abstractmethod
    def get_pool_conf(self) -> dict:
        pass

    @abstractmethod
    def get_pools(self) -> dict:
        pass

    @abstractmethod
    def get_blink_status(self) -> bool:
        pass

    @abstractmethod
    def blink(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def update_pools(
        self, urls: List[str], users: List[str], passwds: List[str]
    ) -> None:
        pass

    def _close_client(self, error: Optional[Exception] = None) -> None:
        self.session.close()
        if error:
            self._error = error
            raise error
