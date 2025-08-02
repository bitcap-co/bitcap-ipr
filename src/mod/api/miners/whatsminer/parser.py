from typing import Dict, Any

from ...parser import Parser


class WhatsminerParser(Parser):
    def __init__(self, target: Dict[str, str]):
        super().__init__(target)
        self.target["algorithm"] = "SHA256"

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        msg = obj["Msg"]
        if "minersn" in msg and msg["minersn"]:
            self.target["serial"] = msg["minersn"]

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        dev = obj["DEVDETAILS"][0]
        if "Model" in dev:
            self.target["subtype"] = dev["Model"]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        msg = obj["Msg"]
        if "fw_ver" in msg:
            self.target["firmware"] = msg["fw_ver"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        msg = obj["Msg"]
        if "platform" in msg:
            self.target["platform"] = msg["platform"]

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        self.parse_serial(obj)

    def parse_pools(self, obj: Dict[str, Any]) -> None:
        for pool in obj["POOLS"]:
            if pool["Status"] == "Alive":
                self.target["pool"] == pool["URL"]
                self.target["worker"] == pool["User"]

    def parse_version_info(self, obj: Dict[str, Any]) -> None:
        self.parse_firmware(obj)
        self.parse_platform(obj)
