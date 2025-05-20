from ...parser import Parser


class WhatsminerParser(Parser):
    def __init__(self, target: dict):
        super().__init__(target)
        self.target["algorithm"] = "SHA256"

    def parse_serial(self, obj: dict):
        msg = obj["Msg"]
        if "minersn" in msg and msg["minersn"]:
            self.target["serial"] = msg["minersn"]

    def parse_subtype(self, obj: dict):
        dev = obj["DEVDETAILS"][0]
        if "Model" in dev:
            self.target["subtype"] = dev["Model"]

    def parse_firmware(self, obj: dict):
        msg = obj["Msg"]
        if "fw_ver" in msg:
            self.target["firmware"] = msg["fw_ver"]

    def parse_platform(self, obj: dict):
        msg = obj["Msg"]
        if "platform" in msg:
            self.target["platform"] = msg["platform"]

    def parse_version_info(self, obj: dict):
        self.parse_firmware(obj)
        self.parse_platform(obj)
