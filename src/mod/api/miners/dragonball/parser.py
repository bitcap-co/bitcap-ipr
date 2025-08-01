from typing import Dict, Any

from ...parser import Parser


class DragonballParser(Parser):
    def __init__(self, target: Dict[str, str]):
        super().__init__(target)

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        if "number" in obj:
            self.target["serial"] = obj["number"]

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        if "miner_model" in obj:
            self.target["subtype"] = obj["miner_model"]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        if "swv" in obj:
            self.target["firmware"] = obj["swv"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        return super().parse_platform(obj)

    def parse_pools(self, obj: Dict[str, Any]) -> None:
        return super().parse_pools(obj)

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        self.parse_serial(obj)
        self.parse_subtype(obj)
        self.parse_firmware(obj)
