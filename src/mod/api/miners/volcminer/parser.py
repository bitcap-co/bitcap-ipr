from ...parser import Parser


class VolcminerParser(Parser):
    def __init__(self, target: dict):
        super().__init__(target)
        self.target["algorithm"] = "SCRYPT"

    def parse_subtype(self, obj: dict):
        if "minertype" in obj:
            self.target["subtype"] = obj["minertype"][10:]

    def parse_firmware(self, obj: dict):
        if "system_filesystem_version" in obj:
            self.target["firmware"] = obj["system_filesystem_version"]

    def parse_all(self, obj: dict):
        self.parse_subtype(obj)
        self.parse_firmware(obj)
