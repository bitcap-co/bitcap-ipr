import random
import time
import requests
from abc import ABC, abstractmethod

import logging

logger = logging.getLogger(__name__)


class BaseHTTPClient(ABC):
    def __init__(self, ip: str) -> None:
        self.ip = ip
        self.port = 80
        self.url = ""
        self.username = None
        self.passwd = None

        self.auth = None
        self.bearer = None
        self.session = requests.Session()

        self.command_format = None

        self.is_custom = False
        self.is_unlocked = False

        self._error = None

        self.__max_retries = 3
        self.__max_delay = 5

    def __new__(cls, *args, **kwargs):
        if cls is BaseHTTPClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def __repr__(self):
        return f"{self.__class__.__name__}: {str(self.ip)}"

    def __delay_times(self, backoff_factor: int, jitter: bool = False):
        delay_times = []
        for retry in range(self.__max_retries):
            delay_time = backoff_factor * (2 ** (self.__max_retries - 1))
            if jitter:
                delay_time *= random.uniform(0.5, 1.5)
            effective_delay = min(delay_time, self.__max_delay)
            delay_times.append(effective_delay)
        return delay_times

    @abstractmethod
    def _initialize_session(self) -> None:
        pass

    @abstractmethod
    def _authenticate_session(self) -> None:
        pass

    def __retry_send(self, req: requests.PreparedRequest, **kwargs):
        success = False
        backoff = self.__delay_times(1, jitter=True)
        for delay in backoff:
            try:
                res = self.session.send(req, **kwargs)
                success = True
                return res
            except (
                requests.exceptions.ReadTimeout,
                requests.exceptions.ChunkedEncodingError
            ) as e:
                logger.warning(f" __retry_send : {e}. retry request in {delay} seconds.")
                time.sleep(delay)
        if not success:
            logger.error(" __retry_send : request failed after max retries.")
            return requests.Response()

    def _do_http(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        payload: dict | None = None,
        data: dict | None = None,
        timeout: float = 3.0,
    ) -> requests.Response:
        if self.bearer:
            self.session.headers.update({"Authorization": "Bearer " + self.bearer})
        req = requests.Request(
            method=method,
            url=self.url + path,
            headers=self.session.headers,
            cookies=self.session.cookies
        )
        if self.auth:
            req.auth = self.auth
        if params:
            req.params = params
        if payload:
            self.session.headers.update({"Content-Type": "application/json"})
            req.json = payload
        if data:
            self.session.headers.update({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
            req.data = data
        r = req.prepare()
        res = self.__retry_send(r, timeout=timeout, verify=self.session.verify)
        return res

    @abstractmethod
    def run_command(
        self,
        method: str,
        command: str,
        params: dict | None = None,
        payload: dict | None = None,
        data: dict | None = None,
    ):
        pass

    @abstractmethod
    def get_system_info(self) -> dict:
        pass

    @abstractmethod
    def blink(self, enabled: bool) -> None:
        pass

    def _close_client(self, error: Exception | None = None) -> None:
        self.session.close()
        if error:
            self._error = error
            raise error
