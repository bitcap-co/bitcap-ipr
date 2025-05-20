import re
from ...parser import Parser


class BitmainParser(Parser):
    def __init__(self, target: dict):
        super().__init__(target)
        self.target["algorithm"] = "sha256d"
        self.ctrl_boards = {
            "xil": r"Zynq|Xilinx|xil",
            "bb": r"BeagleBone",
            "aml": r"amlogic|aml",
            "cv": r"cvitek|CVITEK",
        }

    def parse_serial(self, obj: dict) -> None:
        for k in obj.keys():
            if k in ["serial", "serinum"]:
                self.target["serial"] = obj[k]
                break

    def parse_subtype(self, obj: dict) -> None:
        for k in obj.keys():
            if k in ["miner", "minertype"]:
                self.target["subtype"] = obj[k][9:]
                break

    def parse_algorithm(self, obj: dict):
        for k in obj.keys():
            if k in ["algorithm", "Algorithm"]:
                self.target["algorithm"] = obj[k]

    def parse_firmware(self, obj: dict):
        if "fw_name" in obj:
            self.target["firmware"] = f"{obj['fw_name']} {obj['fw_version']}"
        elif "system_filesystem_version" in obj:
            self.target["firmware"] = obj["system_filesystem_version"]

    def parse_platform(self, obj: dict):
        if "platform" in obj:
            self.target["platform"] = obj["platform"]
        elif "plaintext" in obj:
            for cb, pattern in self.ctrl_boards.items():
                if re.search(pattern, obj["plaintext"]):
                    self.target["platform"] = cb
                    break

    def parse_system_info(self, obj: dict):
        self.parse_algorithm(obj)
        self.parse_firmware(obj)
        self.parse_subtype(obj)
        self.parse_serial(obj)
