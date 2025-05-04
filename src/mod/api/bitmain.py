import re
import requests
from requests.auth import HTTPDigestAuth
from string import Template

from .http import BaseHTTPClient
from .parser import Parser
from .errors import (
    FailedConnectionError,
    AuthenticationError,
)


class BitmainHTTPClient(BaseHTTPClient):
    """Bitmain/Antminer HTTP Client with support for vnish"""

    def __init__(self, ip_addr: str, passwd: str):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "root"
        self.passwd = passwd
        self.command_format = {
            "vnish": "api/v1",
            "stock": Template("cgi-bin/${cmd}.cgi"),
        }

        self._initialize_session()

    def _initialize_session(self) -> None:
        self.session.headers = {"Content-Type": "application/json"}
        try:
            self.is_custom = self.__is_vnish()
            if not self.is_custom:
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
        passwds = [self.passwd, "root"] if self.passwd != "root" else [self.passwd]
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
        path = self.command_format["stock"].substitute(cmd=command)
        if self.is_custom:
            match command:
                case "get_system_info":
                    command = "/info"
                case "get_blink_status":
                    command = "/status"
                case "blink":
                    command = "/find-miner"
            path = self.command_format["vnish"] + command
        res = self._do_http(method=method, path=path, payload=payload)
        try:
            resj = res.json()
        except requests.exceptions.JSONDecodeError:
            resj = {"plaintext": res.text}
        return resj

    # Vnish support
    def __is_vnish(self) -> bool:
        res = self.session.head(self.url + self.command_format["vnish"], timeout=3.0)
        if res.status_code == 200:
            # change to vnish default passwd
            if self.passwd == "root":
                self.passwd = "admin"
            return True
        return False

    def unlock_vnish_session(self):
        passwds = [self.passwd, "admin"] if self.passwd != "admin" else [self.passwd]
        for passwd in passwds:
            payload = {"pw": passwd}
            res = self._do_http(
                method="POST",
                path=self.command_format["vnish"] + "/unlock",
                payload=payload,
            )
            try:
                resj = res.json()
            except requests.exceptions.JSONDecodeError:
                break
            if "token" in resj:
                self.session.headers.update({"Authorization": "Bearer " + resj["token"]})
                self.is_unlocked = True
                break
        if not self.is_unlocked:
            self._close_client(
                AuthenticationError(
                    "Authentication Failed: Failed to unlock vnish session."
                )
            )

    def get_bitmain_system_log(self) -> dict:
        resp = self.run_command("GET", "log")
        resp["plaintext"] = resp["plaintext"][0 : resp["plaintext"].find("===")]
        return resp

    def get_system_info(self) -> dict:
        return self.run_command("GET", "get_system_info")

    def get_blink_status(self) -> bool:
        resp = self.run_command("GET", "get_blink_status")
        if "find-miner" in resp:
            return resp["find-miner"]
        return resp["blink"]

    def blink(self, enabled: bool) -> None:
        if self.is_custom and not self.is_unlocked:
            self.unlock_vnish_session()
        if self.is_custom:
            self.run_command("POST", "blink")
        else:
            self.run_command("POST", "blink", {"blink": enabled})


class BitmainParser(Parser):
    def __init__(self, target: dict):
        super().__init__(target)
        self.target["algorithm"] = "sha256d"
        self.ctrl_boards = {
            "xil": r"Zynq|Xilinx|xil",
            "bb": r"BeagleBone",
            "aml": r"amlogic|aml",
            "cv": r"cvitek|CVITEK",
        }

    def parse_serial(self, obj: dict) -> None:
        for k in obj.keys():
            if k in ["serial", "serinum"]:
                self.target["serial"] = obj[k]
                break

    def parse_subtype(self, obj: dict) -> None:
        for k in obj.keys():
            if k in ["miner", "minertype"]:
                self.target["subtype"] = obj[k][9:]
                break

    def parse_algorithm(self, obj: dict):
        for k in obj.keys():
            if k in ["algorithm", "Algorithm"]:
                self.target["algorithm"] = obj[k]

    def parse_firmware(self, obj: dict):
        if "fw_name" in obj:
            self.target["firmware"] = f"{obj['fw_name']} {obj['fw_version']}"
        elif "system_filesystem_version" in obj:
            self.target["firmware"] = obj["system_filesystem_version"]

    def parse_platform(self, obj: dict):
        if "platform" in obj:
            self.target["platform"] = obj["platform"]
        elif "plaintext" in obj:
            for cb, pattern in self.ctrl_boards.items():
                if re.search(pattern, obj["plaintext"]):
                    self.target["platform"] = cb
                    break

    def parse_system_info(self, obj: dict):
        self.parse_algorithm(obj)
        self.parse_firmware(obj)
        self.parse_subtype(obj)
        self.parse_serial(obj)
