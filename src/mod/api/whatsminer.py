import logging
import re
import hashlib
import binascii
import base64
import socket
import json

from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from passlib.hash import md5_crypt

from .errors import (
    FailedConnectionError,
    AuthenticationError,
    TokenOverMaxTimesError
)

logger = logging.getLogger(__name__)


class WhatsminerClient():
    """Whatsminer JSON-RPC API client"""
    def __init__(self, ip_addr: str, port: int, admin_passwd: str = None):
        self.ip_addr = ip_addr
        self.port = port
        self.admin_passwd = admin_passwd
        if not self.admin_passwd:
            if self.admin_passwd == "":
                self.admin_passwd = "admin"
        self._test_connection()


    def _test_connection(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            try:
                s.connect((self.ip_addr, self.port))
            except TimeoutError:
                self.close_client()
                raise FailedConnectionError("Connection Failed: Failed to connect or timeout occurred.")

    def _create_token(self):
        """
        Encryption algorithm:
        Ciphertext = aes256(plaintext), ECB mode
        Encode text = base64(ciphertext)

        (1)api_cmd = token,$sign|api_str    # api_str is API command plaintext
        (2)enc_str = aes256(api_cmd, $key)  # ECB mode
        (3)tran_str = base64(enc_str)

        Final assembly: enc|base64(aes256("token,sign|set_led|auto", $aeskey))
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.ip_addr, self.port))
            s.sendall('{"cmd": "get_token"}'.encode("utf-8"))
            data = recv_all(s, 4000)

        token_info = json.loads(data)["Msg"]
        if token_info == "over max connect":
            raise TokenOverMaxTimesError("Token Creation Failed: token over max times.")

        # Make encrypted key from passwd and salt
        key = md5_encrypt(self.admin_passwd, token_info["salt"])

        aeskey = hashlib.sha256(key.encode()).hexdigest()
        aeskey = binascii.unhexlify(aeskey.encode())
        self.cipher = AES.new(aeskey, AES.MODE_ECB)

        self.sign = md5_encrypt(key + token_info["time"], token_info["newsalt"])

    def enable_write_access(self, admin_passwd: str):
        self.admin_passwd = admin_passwd
        self._create_token

    def has_write_access(self):
        if not self.admin_passwd:
            return False
        return True

    def _do_rpc(self, payload: dict, params: dict = None, write: bool = False):
        if params:
            payload.update(params)
        cmd = json.dumps(payload)
        if write:
            enc_str = str(
                base64.encodebytes(
                    self.cipher.encrypt(add_to_16(cmd))),
                    encoding="utf8"
            ).replace('\n', '')
            data_enc = {"enc": 1}
            data_enc["data"] = enc_str
            cmd = json.dumps(data_enc)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.ip_addr, self.port))
            s.send(cmd.encode("utf-8"))
            data = recv_all(s, 4000)

        res = json.loads(data.decode())
        if "STATUS" in res and res["STATUS"] == "E":
            logger.error(res["Msg"])
        if write:
            res_ciphertext = b64decode(json.loads(data.decode()))["enc"]
            res_plaintext = self.cipher.decrypt(res_ciphertext).decode().split("\x00")[0]
            res = json.loads(res_plaintext)

        return res

    def _exec_authenticated_command(self, command: dict, params: dict = None):
        success = False
        passwds = [self.admin_passwd]
        if self.admin_passwd != "admin":
            passwds.append("admin")
        for passwd in passwds:
            self.enable_write_access(passwd)
            command.update({"token": self.sign})
            try:
                res = self._do_rpc(command, params, True)
                success = True
            except KeyError:
                continue
        if not success:
            self.close_client()
            raise AuthenticationError("Authentication Failed: failed to authenticate to miner.")
        return res

    def get_version(self):
        cmd = {"cmd": "get_version"}
        return self._do_rpc(cmd)

    def get_dev_details(self):
        cmd = {"cmd": "devdetails"}
        return self._do_rpc(cmd)

    def close_client(self):
        self = None


class WhatsminerParser():
    def __init__(self, target: dict):
        self.target = target.copy()
        self.target["algorithm"] = "SHA256"

    def get_target(self):
        return self.target

    def parse_subtype(self, resp: dict):
        dev = resp["DEVDETAILS"][0]
        if "Model" in dev:
            self.target["subtype"] = dev["Model"]

    def parse_firmware(self, resp: dict):
        msg = resp["Msg"]
        if "fw_ver" in msg:
            self.target["firmware"] = msg["fw_ver"]

    def parse_platform(self, resp: dict):
        msg = resp["Msg"]
        if "platform" in msg:
            self.target["platform"] = msg["platform"]


def md5_encrypt(word: str, salt: str):
    salt = "$1$" + salt + "$"
    salt_expr = re.compile('\s*\$(\d+)\$([\w\./]*)\$')
    is_salt = salt_expr.match(salt)
    if not is_salt:
        raise ValueError("Invalid salt format")
    extra_str = is_salt.group(2)
    encrypted = md5_crypt.hash(word, salt=extra_str).split("$")
    return encrypted[3]


def recv_all(sock: socket.socket, buf_size: int):
    sock.setblocking(True)
    data = bytearray()
    while len(data) < buf_size:
        packet = sock.recv(buf_size - len(data))
        if not packet:
            if data:
                return data
            return None
        data.extend(packet)
    return data


def add_to_16(s: str):
    while len(s) % 16 != 0:
        s += '\0'
    return str.encode(s)
