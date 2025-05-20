import socket
import json
from abc import ABC, abstractmethod

from .errors import FailedConnectionError

import logging

logger = logging.getLogger(__name__)


class BaseRPCClient(ABC):
    def __init__(self, ip: str, port: int = 4028):
        self.ip = ip
        self.port = port
        self.passwd = None

        self.timeout = 3.0

        self._error = None

    def __new__(cls, *args, **kwargs):
        if cls is BaseRPCClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def __repr__(self):
        return f"{self.__class__.__name__}: {str(self.ip)}"

    def _test_connection(self):
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

    def _close_client(self, error: Exception | None = None) -> None:
        if error:
            self._error = error
            raise error
