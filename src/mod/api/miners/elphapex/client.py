import requests
from string import Template

from mod.api import settings
from mod.api.http import BaseHTTPClient
from mod.api.errors import FailedConnectionError


class ElphapexHTTPClient(BaseHTTPClient):
    """Elphapex HTTP Client"""

    def __init__(self, ip_addr: str, passwd: str):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "root"
        self.passwds = [passwd, settings.get("default_elphapex_passwd")]
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

    def _authenticate_session(self) -> None:
        pass

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

    def get_mac_addr(self):
        net_info = self.run_command("GET", "get_network_info")
        if "macaddr" in net_info:
            return net_info["macaddr"]
        return ""

    def get_system_info(self) -> dict:
        return self.run_command("GET", "get_system_info")

    def blink(self, enabled: bool) -> None:
        self.run_command("POST", "blink", payload={"blink": enabled})
