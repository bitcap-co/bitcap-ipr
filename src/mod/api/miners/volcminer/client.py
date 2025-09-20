import json
import logging
import re
from string import Template
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPDigestAuth

from mod.api import settings
from mod.api.errors import AuthenticationError
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
