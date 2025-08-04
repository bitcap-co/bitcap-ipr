from typing import Dict, Any

from ...parser import Parser


class SealminerParser(Parser):
    def __init__(self, target: Dict[str, str]):
        super().__init__(target)
        self.target["algorithm"] = "sha256"

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        if "miner_type" in obj:
            self.target["subtype"] = obj["miner_type"]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        if "firmware_version" in obj:
            self.target["firmware"] = obj["firmware_version"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        if "ctrl_version" in obj:
            self.target["platform"] = obj["ctrl_version"]

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        return super().parse_system_info(obj)

    def parse_pools(self, obj: Dict[str, Any]) -> None:
        pool = obj["pools"][0]
        self.target["pool"] = pool["url"]
        self.target["worker"] = pool["user"]
