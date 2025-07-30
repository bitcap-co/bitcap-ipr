import base64
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional

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
