import base64
import binascii
import datetime
import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional

from Crypto.Cipher import AES
from passlib.hash import md5_crypt

from mod.api import settings
from mod.api.errors import (
    APIError,
    AuthenticationError,
    TokenOverMaxTimesError,
)
from mod.api.rpc import BaseRPCClient

logger = logging.getLogger(__name__)


def _crypt(word: str, salt: str) -> str:
    stdsalt = re.compile(r"\s*\$(\d+)\$([\w\./]*)\$")
    match = stdsalt.match(salt)
    if not match:
        raise ValueError("Invalid salt format")
    new_salt = match.group(2)
    result = md5_crypt.hash(word, salt=new_salt)
    return result


def _add_to_16(s: str) -> bytes:
    while len(s) % 16 != 0:
        s += "\0"
    return str.encode(s)


def create_privileged_cmd(token: Dict[str, Any], command: dict) -> str:
    command.update({"token": token["sign"]})
    aeskey = hashlib.sha256(token["key"].encode()).hexdigest()
    aeskey = binascii.unhexlify(aeskey.encode())
    aes = AES.new(aeskey, AES.MODE_ECB)
    cmd_str = json.dumps(command)
    enc_cmd_str = str(
        base64.encodebytes(aes.encrypt(_add_to_16(cmd_str))),
        encoding="utf8",
    ).replace("\n", "")
    data_enc = {"enc": 1, "data": enc_cmd_str}
    cmd = json.dumps(data_enc)
    return cmd


def parse_privileged_data(token: Dict[str, Any], data: dict) -> dict:
    enc_data = data["enc"]
    aeskey = hashlib.sha256(token["key"].encode()).hexdigest()
    aeskey = binascii.unhexlify(aeskey.encode())
    aes = AES.new(aeskey, AES.MODE_ECB)
    res = json.loads(
        aes.decrypt(base64.decodebytes(bytes(enc_data, encoding="utf-8")))
        .rstrip(b"\x00")
        .decode("utf-8")
    )
    return res


class WhatsminerRPCClient(BaseRPCClient):
    """Whatsminer JSON-RPC API V2 client"""

    def __init__(self, ip_addr: str, passwd: Optional[str]):
        super().__init__(ip_addr)
        self.passwds: List[str] = [passwd, settings.get("default_whatsminer_passwd")]
        self.token = None

        self._test_connection()

    def send_privileged_command(self, command: str, **kwargs):
        cmd = {"cmd": command, **kwargs}
        success = False
        for passwd in self.passwds:
            if not passwd:
                continue
            self.enable_write_access(passwd)
            privileged_cmd = create_privileged_cmd(self.token, cmd)
            res = self._do_rpc(privileged_cmd)
            if "STATUS" in res and res["STATUS"] == "E":
                # handle incorrect passwd
                if res["Code"] == 23:
                    self.token = None
                    continue
            success = True
        if not success:
            self._close_client(
                AuthenticationError(
                    "Authentication Failed: failed to authenticate to miner."
                )
            )
        res = parse_privileged_data(self.token, res)
        logger.debug(f" parsed privileged data: {res}.")

    def get_token(self) -> Dict[str, Any]:
        """
        Encryption algorithm:
        Ciphertext = aes256(plaintext), ECB mode
        Encode text = base64(ciphertext)

        (1)api_cmd = token,$sign|api_str    # api_str is API command plaintext
        (2)enc_str = aes256(api_cmd, $key)  # ECB mode
        (3)tran_str = base64(enc_str)

        Final assembly: enc|base64(aes256("token,sign|set_led|auto", $aeskey))
        """
        if self.token:
            if self.token["timestamp"] > datetime.datetime.now() - datetime.timedelta(
                minutes=30
            ):
                return self.token

        data = self.run_command("get_token")

        token_info = data["Msg"]
        if token_info == "over max connect":
            self._close_client(
                TokenOverMaxTimesError("Token Creation Failed: token over max times.")
            )
        # Make encrypted key from passwd and salt
        pwd = _crypt(self.passwd, "$1$" + token_info["salt"] + "$")
        pwd = pwd.split("$")
        key = pwd[3]

        tmp = _crypt(key + token_info["time"], "$1$" + token_info["newsalt"] + "$")
        tmp = tmp.split("$")
        sign = tmp[3]

        self.token = {"sign": sign, "key": key, "timestamp": datetime.datetime.now()}
        return self.token

    def enable_write_access(self, passwd: str) -> None:
        self.passwd = passwd
        self.get_token()

    def has_write_access(self) -> bool:
        if not self.passwd:
            return False
        return True

    def get_version(self) -> dict:
        return self.run_command("get_version")

    def get_dev_details(self) -> dict:
        return self.run_command("devdetails")

    def get_system_info(self) -> dict:
        return self.run_command(
            "get_miner_info",
            info="ip,proto,netmask,gateway,dns,hostname,mac,ledstat,gateway",
        )

    def get_pool_conf(self) -> dict:
        return self.get_pools()

    def get_pools(self) -> dict:
        return self.run_command("pools")

    def blink(
        self,
        enabled: bool,
        auto: bool = True,
        color: str = "red",
        period: int = 1000,
        duration: int = 500,
        start: int = 0,
    ) -> None:
        if enabled:
            auto = False
        if auto:
            self.send_privileged_command("set_led", param="auto")
        else:
            self.send_privileged_command(
                "set_led", color=color, period=period, duration=duration, start=start
            )

    def update_pools(
        self, urls: List[str], users: List[str], passwds: List[str]
    ) -> None:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            self._close_client(APIError("API Error: Invalid number of argurments."))

        params: Dict[str, str] = {
            "pool1": urls[0],
            "worker1": users[0],
            "passwd1": passwds[0],
            "pool2": urls[1],
            "worker2": users[1],
            "passwd2": passwds[1],
            "pool3": urls[2],
            "worker3": users[2],
            "passwd3": passwds[2],
        }
        self.send_privileged_command("update_pools", **params)
