from typing import Dict, Any

from ...parser import Parser


class GoldshellParser(Parser):
    def __init__(self, target: Dict[str, str]):
        super().__init__(target)

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        if "model" in obj:
            self.target["subtype"] = obj["model"]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        for algo in obj["algos"]:
            if algo["id"] == obj["algo_select"]:
                self.target["algorithm"] = obj["algos"][algo["id"]]["name"]
                break

    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        if "firmware" in obj:
            self.target["firmware"] = obj["firmware"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        self.parse_firmware(obj)
        self.parse_subtype(obj)

    def parse_pools(self, obj: Dict[str, Any]) -> None:
        for pool in obj:
            if pool["active"]:
                self.target["pool"] = pool["url"]
                self.target["worker"] = pool["user"]
                break
