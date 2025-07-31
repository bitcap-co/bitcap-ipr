import re
from typing import Any, Dict

from ...parser import Parser


class BitmainParser(Parser):
    def __init__(self, target: Dict[str, str]):
        super().__init__(target)
        self.target["algorithm"] = "sha256d"
        self.ctrl_boards = {
            "xil": r"Zynq|Xilinx|xil",
            "bb": r"BeagleBone",
            "aml": r"amlogic|aml",
            "cv": r"cvitek|CVITEK",
        }

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        for k in obj.keys():
            if k in ["serial", "serinum"]:
                self.target["serial"] = obj[k]
                break

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        for k in obj.keys():
            if k in ["miner", "minertype"]:
                self.target["subtype"] = obj[k][9:]
                break

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        for k in obj.keys():
            if k in ["algorithm", "Algorithm"]:
                self.target["algorithm"] = obj[k]

    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        if "fw_name" in obj:
            self.target["firmware"] = f"{obj['fw_name']} {obj['fw_version']}"
        elif "system_filesystem_version" in obj:
            self.target["firmware"] = obj["system_filesystem_version"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        if "platform" in obj:
            self.target["platform"] = obj["platform"]
        elif "plaintext" in obj:
            for cb, pattern in self.ctrl_boards.items():
                if re.search(pattern, obj["plaintext"]):
                    self.target["platform"] = cb
                    break

    def parse_pools(self, obj: Dict[str, Any]) -> None:
        if "POOLS" in obj:
            pools = obj["POOLS"]
        elif "miner" in obj:
            pools = obj["miner"]["pools"]
        for pool in pools:
            if pool["status"] == "active" or pool["status"] == "Alive":
                self.target["pool"] = pool["url"]
                self.target["worker"] = pool["user"]
                break

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        self.parse_algorithm(obj)
        self.parse_firmware(obj)
        self.parse_subtype(obj)
        self.parse_serial(obj)
