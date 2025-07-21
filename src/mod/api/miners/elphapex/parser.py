from ...parser import Parser


class ElphapexParser(Parser):
    def __init__(self, target: dict):
        super().__init__(target)

    def parse_subtype(self, obj: dict):
        if "minertype" in obj:
            self.target["subtype"] = obj["minertype"]

    def parse_algorithm(self, obj: dict):
        if "Algorithm" in obj:
            self.target["algorithm"] = obj["Algorithm"]

    def parse_firmware(self, obj: dict):
        if "system_filesystem_version" in obj:
            self.target["firmware"] = obj["system_filesystem_version"]

    def parse_platform(self, obj:dict):
        if "INFO" in obj:
            if "hw_version" in obj["INFO"]:
                self.target["platform"] = obj["INFO"]["hw_version"]

    def parse_system_info(self, obj: dict):
        self.parse_subtype(obj)
        self.parse_firmware(obj)
        self.parse_algorithm(obj)
