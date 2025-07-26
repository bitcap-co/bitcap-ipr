from typing import Any, Dict
from ....parser import Parser


class WhatsminerV3Parser(Parser):
    def __init__(self, target: dict):
        super().__init__(target)
        self.target["algorithm"] = "SHA256"

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        if "miner-sn" in obj and obj["miner-sn"]:
            self.target["serial"] = obj["miner-sn"]

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        if "type" in obj:
            self.target["subtype"] = obj["type"]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        if "fwversion" in obj:
            self.target["firmware"] = obj["fwversion"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        if "platform" in obj:
            self.target["platform"] = obj["platform"]

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        self.parse_firmware(obj)
        self.parse_platform(obj)

    def parse_miner_info(self, obj: Dict[str, Any]) -> None:
        self.parse_serial(obj)
        self.parse_subtype(obj)
