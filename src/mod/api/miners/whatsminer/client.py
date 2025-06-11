import datetime
import logging
import re
import hashlib
import binascii
import base64
import json

from Crypto.Cipher import AES
from passlib.hash import md5_crypt

from mod.api import settings
from mod.api.rpc import BaseRPCClient
from mod.api.errors import (
    AuthenticationError,
    TokenOverMaxTimesError,
)

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


def create_privileged_cmd(token: dict, command: dict) -> str:
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


def parse_privileged_data(token: dict, data: dict) -> dict:
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
    """Whatsminer JSON-RPC API client"""

    def __init__(self, ip_addr: str, passwd: str):
        super().__init__(ip_addr)
        self.passwds = [passwd, settings.get("default_whatsminer_passwd")]
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

    def get_token(self) -> dict:
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

    def enable_write_access(self, passwd: str):
        self.passwd = passwd
        self.get_token()

    def has_write_access(self):
        if not self.passwd:
            return False
        return True

    def get_version(self):
        return self.run_command("get_version")

    def get_dev_details(self):
        return self.run_command("devdetails")

    def get_system_info(self):
        return self.run_command(
            "get_miner_info",
            info="ip,proto,netmask,gateway,dns,hostname,mac,ledstat,gateway",
        )

    def blink(
        self,
        enabled: bool,
        auto: bool = True,
        color: str = "red",
        period: int = 60,
        duration: int = 20,
        start: int = 0,
    ):
        if enabled:
            auto = False
        if auto:
            self.send_privileged_command("set_led", param="auto")
        else:
            self.send_privileged_command("set_led", color=color, period=period, duration=duration, start=start)
