import requests
from string import Template

from .http import BaseHTTPClient
from .parser import Parser
from .errors import (
    FailedConnectionError,
)


class IceriverHTTPClient(BaseHTTPClient):
    """Iceriver HTTP Client with support for pbfarmer"""

    def __init__(self, ip_addr: str, pb_key: str):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
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
        pass

    def run_command(
        self,
        method: str,
        command: str,
        params: dict | None = None,
        payload: dict | None = None,
        data: dict | None = None,
    ):
        path = self.command_format["stock"].substitute(cmd=command)
        if self.is_custom:
            match command:
                case "ipconfig":
                    command = "network"
                case "userpanel":
                    command = "overview"
                case "locate":
                    command = "machine/locate"
            path = self.command_format["pb"].substitute(cmd=command)
        res = self._do_http(method=method, path=path, data=data, timeout=10.0)
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

    def get_mac_addr(self):
        data = {"post": 1}
        resp = self.run_command("POST", "ipconfig", data=data)
        for k in resp.keys():
            if k in ["data", "network"]:
                if "mac" in resp[k]:
                    return resp[k]["mac"]
        return ""

    def get_system_info(self):
        data = {"post": 4}
        resp = self.run_command("POST", "userpanel", data=data)
        return resp["data"]

    def get_blink_status(self):
        resp = self.get_system_info()
        return resp["locate"]

    def blink(self, enabled: bool):
        if not self.is_custom:
            data = {"post": 5, "locate": "1" if enabled else "0"}
            self.run_command("POST", "userpanel", data=data)
        else:
            self.run_command("POST", "locate")


class IceriverParser(Parser):
    def parse_subtype(self, obj: dict):
        if "model" in obj:
            if obj["model"] == "none":
                if "softver1" in obj:
                    model = "".join(obj["softver1"].split("_")[-2:])
                    self.target["subtype"] = model[
                        model.rfind("ks") : model.rfind("miner")
                    ].upper()
            else:
                self.target["subtype"] = obj["model"]

    def parse_algorithm(self, obj: dict):
        if "algo" in obj:
            if not obj["algo"] == "none":
                self.target["algorithm"] = obj["algo"]

    def parse_firmware(self, obj: dict):
        if "softver1" in obj:
            self.target["firmware"] = obj["softver1"]

    def parse_all(self, obj: dict):
        self.parse_subtype(obj)
        self.parse_algorithm(obj)
        self.parse_firmware(obj)
        return self.target
