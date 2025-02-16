import logging
import re
import requests
from requests.auth import HTTPDigestAuth
from string import Template

from .errors import (
    FailedConnectionError,
    AuthenticationError,
)

logger = logging.getLogger(__name__)
HOST_URL = Template("http://${ip}/")


class BitmainHTTPClient:
    """Bitmain/Antminer HTTP Client with support for vnish"""

    def __init__(self, ip_addr: str, passwd: str):
        self.ip = ip_addr
        self.url = HOST_URL.substitute(ip=self.ip)
        self.passwd = passwd
        self.digest = None
        self.is_custom = False
        self.is_unlocked = False
        self.command_prefix = {
            "vnish": "api/v1",
            "stock": Template("cgi-bin/${cmd}.cgi"),
        }
        self.err = None
        self._initialize_session()

    def _initialize_session(self):
        self.session = requests.Session()
        self.session.headers = {"Content-Type": "application/json"}
        try:
            self.is_custom = self._is_vnish()
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

    def _authenticate_session(self):
        passwds = [self.passwd, "root"] if self.passwd != "root" else [self.passwd]
        for passwd in passwds:
            self.session.auth = HTTPDigestAuth("root", passwd)
            res = self.session.head(self.url, timeout=3.0)
            if res.status_code == 200:
                self.digest = self.session.auth
                break
        if not self.digest:
            self._close_client(
                AuthenticationError(
                    "Authentication Failed: Failed to authenticate session."
                )
            )

    def _do_http(self, method: str, path: str, payload: dict | None = None):
        req = requests.Request(
            method=method,
            url=self.url + path,
            headers=self.session.headers
        )
        if self.digest:
            req.auth = self.digest
        if payload:
            req.json = payload
        r = req.prepare()
        res = self.session.send(r)
        try:
            return res.json()
        except requests.exceptions.JSONDecodeError:
            logger.warning("_do_http : return wrapped plaintext content.")
            return {"plaintext": res.text}

    def run_command(self, method: str, command: str, payload: dict | None = None):
        path = self.command_prefix["stock"].substitute(cmd=command)
        if self.is_custom:
            match command:
                case "get_system_info":
                    command = "/info"
                case "get_blink_status":
                    command = "/status"
                case "blink":
                    command = "/find-miner"
            path = self.command_prefix["vnish"] + command
        return self._do_http(method, path, payload)

    # Vnish support
    def _is_vnish(self) -> bool:
        res = self.session.head(self.url + self.command_prefix["vnish"], timeout=3.0)
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
                "POST", self.command_prefix["vnish"] + "/unlock", payload
            )
            if "token" in res:
                self.session.headers.update({"Authorization": "Bearer " + res["token"]})
                self.is_unlocked = True
                break
        if not self.is_unlocked:
            self._close_client(
                AuthenticationError(
                    "Authentication Failed: Failed to unlock vnish session."
                )
            )

    def get_bitmain_system_log(self):
        resp = self.run_command("GET", "log")
        resp["plaintext"] = resp["plaintext"][0 : resp["plaintext"].find("===")]
        return resp

    def get_system_info(self):
        return self.run_command("GET", "get_system_info")

    def get_blink_status(self):
        resp = self.run_command("GET", "get_blink_status")
        if "find-miner" in resp:
            return resp["find-miner"]
        return resp["blink"]

    def blink(self, enabled: bool):
        if self.is_custom and not self.is_unlocked:
            self.unlock_vnish_session()
        if self.is_custom:
            self.run_command("POST", "blink")
        else:
            self.run_command("POST", "blink", {"blink": enabled})

    def _close_client(self, error: Exception | None = None):
        self.session.close()
        if error:
            self.err = error
            raise error


class BitmainParser:
    def __init__(self, target: dict):
        self.target = target.copy()
        self.ctrl_boards = {
            "xil": r"Zynq|Xilinx|xil",
            "bb": r"BeagleBone",
            "aml": r"amlogic|aml",
            "cv": r"cvitek|CVITEK",
        }

    def get_target(self):
        return self.target

    def parse_common(self, obj: dict):
        for k in obj.keys():
            if k in ["serial", "serinum"]:
                self.target["serial"] = obj[k]
            if k in ["miner", "minertype"]:
                self.target["subtype"] = obj[k][9:]

    def parse_algorithm(self, obj: dict):
        if "Algorithm" in obj:
            self.target["algorithm"] = obj["Algorithm"]
        else:
            self.target["algorithm"] = "SHA256"

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
