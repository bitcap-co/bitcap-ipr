import logging
import requests
from string import Template

from .parser import Parser
from .errors import (
    FailedConnectionError,
    AuthenticationError,
)


class GoldshellHTTPClient:
    """Goldshell miner HTTP Client"""

    def __init__(self, ip_addr: str, passwd: str):
        self.ip = ip_addr
        self.host = f"http://{self.ip}/"
        self.passwd = passwd
        self.token = None
        self.command_format = Template("/mcb/${cmd}")
        self.err = None

        self.__initialize_session()

    def __initialize_session(self):
        self.session = requests.Session()
        self.session.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
        }
        try:
            self.__authenticate_session()
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

    def __do_http(self, method: str, path: str, query: dict | None = None, payload: dict | None = None):
        if self.token:
            self.session.headers.update({"Authorization": "Bearer " + self.token})
        req = requests.Request(
            method=method, url=self.host + path, headers=self.session.headers
        )
        if query:
            req.params = query
        if payload:
            req.json = payload
        r = req.prepare()
        res = self.session.send(r, timeout=3.0)
        try:
            return res.json()
        except requests.exceptions.JSONDecodeError:
            return res.status_code

    def __authenticate_session(self):
        self.__do_http("GET", "/user/logout")
        passwds = [self.passwd, "123456789"] if self.passwd != "123456789" else [self.passwd]
        for pw in passwds:
            query = {
                "username": "admin",
                "password": pw,
                "cipher": "false"
            }
            res = self.__do_http("GET", "/user/login", query)
            if res and res["JWT Token"]:
                self.token = res["JWT Token"]
                break
        if not self.token:
            self._close_client(
                AuthenticationError(
                    "Authentication Failed: Failed to authenticate session"
                )
            )

    def run_command(self, method: str, command: str, params: dict | None = None, payload: dict | None = None):
        path = self.command_format.substitute(cmd=command)
        return self.__do_http(method, path, params, payload)

    def get_status(self):
        return self.run_command("GET", "status")

    def get_settings(self):
        return self.run_command("GET", "setting")

    def get_algo_settings(self):
        return self.run_command("GET", "algosetting")

    def get_blink_status(self):
        settings = self.get_settings()
        return settings["ledcontrol"]

    def blink(self, enabled: bool):
        settings = self.get_settings()
        settings["ledcontrol"] = f"{enabled}"
        self.__do_http("PUT", "setting", payload=settings)

    def _close_client(self, error: Exception | None = None):
        self.session.close()
        if error:
            self.err = error
            raise error


class GoldshellParser(Parser):
    def parse_subtype(self, obj: dict):
        if "model" in obj:
            self.target["subtype"] = obj["model"]

    def parse_algorithm(self, obj: dict):
        for algo in obj["algos"]:
            if algo["id"] == obj["algo_select"]:
                self.target["algorithm"] = obj["algos"][algo["id"]]["name"]
                break

    def parse_firmware(self, obj: dict):
        if "firmware" in obj:
            self.target["firmware"] = obj["firmware"]
