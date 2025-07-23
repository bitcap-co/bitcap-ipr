from typing import Dict, Any

from ...parser import Parser


class VolcminerParser(Parser):
    def __init__(self, target: Dict[str, str]):
        super().__init__(target)
        self.target["algorithm"] = "SCRYPT"

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        if "minertype" in obj:
            self.target["subtype"] = obj["minertype"][10:]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: dict):
        if "system_filesystem_version" in obj:
            self.target["firmware"] = obj["system_filesystem_version"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        return super().parse_system_info(obj)
