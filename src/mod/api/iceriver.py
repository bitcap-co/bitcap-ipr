import requests
from string import Template
from .errors import (
    FailedConnectionError,
    MissingAPIKeyError,
)

HOST_URL = Template("${schema}://${ip}/")


class IceriverClient():
    """Iceriver HTTP API client with support for pbfarmer"""
    def __init__(self, ip_addr: str, pb_key: str):
        self.ip_addr = ip_addr
        self.host = HOST_URL.substitute(schema="http", ip=ip_addr)
        self.pb_key = pb_key
        self.is_custom = False
        self.command_prefixes = {
            "pb": "api/",
            "stock": "user/"
        }
        self._initialize_session()

    def _is_pbfarmer(self):
        res = self.session.head(self.host + "api", timeout=5.0, verify=self.session.verify)
        if res.status_code == 301:
            self.host = HOST_URL.substitute(schema="https", ip=self.ip_addr)
            return True
        return False

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
            raise FailedConnectionError("Connection Failed: Failed to connect to timeout occurred.")

    def _do_http(self, method: str, path: str, payload: dict = None):
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}
        if self.is_custom:
            if not self.pb_key:
                self.close_client()
                raise MissingAPIKeyError("Missing API Key: No pbfarmer API key found.")
            headers.update({"Authorization": "Bearer " + self.pb_key})
        req = requests.Request(
            method=method,
            url=self.host + path,
            headers=headers
        )
        if payload:
            req.data = payload
        r = req.prepare()
        res = self.session.send(r, timeout=10.0, verify=self.session.verify)
        return res.json()

    def run_command(self, method: str, command: str, data: dict = None):
        path = self.command_prefixes["stock"] + command
        if self.is_custom:
            match command:
                case "ipconfig":
                    command = "network"
                case "userpanel":
                    command = "overview"
            path = self.command_prefixes["pb"] + command
        return self._do_http(method, path, data)

    def get_mac_address(self):
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

    def close_client(self):
        self.session.close()
        self = None


class IceriverParser():
    def __init__(self, target: dict):
        self.target = target.copy()

    def get_target(self):
        return self.target

    def parse_subtype(self, resp: dict):
        if "model" in resp:
            if resp["model"] == "none":
                if "softver1" in resp:
                    model = "".join(resp["softver1"].split("_")[-2:])
                    self.target["subtype"] = model[model.rfind("ks"):model.rfind("miner")].upper()
            else:
                self.target["subtype"] = resp["model"]

    def parse_algorithm(self, resp: dict):
        if "algo" in resp:
            if not resp["algo"] == "none":
                self.target["algorithm"] = resp["algo"]

    def parse_all(self, resp: dict):
        self.parse_subtype(resp)
        self.parse_algorithm(resp)
        return self.target
