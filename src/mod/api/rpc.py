import json
import logging
import re
import socket
from abc import ABC, abstractmethod
from typing import Optional

from mod.api import settings
from mod.api.errors import APIError, FailedConnectionError

logger = logging.getLogger(__name__)


class BaseRPCClient(ABC):
    def __init__(self, ip: str, port: int = 4028):
        self.ip = ip
        self.port = port
        self.passwd: Optional[str] = None

        self.timeout: float = settings.get("rpc_request_timeout")

        self._error: Optional[Exception] = None

    def __new__(cls, *args, **kwargs):
        if cls is BaseRPCClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def __repr__(self):
        return f"{self.__class__.__name__}: {str(self.ip)}"

    def _test_connection(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            try:
                s.connect((self.ip, self.port))
            except TimeoutError:
                self._close_client(
                    FailedConnectionError(
                        "Connection Failed: Failed to connect or timeout occurred."
                    )
                )

    def _do_rpc(self, command: str, port: int = None, timeout: float = None) -> dict:
        if port is None:
            port = self.port
        if timeout is None:
            timeout = self.timeout
        try:
            logger.debug(f" send rpc command: {command}.")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((self.ip, port))
                s.send(command.encode("utf-8"))
                data = self._recv_all(s, 4000)
            if data is None:
                self._close_client(APIError("API Error: API failed to respond."))

            if data == b"Socket connect failed: Connection refused\n":
                self._close_client(
                    FailedConnectionError(
                        "Connection Failed: Failed to connect or timeout occurred."
                    )
                )

            res = self._load_api_data(data)
            logger.debug(f" received api response: {res}.")
            return res
        except TimeoutError:
            self._close_client(
                FailedConnectionError(
                    "Connection Failed: Failed to connect or timeout occurred."
                )
            )

    def run_command(
        self,
        command: str,
        **kwargs
    ) -> dict:
        cmd = json.dumps({"cmd": command, **kwargs})
        return self._do_rpc(cmd)

    @abstractmethod
    def get_system_info(self) -> dict:
        pass

    @abstractmethod
    def blink(self, enabled: bool, **kwargs) -> None:
        pass

    def _load_api_data(self, data: bytes) -> dict:
        str_data = data.decode("utf-8").rstrip("\x00")
        str_data = str_data.replace(",}", "}")
        str_data = str_data.replace("\n", "")

        # # try to fix an error with overflowing the receive buffer
        # # this can happen in cases such as bugged btminers returning arbitrary length error info with 100s of errors.
        if not str_data.endswith("}"):
            str_data = ",".join(str_data.split(",")[:-1]) + "}"

        # # fix a really nasty bug with whatsminer API v2.0.4 where they return a list structured like a dict
        if re.search(r"\"error_code\":\[\".+\"\]", str_data):
            str_data = str_data.replace("[", "{").replace("]", "}")

        try:
            api_data = json.loads(str_data)
        except json.JSONDecodeError:
            self._close_client(APIError("API Error: Failed to decode data from API."))
        return api_data

    @staticmethod
    def _recv_all(s: socket.socket, buf_size: int) -> Optional[bytearray]:
        s.setblocking(True)
        data = bytearray()
        while len(data) < buf_size:
            packet = s.recv(buf_size - len(data))
            if not packet:
                if data:
                    return data
                return None
            data.extend(packet)
        return data

    def _close_client(self, error: Exception | None = None) -> None:
        if error:
            self._error = error
            raise error
