import requests
from abc import ABC, abstractmethod


class BaseHTTPClient(ABC):
    def __init__(self, ip: str) -> None:
        self.ip = ip
        self.port = 80
        self.url = None
        self.username = None
        self.passwd = None

        self.auth = None
        self.bearer = None
        self.session = requests.Session()

        self.command_format = None

        self.is_custom = False
        self.is_unlocked = False

        self._error = None

    def __new__(cls, *args, **kwargs):
        if cls is BaseHTTPClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def __repr__(self):
        return f"{self.__class__.__name__}: {str(self.ip)}"

    @abstractmethod
    def _initialize_session(self) -> None:
        pass

    @abstractmethod
    def _authenticate_session(self) -> None:
        pass

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
        res = self.session.send(r, timeout=timeout, verify=self.session.verify)
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

    def _close_client(self, error: Exception | None = None) -> None:
        self.session.close()
        if error:
            self._error = error
            raise error
