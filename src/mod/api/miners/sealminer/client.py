from string import Template
from typing import Any, Dict, List, Optional

import requests

from mod.api import settings
from mod.api.errors import APIError, AuthenticationError
from mod.api.http import BaseHTTPClient


class SealminerHTTPClient(BaseHTTPClient):
    """Bitdeer/Sealminer HTTP Client"""

    def __init__(self, ip_addr: str, passwd: Optional[str]):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "seal"
        self.passwds = [passwd, settings.get("default_sealminer_passwd")]
        self.command_format = Template("cgi-bin/${cmd}.php")

        self._initialize_session()

    def _initialize_session(self) -> None:
        return super()._initialize_session()

    def _authenticate_session(self):
        for passwd in self.passwds:
            if not passwd:
                continue
            data = {"username": self.username, "origin_pwd": passwd}
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
        params: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        path = self.command_format.substitute(cmd=command)
        res = self._do_http(method, path, params=params, payload=payload, data=data)
        try:
            resj = res.json()
        except requests.exceptions.JSONDecodeError:
            resj = {}
        return resj

    def get_mac_addr(self) -> str:
        return super().get_mac_addr()

    def get_system_info(self):
        return self.run_command("GET", "get_system_info")

    def get_miner_conf(self) -> dict:
        return self.run_command("GET", "get_miner_poolconf")

    def get_pool_conf(self) -> dict:
        return self.get_miner_conf()["pools"]

    def get_pools(self) -> dict:
        status = self.run_command("GET", "miner-status")
        return status["pools"]

    def get_blink_status(self) -> bool:
        sys = self.get_system_info()
        return True if sys["led"] == "on" else False

    def blink(self, enabled: bool):
        data = '{"key":"led","value": "%s"}' % ("on" if enabled else "off")
        self.run_command("POST", "led_conf", data=data)

    def update_pools(
        self, urls: List[str], users: List[str], passwds: List[str]
    ) -> None:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            self._close_client(APIError("API Error: Invalid number of argurments."))
        pool_conf = self.get_pool_conf()

        new_conf = {
            "poolurl1": "",
            "pooluser1": "",
            "poolpwd1": "",
            "poolurl2": "",
            "pooluser2": "",
            "poolpwd2": "",
            "poolurl3": "",
            "pooluser3": "",
            "poolpwd3": "",
        }
        for i in range(0, len(urls)):
            if not pool_conf[i] and not len(users[i]) and not len(passwds[i]):
                continue
            idx = i + 1
            new_conf[f"poolurl{idx}"] = urls[i]
            new_conf[f"pooluser{idx}"] = users[i]
            new_conf[f"poolpwd{idx}"] = passwds[i]

        self.run_command("POST", "set_miner_poolconf", payload=new_conf)
