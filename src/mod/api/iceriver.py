import logging
import requests
from string import Template

from .errors import (
    FailedConnectionError,
    MissingAPIKeyError,
)

logger = logging.getLogger(__name__)
HOST_URL = Template("${schema}://${ip}/")


class IceriverHTTPClient():
    """Iceriver HTTP Client with support for pbfarmer"""
    def __init__(self, ip_addr: str, pb_key: str):
        self.ip = ip_addr
        self.host = HOST_URL.substitute(schema="http", ip=self.ip)
        self.pb_key = pb_key
        self.is_custom = False
        self.command_prefix = {
            "pb": "api/",
            "stock": "user/"
        }
        self.err = None
        self._initialize_session()

    def _initialize_session(self):
        self.session = requests.Session()
        self.session.verify = False
        try:
            self.is_custom = self._is_pbfarmer()
            if not self.is_custom:
                self.session.head(self.host, timeout=5.0, verify=self.session.verify)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout
        ):
            self._close_client(FailedConnectionError("Connection Failed: Failed to connect to timeout occurred."))

    def _do_http(self, method: str, path: str, data: dict | None = None):
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
        if self.is_custom:
            if not self.pb_key:
                self._close_client(MissingAPIKeyError("Missing API Key: No pbfarmer API key found."))
            headers.update({"Authorization": "Bearer " + self.pb_key})
        req = requests.Request(
            method=method,
            url=self.host + path,
            headers=headers
        )
        if data:
            req.data = data
        r = req.prepare()
        res = self.session.send(r, timeout=10.0, verify=self.session.verify)
        return res.json()

    def run_command(self, method: str, command: str, data: dict | None = None):
        path = self.command_prefix["stock"] + command
        if self.is_custom:
            match command:
                case "ipconfig":
                    command = "network"
                case "userpanel":
                    command = "overview"
                case "locate":
                    command = "machine/locate"
            path = self.command_prefix["pb"] + command
        return self._do_http(method, path, data)

    # pbfarmer support
    def _is_pbfarmer(self):
        res = self.session.head(self.host + "api", timeout=5.0, verify=self.session.verify)
        if res.status_code == 301:
            self.host = HOST_URL.substitute(schema="https", ip=self.ip)
            return True
        return False

    def get_iceriver_mac_addr(self):
        data = {"post": 1}
        resp = self.run_command("POST", "ipconfig", data)
        for k in resp.keys():
            if k in ["data", "network"]:
                if "mac" in resp[k]:
                    return resp[k]["mac"]

    def get_system_info(self):
        data = {"post": 4}
        resp = self.run_command("POST", "userpanel", data)
        return resp["data"]

    def get_blink_status(self):
        resp = self.get_system_info()
        return resp["locate"]

    def blink(self, enabled: bool):
        if not self.is_custom:
            data = {
                "post": 5,
                "locate": "1" if enabled else "0"
            }
            self.run_command("POST", "userpanel", data)
        else:
            self.run_command("POST", "locate")

    def _close_client(self, error: Exception | None = None):
        self.session.close()
        if error:
            self.err = error
            raise error


class IceriverParser():
    def __init__(self, target: dict):
        self.target = target.copy()

    def get_target(self):
        return self.target

    def parse_subtype(self, obj: dict):
        if "model" in obj:
            if obj["model"] == "none":
                if "softver1" in obj:
                    model = "".join(obj["softver1"].split("_")[-2:])
                    self.target["subtype"] = model[model.rfind("ks"):model.rfind("miner")].upper()
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
