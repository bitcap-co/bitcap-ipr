import json
import logging
import re
from string import Template
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPDigestAuth

from mod.api import settings
from mod.api.errors import APIError, AuthenticationError
from mod.api.http import BaseHTTPClient

logger = logging.getLogger(__name__)


class VolcminerHTTPClient(BaseHTTPClient):
    """Volcminer HTTP Client"""

    def __init__(self, ip_addr: str, passwd: Optional[str]):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "root"
        self.passwds = [passwd, settings.get("default_volcminer_passwd")]
        self.command_format = Template("cgi-bin/${cmd}.cgi")

        self._initialize_session()

    def _initialize_session(self) -> None:
        return super()._initialize_session()

    def _authenticate_session(self) -> None:
        for passwd in self.passwds:
            if not passwd:
                continue
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
        conf = self.run_command("GET", "get_miner_confV1")
        cleaned_conf = re.sub(r"\s{4,}", "", conf)
        parts = re.search(r'"{ "cfgs": "\[(.*?)\]",.*?, "debug": "{(.*?)}",(.*?)}"', cleaned_conf)

        miner_conf = json.loads(parts.group(1))
        debug_conf = json.loads("{" + parts.group(2) + "}")
        config_conf = json.loads("{" + parts.group(3) + "}")

        conf = {
            **miner_conf,
            "keeppower": "0",
            **debug_conf,
            **config_conf
        }
        return conf

    def get_pool_conf(self) -> dict:
        conf = self.get_miner_conf()
        return conf["pools"]

    def get_pools(self) -> dict:
        status = self.run_command("GET", "get_miner_statusV1")
        cleaned_status = re.sub(r"\s{4,}", "", status)
        pool_data = re.search(r'"pool_dtls": "\[(.*?)\]"', cleaned_status).group(1)
        return json.loads("[" + pool_data + "]")

    def get_blink_status(self) -> bool:
        return super().get_blink_status()

    def blink(self, enabled: bool) -> None:
        data = {"_bb_type": "rgOn" if enabled else "rgOff"}
        self.run_command("POST", "post_led_onoff", data=data)

    def update_pools(self, urls: List[str], users: List[str], passwds: List[str]) -> None:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            self._close_client(APIError("API Error: Invalid number of argurments."))

        conf = self.get_miner_conf()

        new_conf = {**conf}
        pool_conf = new_conf["pools"]

        data = {}
        for i in range(0, len(urls)):
            if not pool_conf[i] and not len(users[i]) and not len(passwds[i]):
                continue
            idx = i + 1
            data[f"_bb_pool{idx}url"] = urls[i]
            data[f"_bb_pool{idx}user"] = users[i]
            data[f"_bb_pool{idx}pw"] = passwds[i]

        data["_bb_nobeeper"] = ""
        data["_bb_notempoverctrl"] = "false"
        if new_conf["fan-ctrl"]:
            data["_bb_fan_customize_switch"] =  "true"
            data["_bb_fan_customize_value_front"] = new_conf["fan-pwm-front"]
            data["_bb_fan_customize_value_back"] = new_conf["fan-pwm-back"]
        else:
            data["_bb_fan_customize_switch"] =  "false"
            data["_bb_fan_customize_value_front"] = ""
            data["_bb_fan_customize_value_back"] = ""

        data["_bb_fan_customize_value_back"] = ""
        data["_bb_freq"] = new_conf["freq"]
        data["_bb_coin_type"] = new_conf["coin_type"]
        data["_bb_runmode"] = new_conf["runmode"]
        data["_bb_voltage_customize_value"] = new_conf["voltage"]
        data["_bb_ema"] = new_conf["sram-voltage"]
        data["_bb_debug"] = "false"
        self.run_command("POST", "set_miner_conf", data=data)
