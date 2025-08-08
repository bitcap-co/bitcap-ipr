import json
from string import Template
from typing import Any, Dict, List, Optional

import requests

from mod.api import settings
from mod.api.http import BaseHTTPClient


class DragonballHTTPClient(BaseHTTPClient):
    """Dragonball HTTP Client"""

    def __init__(self, ip_addr: str, passwd: Optional[str] = None, port: int = 16666):
        super().__init__(ip_addr, port)
        self.url = f"http://{self.ip}:{self.port}/"
        if passwd:
            self.passwds = [passwd, settings.get("default_dragonball_passwd")]
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
            resj = res.text
        return resj

    def get_mac_addr(self) -> str:
        return super().get_mac_addr()

    def get_system_info(self) -> dict:
        return self.run_command("GET", "get_system_info")

    def get_miner_conf(self) -> dict:
        conf = self.run_command("GET", "get_miner_info")
        return json.loads(conf)

    def get_blink_status(self) -> bool:
        return super().get_blink_status()

    def get_pools(self) -> dict:
        return super().get_pools()

    def blink(self, enabled: bool) -> None:
        return super().blink(enabled)

    def update_pools(self, urls: List[str], users: List[str], passwds: List[str]) -> None:
        return super().update_pools(urls, users, passwds)
