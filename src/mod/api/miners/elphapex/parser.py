from typing import Dict, Any

from ...parser import Parser


class ElphapexParser(Parser):
    def __init__(self, target: Dict[str, str]):
        super().__init__(target)

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        if "minertype" in obj:
            self.target["subtype"] = obj["minertype"]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        if "Algorithm" in obj:
            self.target["algorithm"] = obj["Algorithm"]

    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        if "system_filesystem_version" in obj:
            self.target["firmware"] = obj["system_filesystem_version"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        if "INFO" in obj:
            if "hw_version" in obj["INFO"]:
                self.target["platform"] = obj["INFO"]["hw_version"]

    def parse_pools(self, obj: Dict[str, Any]) -> None:
        for pool in obj["POOLS"]:
            if pool["status"] == "Alive":
                self.target["pool"] = pool["url"]
                self.target["worker"] = pool["user"]
                break

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        self.parse_subtype(obj)
        self.parse_firmware(obj)
        self.parse_algorithm(obj)
