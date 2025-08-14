from string import Template
from typing import Any, Dict, List, Optional

import requests

from mod.api import settings
from mod.api.http import BaseHTTPClient
from mod.api.errors import APIError


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
        return self.run_command("GET", "get_miner_conf")

    def get_pool_conf(self) -> dict:
        conf = self.get_miner_conf()
        pool_conf = [conf["pool1"], conf["pool2"], conf["pool3"]]
        return pool_conf

    def get_pools(self) -> dict:
        return super().get_pools()

    def get_blink_status(self) -> bool:
        return super().get_blink_status()

    def blink(self, enabled: bool) -> None:
        return super().blink(enabled)

    def update_pools(
        self, urls: List[str], users: List[str], passwds: List[str]
    ) -> None:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            self._close_client(APIError("API Error: Invalid number of argurments."))

        conf = self.get_miner_conf()

        pool_conf = [
            conf["pool1"],
            conf["pool2"],
            conf["pool3"],
        ]

        data = {}
        for i in range(0, len(urls)):
            if not pool_conf[i] and not len(users[i]) and not len(passwds[i]):
                continue
            idx = i + 1
            data[f"_pool{idx}url"] = urls[i]
            data[f"_pool{idx}user"] = users[i]
            data[f"_pool{idx}pw"] = passwds[i]

        data["_nobeeper"] = "false"
        data["_notempoverctrl"] = "false"
        data["_fan_customize_switch"] = "false"
        data["_fan_customize_value"] = ""
        data["_freq"] = conf["frequency"]
        data["_freq1"] = conf["frequency1"]
        data["_freq2"] = conf["frequency2"]
        data["_freq3"] = conf["frequency3"]
        data["_freq4"] = conf["frequency4"]
        data["_usefrequencyAll"] = conf["usefrequencyAll"]
        data["position"] = conf["position"]
        data["fan1_speed"] = conf["fan1_speed"]
        data["fan2_speed"] = conf["fan2_speed"]
        data["temperature_threshould"] = conf["temperature_threshould"]
        data["mhs_threshould"] = conf["mhs_threshould"]
        self.run_command("POST", "set_miner_conf", data=data)
