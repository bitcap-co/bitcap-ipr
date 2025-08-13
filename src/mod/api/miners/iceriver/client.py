import logging
from string import Template
from typing import Any, Dict, List, Optional

import requests

from mod.api import settings
from mod.api.errors import (
    APIError,
    FailedConnectionError,
)
from mod.api.http import BaseHTTPClient

logger = logging.getLogger(__name__)


class IceriverHTTPClient(BaseHTTPClient):
    """Iceriver HTTP Client with support for pbfarmer"""

    def __init__(
        self, ip_addr: str, passwd: Optional[str] = None, pb_key: Optional[str] = None
    ):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        if passwd:
            self.passwds: List[str] = [passwd, settings.get("default_iceriver_passwd")]
        self.bearer: str = settings.get("default_pbfarmer_auth")
        if pb_key:
            self.bearer = pb_key
        self.command_format = {
            "pb": Template("api/${cmd}"),
            "stock": Template("user/${cmd}"),
        }

        self._initialize_session()

    def _initialize_session(self) -> None:
        self.session.verify = False
        try:
            self.is_custom = self.__is_pbfarmer()
            if not self.is_custom:
                self.session.head(self.url, timeout=5.0, verify=self.session.verify)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
        ):
            self._close_client(
                FailedConnectionError(
                    "Connection Failed: Failed to connect to timeout occurred."
                )
            )

    def _authenticate_session(self) -> None:
        return super()._authenticate_session()

    def run_command(
        self,
        method: str,
        command: str,
        params: Optional[Dict[str, str]] = None,
        payload: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        path = self.command_format["stock"].substitute(cmd=command)
        if self.is_custom:
            match command:
                case "ipconfig":
                    command = "network"
                case "machineconfig":
                    command = "machine"
                case "userpanel":
                    command = "overview"
                case "locate":
                    command = "machine/locate"
            path = self.command_format["pb"].substitute(cmd=command)
        res = self._do_http(
            method, path, params=params, payload=payload, data=data, timeout=10.0
        )
        try:
            resj = res.json()
        except requests.exceptions.JSONDecodeError:
            resj = {}
        return resj

    # pbfarmer support
    def __is_pbfarmer(self):
        res = self.session.head(
            self.url + "api", timeout=5.0, verify=self.session.verify
        )
        if res.status_code == 301:
            self.url = f"https://{self.ip}:{self.port}/"
            return True
        return False

    def get_mac_addr(self) -> str:
        data = {"post": 1}
        resp = self.run_command("POST", "ipconfig", data=data)
        for k in resp.keys():
            if k in ["data", "network"]:
                if "mac" in resp[k]:
                    return resp[k]["mac"]
        return ""

    def get_system_info(self) -> dict:
        data = {"post": 4}
        resp = self.run_command("POST", "userpanel", data=data)
        return resp["data"]

    def get_miner_conf(self) -> dict:
        data = {"post": 1}
        resp = self.run_command("POST", "machineconfig", data=data)
        return resp["data"]

    def get_pool_conf(self) -> dict:
        conf = self.get_miner_conf()
        return conf["pools"]

    def get_pools(self) -> dict:
        data = self.get_system_info()
        return data["pools"]

    def get_blink_status(self) -> bool:
        resp = self.get_system_info()
        return resp["locate"]

    def blink(self, enabled: bool) -> None:
        if not self.is_custom:
            data = {"post": 5, "locate": "1" if enabled else "0"}
            self.run_command("POST", "userpanel", data=data)
        else:
            self.run_command("POST", "locate")

    def update_pools(
        self, urls: List[str], users: List[str], passwds: List[str]
    ) -> None:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            self._close_client(APIError("API Error: Invalid number of argurments."))
        conf = self.get_miner_conf()

        new_conf = {**conf}
        if not self.is_custom:
            data = {"post": 2}
            data["fanratio"] = f"{new_conf['ratio']}"
            match new_conf["mode"]:
                case 0:
                    data["fanmode"] = "sleep"
                case 1:
                    data["fanmode"] = "normal"

            for i in range(0, len(urls)):
                if (
                    not new_conf["pools"][i]
                    and not len(users[i])
                    and not len(passwds[i])
                ):
                    continue
                idx = i + 1
                data[f"pool{idx}address"] = urls[i]
                data[f"pool{idx}miner"] = users[i]
                data[f"pool{idx}pwd"] = passwds[i]
            self.run_command("POST", "machineconfig", data=data)
        else:
            for i in range(0, len(urls)):
                data = {
                    "id": f"{i + 1}",
                    "pool_address": f"{urls[i]}",
                    "wallet": f"{users[i]}",
                    "pool_password": f"{passwds[i]}",
                }
                self.run_command("POST", "/pool/update", data=data)
