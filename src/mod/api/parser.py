from abc import ABC, abstractmethod
from typing import Any, Dict


class Parser(ABC):
    def __init__(self, target: Dict[str, str]) -> None:
        self.target = target.copy()

    def __new__(cls, *args, **kwargs):
        if cls is Parser:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def get_target(self) -> Dict[str, str]:
        return self.target

    @abstractmethod
    def parse_serial(self, obj: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def parse_platform(self, obj: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        self.parse_serial(obj)
        self.parse_subtype(obj)
        self.parse_algorithm(obj)
        self.parse_firmware(obj)
        self.parse_platform(obj)

    @abstractmethod
    def parse_pools(self, obj: Dict[str, Any]) -> None:
        pass
