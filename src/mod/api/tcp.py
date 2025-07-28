import logging
import json
import socket
import struct
from abc import ABC
from typing import Dict, Optional, Any

from mod.api import settings
from mod.api.errors import APIError, FailedConnectionError

logger = logging.getLogger(__name__)


class BaseTCPClient(ABC):
    def __init__(self, ip: str, port: int, username: Optional[str] = None, passwd: Optional[str] = None):
        self.ip = ip
        self.port = port
        self.username = username
        self.passwd = passwd

        self.timeout = settings.get("tcp_request_timeout")
        self.sock: Optional[socket.socket] = None

        self._error = None

    def __new__(cls, *args, **kwargs):
        if cls is BaseTCPClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {str(self.ip)}"

    def _connect(self) -> None:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.ip, self.port))
        except TimeoutError:
            self._close_client(
                FailedConnectionError(
                    "Connection Failed: Failed to connect or timeout occurred."
                )
            )

    # whatsminer api v3
    def wm_v3_send(self, msg: str, msg_len: int) -> Dict[str, Any]:
        packed_size = struct.pack("<I", msg_len)
        self.sock.sendall(packed_size)
        self.sock.sendall(msg.encode())
        resp = self._wm_v3_recv_all()

        if resp is None:
            self._close_client(
                APIError(
                    "API Error: Failed to receive response."
                )
            )

        return json.loads(resp)

    def _wm_v3_recv_all(self) -> Optional[str]:
        buffer = b""
        # get first 4 bytes for length of data
        packed_len = self.sock.recv(4)
        if len(packed_len) < 4:
            logger.error("_wm_v3_receive : failed to get resp length")
            return None

        resp_len = struct.unpack("<I", packed_len)[0]
        if resp_len > 8192:
            logger.error(f"_wm_v3_receive : invalid resp length: {resp_len}")
            return None

        while len(buffer) < resp_len:
            data = self.sock.recv(resp_len - len(buffer))
            if not data:
                break
            buffer += data
        return buffer.decode()

    def _close_client(self, error: Exception | None = None) -> None:
        if self.sock:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        if error:
            self._error = error
            raise error
