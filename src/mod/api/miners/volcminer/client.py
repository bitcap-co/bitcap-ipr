import requests
from requests.auth import HTTPDigestAuth
from string import Template

from ...http import BaseHTTPClient
from ...errors import FailedConnectionError, AuthenticationError


class VolcminerHTTPClient(BaseHTTPClient):
    """Volcminer HTTP Client"""

    def __init__(self, ip_addr: str, passwd: str):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "root"
        self.passwd = passwd
        self.command_format = Template("cgi-bin/${cmd}.cgi")

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
            [self.passwd, "ltc@dog"] if self.passwd != "ltc@dog" else [self.passwd]
        )
        for passwd in passwds:
            self.session.auth = HTTPDigestAuth(self.username, passwd)
            res = self.session.head(self.url, timeout=3.0)
            if res.status_code == 200:
                self.auth = self.session.auth
                break
        if not self.auth:
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
        res = self._do_http(method, path, data=data)
        try:
            resj = res.json()
        except requests.exceptions.JSONDecodeError:
            resj = {}
        return resj

    def get_system_info(self):
        return self.run_command("GET", "get_system_info")

    def blink(self, enabled: bool):
        data = {"_bb_type": "rgOn" if enabled else "rgOff"}
        self.run_command("POST", "post_led_onoff", data=data)
