import base64
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional

from Crypto.Cipher import AES

from mod.api import settings
from mod.api.errors import APIError
from mod.api.tcp import BaseTCPClient

logger = logging.getLogger(__name__)


class WhatsminerV3Client(BaseTCPClient):
    """Whatsminer API v3 Client"""

    def __init__(
        self,
        ip_addr: str,
        user: Optional[str] = None,
        passwd: Optional[str] = None,
        port: int = 4433,
    ):
        if not user:
            self.username = "super"
        if not passwd:
            self.passwd: str = settings.get("default_whatsminer_v3_passwd", "super")
        self.salt = ""
        super().__init__(ip_addr, port, user, passwd)

        self._initialize_client()

    def _initialize_client(self):
        self._connect()
        # get and set salt
        salt = self.run_command("get.device.info", "salt")
        self.salt = salt["salt"]

    def _generate_token(self, command: str, ts: int) -> str:
        src = f"{command}{self.passwd}{self.salt}{ts}"
        aes_key = hashlib.sha256(src.encode("utf-8")).digest()
        token_info = base64.b64encode(aes_key).decode("utf-8")
        return token_info[:8]

    def _encrypt_param(self, param: str, command: str, ts: int) -> str:
        src = f"{command}{self.passwd}{self.salt}{ts}"
        aes_key = hashlib.sha256(src.encode("utf-8")).digest()
        pad_len = 16 - (len(param) % 16)
        padded_param = param + (chr(pad_len) * pad_len)
        cipher = AES.new(aes_key, AES.MODE_ECB)
        enc_param = cipher.encrypt(padded_param.encode())
        return base64.b64encode(enc_param).decode()

    def create_get_cmd(self, command: str, param: Optional[Any] = None) -> str:
        cmd = json.dumps({"cmd": command, "param": param})
        return cmd

    def create_set_cmd(self, command: str, param: Optional[Any] = None) -> str:
        cmd: Dict[str, Any] = {"cmd": command, "param": param}
        ts = int(time.time())
        token = self._generate_token(command, ts)
        cmd["ts"] = ts
        cmd["token"] = token
        cmd["account"] = self.username
        if command == "set.miner.pools":
            ts = int(time.time())
            cmd.update(
                {
                    "ts": ts,
                    "token": token,
                    "account": self.username,
                    "param": self._encrypt_param(json.dumps(param), command, ts),
                }
            )
        return json.dumps(cmd)

    def run_command(
        self, command: str, param: Optional[Any] = None, privileged: bool = False
    ) -> Dict[str, Any]:
        cmd = self.create_get_cmd(command, param)
        if privileged:
            cmd = self.create_set_cmd(command, param)
        resp = self.wm_v3_send(cmd, len(cmd))

        if resp["code"] == 0:
            logger.debug(resp)
            return resp["msg"]
        else:
            self._close_client(APIError(f"API Error: {json.dumps(resp, indent=2)}"))

    def get_miner_info(self) -> Dict[str, Any]:
        dev_info = self.run_command("get.device.info", "miner")
        return dev_info["miner"]

    def get_system_info(self) -> Dict[str, Any]:
        sys_info = self.run_command("get.device.info", "system")
        return sys_info["system"]

    def get_pool_conf(self) -> Dict[str, Any]:
        return self.get_pools()

    def get_pools(self) -> Dict[str, Any]:
        pools = self.run_command("get.miner.status", "pools")
        return pools["pools"]

    def blink(
        self,
        enabled: bool,
        auto: bool = True,
        period: int = 1000,
        duration: int = 500,
        start: int = 0,
    ):
        if enabled:
            auto = False
        if auto:
            self.run_command("set.system.led", "auto", True)
        else:
            param_data = [
                {
                    "color": "red",
                    "period": period,
                    "duration": duration,
                    "start": start,
                },
                {
                    "color": "green",
                    "period": period,
                    "duration": duration,
                    "start": start,
                },
            ]
            self.run_command("set.system.led", param_data, True)

    def update_pools(
        self, urls: List[str], users: List[str], passwds: List[str]
    ) -> None:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            self._close_client(APIError("API Error: Invalid number of argurments."))

        param_data = [
            {
                "pool": urls[0],
                "worker": users[0],
                "passwd": passwds[0],
            },
            {
                "pool": urls[1],
                "worker": users[1],
                "passwd": passwds[1],
            },
            {
                "pool": urls[2],
                "worker": users[2],
                "passwd": passwds[2],
            },
        ]
        self.run_command("set.miner.pools", param_data, True)
