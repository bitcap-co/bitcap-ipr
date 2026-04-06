import re
from typing import Any

from mod.apiv2.data import (
    BaseParser,
    MinerAlgorithm,
    MinerFirmware,
    MinerPlatform,
    MinerType,
)


class AntminerParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.ANTMINER
        self.data.firmware = MinerFirmware.STOCK
        self.ctrl_boards = {
            "Xilinx": r"Zynq|Xilinx|xil",
            "BeagleBone": r"BeagleBone",
            "AMLogic": r"amlogic|aml",
            "CVITEK": r"cvitek|CVITEK",
        }

    def parse_api_version(self, obj: dict[str, Any]) -> None:
        return super().parse_api_version(obj)

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: dict[str, Any]) -> None:
        self.data.hostname = obj["hostname"]

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["macaddr"]

    def parse_serial(self, obj: dict[str, Any]) -> None:
        self.data.serial = obj["serinum"]

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: dict[str, Any]) -> None:
        self.data.subtype = obj["minertype"][9:]

    def parse_algorithm(self, obj: dict[str, Any]) -> None:
        if "Algorithm" in obj:
            self.data.algorithm = MinerAlgorithm.from_value(obj["Algorithm"])
        else:
            self.data.algorithm = MinerAlgorithm.SHA256

    def parse_firmware(self, obj: dict[str, Any]) -> None:
        self.data.fw_version = obj["system_filesystem_version"]

    def parse_platform(self, obj: dict[str, Any]) -> None:
        if "text" in obj:
            obj["text"] = obj["text"][0 : obj["text"].find("===")]
            for cb, pattern in self.ctrl_boards.items():
                if re.search(pattern, obj["text"]):
                    self.data.platform = MinerPlatform.from_value(cb)
                    break

    def parse_system_info(self, obj: dict[str, Any]) -> None:
        self.parse_hostname(obj)
        self.parse_mac(obj)
        self.parse_serial(obj)
        self.parse_subtype(obj)
        self.parse_algorithm(obj)
        self.parse_firmware(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if pool["status"] == "Alive":
                self.data.stratum_url = pool["url"]
                if "." in pool["user"]:
                    user, worker = pool["user"].split(".", 1)
                    self.data.username = user
                    self.data.worker_name = worker
                else:
                    self.data.username = pool["user"]
                break
