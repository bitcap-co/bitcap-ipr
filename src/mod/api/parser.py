from abc import ABC, abstractmethod


class Parser(ABC):
    def __init__(self, target: dict) -> None:
        self.target = target.copy()

    def __new__(cls, *args, **kwargs):
        if cls is Parser:
            raise TypeError(f"Only children of '{cls.__name__}' may be instantiated")
        return object.__new__(cls)

    def get_target(self) -> dict:
        return self.target

    @abstractmethod
    def parse_subtype(self, obj: dict) -> None:
        pass

    @abstractmethod
    def parse_firmware(self, obj: dict) -> None:
        pass
