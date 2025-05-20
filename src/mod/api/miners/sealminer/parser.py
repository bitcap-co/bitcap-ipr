from ...parser import Parser


class SealminerParser(Parser):
    def __init__(self, target: dict):
        super().__init__(target)
        self.target["algorithm"] = "SHA256"

    def parse_subtype(self, obj: dict) -> None:
        if "miner_type" in obj:
            self.target["subtype"] = obj["miner_type"]

    def parse_firmware(self, obj: dict) -> None:
        if "firmware_version" in obj:
            self.target["firmware"] = obj["firmware_version"]

    def parse_platform(self, obj: dict) -> None:
        if "ctrl_version" in obj:
            self.target["platform"] = obj["ctrl_version"]

    def parse_all(self, obj: dict) -> None:
        self.parse_subtype(obj)
        self.parse_firmware(obj)
        self.parse_platform(obj)
