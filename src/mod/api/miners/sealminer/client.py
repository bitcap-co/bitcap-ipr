import requests
from string import Template

from ...http import BaseHTTPClient
from ...errors import (
    FailedConnectionError,
    AuthenticationError
)


class SealminerHTTPClient(BaseHTTPClient):
    """Bitdeer/Sealminer HTTP Client"""

    def __init__(self, ip_addr: str, passwd: str):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "seal"
        self.passwd = passwd
        self.command_format = Template("cgi-bin/${cmd}.php")

        self._initialize_session()

    def _initialize_session(self):
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

    def _authenticate_session(self):
        passwds = (
            [self.passwd, "seal"] if self.passwd != "seal" else [self.passwd]
        )
        for passwd in passwds:
            data = {
                "username": self.username,
                "origin_pwd": passwd
            }
            resj = self.run_command("POST", "login", data=data)

            if "state" in resj:
                if resj["state"] == 0:
                    self.is_unlocked = True
                    break
        if not self.is_unlocked:
            self._close_client(
                AuthenticationError(
                    "Authentication Failed: Failed to authenticate session."
                )
            )

    def run_command(
        self,
        method: str,
        command: str,
        params: dict | None = None,
        payload: dict | None = None,
        data: dict | None = None,
    ):
        path = self.command_format.substitute(cmd=command)
        res = self._do_http(method=method, path=path, params=params, data=data)
        try:
            resj = res.json()
        except requests.exceptions.JSONDecodeError:
            resj = {}
        return resj

    def get_system_info(self):
        return self.run_command("GET", "get_system_info")

    def get_blink_status(self) -> bool:
        sys = self.get_system_info()
        return True if sys["led"] == "on" else False

    def blink(self, enabled: bool):
        data = '{"key":"led","value": "%s"}' % ("on" if enabled else "off")
        self.run_command("POST", "led_conf", data=data)
