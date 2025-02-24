import logging
import requests
from requests.auth import HTTPDigestAuth
from string import Template

from .errors import FailedConnectionError, AuthenticationError

logger = logging.getLogger(__name__)


class VolcminerHTTPClient:
    """Volcminer HTTP Client"""

    def __init__(self, ip_addr: str, passwd: str):
        self.ip = ip_addr
        self.host = f"http://{self.ip}/"
        self.passwd = passwd
        self.digest = None
        self.command_prefix = Template("cgi-bin/${cmd}.cgi")
        self.err = None
        self._initialize_session()

    def _initialize_session(self):
        self.session = requests.Session()
        self.session.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }
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
        passwds = (
            [self.passwd, "ltc@dog"] if self.passwd != "ltc@dog" else [self.passwd]
        )
        for passwd in passwds:
            self.session.auth = HTTPDigestAuth("root", passwd)
            res = self.session.head(self.host, timeout=3.0)
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
            method=method, url=self.host + path, headers=self.session.headers
        )
        if self.digest:
            req.auth = self.digest
        if payload:
            req.data = payload
        r = req.prepare()
        res = self.session.send(r)
        try:
            return res.json()
        except requests.exceptions.JSONDecodeError:
            logger.warning("_do_http : return wrapped plaintext content.")
            return {"plaintext": res.text}

    def run_command(self, method: str, command: str, payload: dict | None = None):
        path = self.command_prefix.substitute(cmd=command)
        return self._do_http(method, path, payload)

    def get_system_info(self):
        return self.run_command("GET", "get_system_info")

    def blink(self, enabled: bool):
        data = {"_bb_type": "rgOn" if enabled else "rgOff"}
        self.run_command("POST", "post_led_onoff", data)

    def _close_client(self, error: Exception | None = None):
        self.session.close()
        if error:
            self.err = error
            raise error


class VolcminerParser:
    def __init__(self, target: dict):
        self.target = target.copy()

    def get_target(self):
        return self.target

    def parse_subtype(self, obj: dict):
        if "minertype" in obj:
            self.target["subtype"] = obj["minertype"][10:]

    def parse_firmware(self, obj: dict):
        if "system_filesystem_version" in obj:
            self.target["firmware"] = obj["system_filesystem_version"]
