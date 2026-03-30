from abc import ABC, abstractmethod
from ipaddress import ip_address
from typing import Self


class BaseClient(ABC):
    def __init__(self, ip: str, port: int, *args, **kwargs) -> None:
        self.ip = str(ip)
        self.ip_addr = ip_address(ip)
        self.port = port

        # auth
        self.username: str | None = None
        self.pwd: str | None = None
        self.passwds: list[str] = []
        self.authed: bool = False

        self._ex: Exception | None = None

    def __new__(cls, *args, **kwargs) -> Self:
        if cls is BaseClient:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{str(self.ip)}]"

    def error(self) -> Exception | None:
        if self._ex is not None:
            return self._ex

    @abstractmethod
    def _close(self, ex: Exception | None = None) -> None:
        if ex:
            self._ex = ex
