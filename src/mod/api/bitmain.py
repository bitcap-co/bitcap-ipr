import logging
import re
import requests
from requests.auth import HTTPDigestAuth
from string import Template

from .errors import (
    FailedConnectionError,
    AuthenticationError
)

logger = logging.getLogger(__name__)
HOST_URL = Template("http://${ip}/")


class BitmainClient():
    """Bitmain/Antminer HTTP API client with support for vnish"""
    def __init__(self, ip_addr: str, admin_passwd: str):
        self.ip_addr = ip_addr
        self.host = HOST_URL.substitute(ip=ip_addr)
        self.admin_passwd = admin_passwd
        self.digest = None
        self.is_custom = False
        self.unlocked = False
        self.command_prefixes = {
            "vnish": "api/v1",
            "stock": Template("cgi-bin/${cmd}.cgi")
        }
        self._initialize_session()

    def _is_vnish(self):
        res = self.session.head(self.host + self.command_prefixes["vnish"], timeout=3.0)
        if res.status_code == 200:
            if self.admin_passwd == "root":
                self.admin_passwd = "admin"
            return True
        return False

    def _authenticate_session(self):
        passwds = [self.admin_passwd]
        if self.admin_passwd != "root":
            passwds.append("root")
        for passwd in passwds:
            self.session.auth = HTTPDigestAuth("root", passwd)
            res = self.session.head(self.host, timeout=3.0)
            if res.status_code == 200:
                self.digest = self.session.auth
                break
        if not self.digest:
            self.close_client()
            raise AuthenticationError("Authentication failed: Failed to authenticate session.")

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
            requests.exceptions.ReadTimeout
        ):
            self.close_client()
            raise FailedConnectionError("Connection Failed: Failed to connect or timeout occurred.")

    def _do_http(self, method: str, path: str, payload: dict = None):
        req = requests.Request(
            method=method,
            url=self.host + path,
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
        except (
            requests.exceptions.JSONDecodeError,
            requests.exceptions.InvalidJSONError
        ):
            logger.warning("_do_http : expected json. return wrapped plaintext context")
            return {"plain": res.text}

    def unlock_vnish_session(self):
        passwds = [self.admin_passwd]
        if self.admin_passwd != "admin":
            passwds.append("admin")
        for passwd in passwds:
            payload = {"pw": passwd}
            res = self._do_http("POST", self.command_prefixes["vnish"] + "/unlock", payload)
            if "token" in res:
                self.session.headers.update({"Authorization": "Bearer" + res["token"]})
                self.unlocked = True
                break
        if not self.unlocked:
            self.close_client()
            raise AuthenticationError("Authentication Failed: Failed to unlock miner.")

    def run_command(self, method: str, command: str, payload: dict = None):
        path = self.command_prefixes["stock"].substitute(cmd=command)
        if self.is_custom:
            match command:
                case "get_system_info":
                    command = "/info"
                case "get_network_info":
                    command = "/info"
                case "stats":
                    command = "/summary"
                case "summary":
                    command = "/summary"
                case "get_miner_conf":
                    command = "/settings"
            path = self.command_prefixes["vnish"] + command
        return self._do_http(method, path, payload)

    def get_system_log(self):
        log = self.run_command("GET", "log")
        log["plain"] = log["plain"][0:log["plain"].find("===")]
        return log

    def close_client(self):
        self.session.close()
        self = None


class BitmainParser():
    def __init__(self, target: dict):
        self.target = target.copy()
        self.ctrl_boards = {
            "xil": r'Zynq|Xilinx|xil',
            "bb": r'BeagleBone',
            "aml": r'amlogic|aml',
            "cv": r'cvitek|CVITEK',
        }

    def get_target(self):
        return self.target

    def parse_common(self, resp: dict):
        for k in resp.keys():
            if k in ["serial", "serinum"]:
                self.target["serial"] = resp[k]
            if k in ["miner", "minertype"]:
                self.target["subtype"] = resp[k][9:]

    def parse_algorithm(self, resp: dict):
        if "Algorithm" in resp:
            self.target["algorithm"] = resp["Algorithm"]
        else:
            self.target["algorithm"] = "SHA256"

    def parse_firmware(self, resp: dict):
        if "fw_name" in resp:
            self.target["firmware"] = f"{resp['fw_name']} {resp['fw_version']}"
        elif "system_filesystem_version" in resp:
            self.target["firmware"] = resp["system_filesystem_version"]

    def parse_platform(self, resp: dict):
        if "platform" in resp:
            self.target["platform"] = resp["platform"]
        elif "plain" in resp:
            for cb, pattern in self.ctrl_boards.items():
                if re.search(pattern, resp["plain"]):
                    self.target["platform"] = cb
                    break
