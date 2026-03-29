import json
import re
import socket
from abc import abstractmethod
from typing import Self

from apiv2 import settings
from apiv2.base import BaseClient
from apiv2.errors import APIError, FailedConnectionError


class BaseRPCClient(BaseClient):
    """Base client for JSON-RPC APIs for handling requests/commands"""

    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port)

        self._timeout = settings.get("rpc_blocking_timeout", 10.0)
        self.connected: bool = False

    def __new__(cls, *args, **kwargs) -> Self:
        if cls is BaseRPCClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def _connect(self, sock: socket.socket) -> None:
        try:
            sock.settimeout(self._timeout)
            sock.connect((self.ip, self.port))
        except TimeoutError:
            if sock:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()
            raise FailedConnectionError("Failed to connect or timeout occurred")
        else:
            self.connected = True

    def _do_rpc(self, command: str) -> dict:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self._connect(s)
            s.send(command.encode("utf-8"))
            data = self._recv_all(s, 4000)
            if data is None:
                raise APIError("Failed to receive API response")

            if data == b"Socket connect failed: Connection refused\n":
                raise APIError("Connection Failed: connection refused.")

            resp = self._load_api_data(data)
            return resp

    def _load_api_data(self, data: bytes) -> dict:
        # some json from the API returns with a null byte (\x00) on the end
        if data.endswith(b"\x00"):
            str_data = data.decode("utf-8", errors="replace")[:-1]
        else:
            str_data = data.decode("utf-8", errors="replace")
        # fix an error with a btminer return having an extra comma that breaks json.loads()
        str_data = str_data.replace(",}", "}")
        # fix an error with a btminer return having a newline that breaks json.loads()
        str_data = str_data.replace("\n", "")
        # fix an error with a bmminer return not having a specific comma that breaks json.loads()
        str_data = str_data.replace("}{", "},{")
        # fix an error with a bmminer return having a specific comma that breaks json.loads()
        str_data = str_data.replace("[,{", "[{")
        # fix an error with a btminer return having a missing comma. (2023-01-06 version)
        str_data = str_data.replace('""temp0', '","temp0')

        # try to fix an error with overflowing the receive buffer
        # this can happen in cases such as bugged btminers returning arbitrary length error info with 100s of errors.
        if not str_data.endswith("}"):
            str_data = ",".join(str_data.split(",")[:-1]) + "}"

        # fix a really nasty bug with whatsminer API v2.0.4 where they return a list structured like a dict
        if re.search(r"\"error_code\":\[\".+\"\]", str_data):
            str_data = str_data.replace("[", "{").replace("]", "}")

        try:
            api_data = json.loads(str_data)
        except json.JSONDecodeError:
            raise APIError("Failed to decode JSON from API response")
        return api_data

    @abstractmethod
    def version(self) -> dict:
        """Get miner version info"""
        raise NotImplementedError

    @abstractmethod
    def summary(self) -> dict:
        """Get status summary of miner"""
        raise NotImplementedError

    @abstractmethod
    def pools(self) -> list[dict]:
        """Get pool information"""
        raise NotImplementedError

    @abstractmethod
    def devs(self) -> list[dict]:
        """Get data on each PGA/ASC devices"""
        raise NotImplementedError

    @abstractmethod
    def devdetails(self) -> list[dict]:
        """Get static details on all devices"""
        raise NotImplementedError

    @abstractmethod
    def stats(self) -> list[dict]:
        """Get stats of each device/pool"""
        raise NotImplementedError

    @abstractmethod
    def get_system_info(self) -> dict:
        """Get miner system information."""
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

    def send_command(
        self, command: str, parameters: str | int | bool | None = None, **kwargs
    ) -> dict:
        cmd = {"command": command, **kwargs}
        if parameters:
            cmd["parameter"] = parameters
        return self._do_rpc(json.dumps(cmd))

    def send_privileged_command(self, *args, **kwargs) -> dict:
        return self.send_command(*args, **kwargs)

    @staticmethod
    def _recv_all(sock: socket.socket, buf_size: int) -> bytes | None:
        sock.setblocking(True)
        data = bytes()
        while len(data) < buf_size:
            packet = sock.recv(buf_size - len(data))
            if not packet:
                if data:
                    return data
                return None
            data += packet
        return data

    def _close(self, ex: Exception | None = None) -> None:
        return super()._close(ex)
