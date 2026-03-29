import json
import logging
import socket
import struct
from abc import abstractmethod
from typing import Any, Self

from apiv2 import settings
from apiv2.base.base import BaseClient
from apiv2.errors import APIError, APIInvalidResponse, FailedConnectionError

logger = logging.getLogger(__name__)


class BaseTCPClient(BaseClient):
    def __init__(
        self,
        ip: str,
        port: int,
        username: str | None = None,
        alt_pwd: str | None = None,
    ) -> None:
        super().__init__(ip, port)

        self._timeout = settings.get("tcp_blocking_timeout", 10.0)
        self.connected: bool = False
        self._sock: socket.socket | None = None

        _ = self._connect()

    def __new__(cls, *args, **kwargs) -> Self:
        if cls is BaseTCPClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def _connect(self) -> bool:
        if not self.connected:
            try:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.settimeout(self._timeout)
                self._sock.connect((self.ip, self.port))
            except TimeoutError:
                if self._sock:
                    try:
                        self._sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    self._sock.close()
                    self._sock = None
                raise FailedConnectionError("Failed to connect or timeout occurred")
            else:
                self.connected = True
        return self.connected

    # whatsminer v3 api methods
    def btv3_send(self, msg: str, msg_len: int) -> dict[str, Any]:
        if self._sock is None:
            return {}
        packed_size = struct.pack("<I", msg_len)
        self._sock.sendall(packed_size)
        self._sock.sendall(msg.encode())
        data = self._btv3_recv_all(self._sock)
        try:
            resp = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resp

    def _btv3_recv_all(self, sock: socket.socket) -> str:
        buffer = b""
        # get first 4 bytes for length
        packed_len = sock.recv(4)
        if len(packed_len) < 4:
            logger.error(
                f"{self.__repr__()} : {str(APIError('Failed to get response length'))}"
            )
            raise APIError("Invalid response length")

        msg_len = struct.unpack("<I", packed_len)[0]
        if msg_len > 8192:
            logger.error(
                f"{self.__repr__()} : {str(APIError(f'Invalid response length {msg_len}'))}"
            )
            raise APIError("Invalid response length")

        while len(buffer) < msg_len:
            data = sock.recv(msg_len - len(buffer))
            if not data:
                break
            buffer += data
        return buffer.decode()

    @abstractmethod
    def get_hostname(self) -> str:
        """Get miner hostname from network configuration."""
        raise NotImplementedError

    @abstractmethod
    def get_mac_addr(self) -> str:
        """Get miner MAC address."""
        raise NotImplementedError

    @abstractmethod
    def get_api_version(self) -> str:
        """Get miner API version."""
        raise NotImplementedError

    @abstractmethod
    def get_system_info(self) -> dict:
        """Get miner system information."""
        raise NotImplementedError

    @abstractmethod
    def get_network_info(self) -> dict:
        """Get miner network information."""
        raise NotImplementedError

    @abstractmethod
    def log(self, *args, **kwargs) -> dict:
        """Get miner log."""
        raise NotImplementedError

    @abstractmethod
    def summary(self) -> dict:
        """Get miner status information."""
        raise NotImplementedError

    @abstractmethod
    def get_miner_conf(self) -> dict:
        """Get current miner configuration."""
        raise NotImplementedError

    @abstractmethod
    def set_miner_conf(self, *args, **kwargs) -> dict:
        """Set miner configuration."""
        raise NotImplementedError

    @abstractmethod
    def pools(self) -> list[dict]:
        """Get miner pool status information."""
        raise NotImplementedError

    @abstractmethod
    def get_pool_conf(self) -> list[dict]:
        """Get current miner pool configuration."""
        raise NotImplementedError

    @abstractmethod
    def get_miner_status(self) -> dict:
        """Get current miner status"""
        raise NotImplementedError

    @abstractmethod
    def get_blink_status(self) -> dict:
        """Get miner LED blink status."""
        raise NotImplementedError

    @abstractmethod
    def blink(self, enabled: bool, *args, **kwargs) -> dict:
        """Blink miner LEDS for locating."""
        raise NotImplementedError

    @abstractmethod
    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        """Update the current miner pool configuration."""
        raise NotImplementedError

    def _close(self, ex: Exception | None = None) -> None:
        if self._sock is not None:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._sock.close()
            self._sock = None
        if ex:
            self._ex = ex
