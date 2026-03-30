from abc import ABC, abstractmethod
from typing import Any, Self

from .. import MinerData


class BaseParser(ABC):
    def __init__(self) -> None:
        self.data = MinerData()

    def __new__(cls) -> Self:
        if cls is BaseParser:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def get_data(self) -> dict[str, Any]:
        return self.data.as_dict()

    @abstractmethod
    def parse_api_version(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_uptime(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_hostname(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_mac(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_serial(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_type(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_subtype(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_algorithm(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_firmware(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_platform(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_system_info(self, obj: Any) -> None:
        pass

    @abstractmethod
    def parse_pools(self, obj: list[dict]) -> None:
        pass

    def parse_all(self, obj: dict[str, Any]) -> None:
        self.parse_api_version(obj)
        self.parse_hostname(obj)
        self.parse_mac(obj)
        self.parse_serial(obj)
        self.parse_type(obj)
        self.parse_subtype(obj)
        self.parse_algorithm(obj)
        self.parse_firmware(obj)
        self.parse_platform(obj)
