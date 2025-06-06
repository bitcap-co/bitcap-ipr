import requests
from requests.auth import HTTPDigestAuth
from string import Template

from mod.api import settings
from mod.api.http import BaseHTTPClient
from mod.api.errors import (
    FailedConnectionError,
    AuthenticationError,
)


class BitmainHTTPClient(BaseHTTPClient):
    """Bitmain/Antminer HTTP Client with support for vnish"""

    def __init__(self, ip_addr: str, passwd: str, vnish_passwd: str):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "root"
        self.passwds = [passwd, settings.get("default_bitmain_passwd")]
        self.vnish_passwds = [vnish_passwd, settings.get("default_vnish_passwd")]
        self.command_format = {
            "vnish": "api/v1",
            "stock": Template("cgi-bin/${cmd}.cgi"),
        }

        self._initialize_session()

    def _initialize_session(self) -> None:
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
            return True
        return False

    def unlock_vnish_session(self):
        for passwd in self.vnish_passwds:
            if not passwd:
                continue
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
                self.session.headers.update(
                    {"Authorization": "Bearer " + resj["token"]}
                )
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
            self.run_command("POST", "blink", payload={"blink": enabled})
