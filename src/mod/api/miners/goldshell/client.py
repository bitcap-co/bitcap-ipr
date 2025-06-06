import requests
from string import Template
from Crypto.Cipher import AES

from mod.api import settings
from mod.api.http import BaseHTTPClient
from mod.api.errors import (
    FailedConnectionError,
    AuthenticationError,
)


class GoldshellHTTPClient(BaseHTTPClient):
    """Goldshell HTTP Client"""

    def __init__(self, ip_addr: str, passwd: str):
        super().__init__(ip_addr)
        self.url = f"http://{self.ip}:{self.port}/"
        self.username = "admin"
        self.passwds = [passwd, settings.get("default_goldshell_passwd")]
        self.command_format = Template("/mcb/${cmd}")

        self._initialize_session()

    def _initialize_session(self):
        try:
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
        self._do_http("GET", "/user/logout")
        for passwd in self.passwds:
            if not passwd:
                continue
            params = {"username": self.username, "password": passwd, "cipher": "false"}
            res = self._do_http("GET", "/user/login", params=params)
            if res.status_code == 500:
                # login failed, try with encrypted password
                params["password"] = encrypt_to_hex(passwd)
                params["cipher"] = "true"
                res = self._do_http("GET", "/user/login", params=params)
                if res.status_code == 500:
                    continue
            try:
                resj = res.json()
            except requests.exceptions.JSONDecodeError:
                break
            if resj["JWT Token"]:
                self.bearer = resj["JWT Token"]
                break
        if not self.bearer:
            self._close_client(
                AuthenticationError(
                    "Authentication Failed: Failed to authenticate session"
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
        path = self.command_format.substitute(cmd=command)
        res = self._do_http(method, path, params=params, payload=payload)
        try:
            resj = res.json()
        except requests.exceptions.JSONDecodeError:
            resj = {}
        return resj

    def get_system_info(self):
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
        settings["ledcontrol"] = enabled
        self.run_command("PUT", "setting", payload=settings)


def zero_pad(data: bytes, block_size: int) -> bytes:
    padding_len = block_size - len(data) % block_size
    padding = bytes([0]) * padding_len
    return data + padding


def unpad(padded_data: bytes, block_size: int) -> bytes:
    pdata_len = len(padded_data)
    padding_len = pdata_len - padded_data.rfind(bytes([0]))
    return padded_data[:-padding_len]


def encrypt_to_hex(plain: str) -> str:
    cipher = AES.new(
        b"!!!!!!!!!!!!!!!!",
        AES.MODE_CBC,
        iv=bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    )
    b = zero_pad(plain.encode("UTF-8"), 16)
    return cipher.encrypt(b).hex()
