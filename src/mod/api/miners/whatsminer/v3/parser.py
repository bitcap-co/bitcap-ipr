from ....parser import Parser


class WhatsminerV3Parser(Parser):
    def __init__(self, target: dict):
        super().__init__(target)
        self.target["algorithm"] = "SHA256"

    def parse_serial(self, obj: dict) -> None:
        if "miner-sn" in obj and obj["miner-sn"]:
            self.target["serial"] = obj["miner-sn"]

    def parse_subtype(self, obj: dict) -> None:
        if "type" in obj:
            self.target["subtype"] = obj["type"]

    def parse_firmware(self, obj: dict) -> None:
        if "fwversion" in obj:
            self.target["firmware"] = obj["fwversion"]

    def parse_platform(self, obj: dict) -> None:
        if "platform" in obj:
            self.target["platform"] = obj["platform"]

    def parse_system_info(self, obj: dict) -> None:
        self.parse_firmware()
        self.parse_platform()

    def parse_miner_info(self, obj: dict) -> None:
        self.parse_serial()
        self.parse_subtype()
