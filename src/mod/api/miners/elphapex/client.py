from string import Template
from typing import Any, Dict, List, Optional

import requests

from mod.api import settings
from mod.api.http import BaseHTTPClient
from mod.api.errors import APIError


class ElphapexHTTPClient(BaseHTTPClient):
    """Elphapex HTTP Client"""

    def __init__(self, ip_addr: str, passwd: Optional[str] = None):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "root"
        if passwd:
            self.passwds = [passwd, settings.get("default_elphapex_passwd")]
        self.command_format = Template("cgi-bin/${cmd}.cgi")

        self._initialize_session()

    def _initialize_session(self) -> None:
        return super()._initialize_session()

    def _authenticate_session(self) -> None:
        res = self.session.head(self.url, timeout=3.0)
        if res.status_code == 200:
            return

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

    def get_miner_info(self) -> dict:
        return self.run_command("GET", "summary")

    def get_mac_addr(self) -> str:
        net_info = self.run_command("GET", "get_network_info")
        if "macaddr" in net_info:
            return net_info["macaddr"]
        return ""

    def get_system_info(self) -> dict:
        return self.run_command("GET", "get_system_info")

    def get_miner_conf(self) -> dict:
        return self.run_command("GET", "get_miner_conf")

    def get_pool_conf(self) -> dict:
        conf = self.get_miner_conf()
        return conf["pools"]

    def get_pools(self) -> dict:
        return self.run_command("GET", "pools")

    def get_blink_status(self) -> bool:
        return super().get_blink_status()

    def blink(self, enabled: bool) -> None:
        self.run_command("POST", "blink", payload={"blink": enabled})

    def update_pools(
        self, urls: List[str], users: List[str], passwds: List[str]
    ) -> None:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            self._close_client(APIError("API Error: Invalid number of argurments."))
        current_conf = self.get_miner_conf()

        new_conf = {**current_conf}
        pool_conf = new_conf["pools"]
        for i in range(0, len(urls)):
            if not pool_conf[i] and not len(users[i]) and not len(passwds[i]):
                continue
            pool_conf[i] = {"url": urls[i], "user": users[i], "pass": passwds[i]}

        res = self.run_command("POST", "set_miner_conf", payload=new_conf)
        if "msg" in res and res["msg"] != "OK!":
            self._close_client(APIError(res["msg"]))
