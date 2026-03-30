from typing import Any

from .. import MinerAlgorithm, MinerFirmware, MinerPlatform, MinerType
from .base import BaseParser


class VnishParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.ANTMINER
        self.data.firmware = MinerFirmware.VNISH

    def parse_api_version(self, obj: Any) -> None:
        return super().parse_api_version(obj)

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: Any) -> None:
        self.data.hostname = obj["system"]["network_status"]["hostname"]

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["system"]["network_status"]["mac"]

    def parse_serial(self, obj: Any) -> None:
        self.data.serial = obj["serial"]

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: Any) -> None:
        if "model" in obj:
            self.data.subtype = obj["model"].upper()
        elif "miner" in obj:
            self.data.subtype = obj["miner"].split(" ")[-1]

    def parse_algorithm(self, obj: Any) -> None:
        self.data.algo = MinerAlgorithm.from_value(obj["algorithm"])

    def parse_firmware(self, obj: Any) -> None:
        self.data.fw_version = obj["fw_version"]

    def parse_platform(self, obj: Any) -> None:
        match obj["platform"]:
            case "xil":
                self.data.platform = MinerPlatform.XILINX
            case "bb":
                self.data.platform = MinerPlatform.BEAGLEBONE
            case "aml":
                self.data.platform = MinerPlatform.AMLOGIC
            case "cv":
                self.data.platform = MinerPlatform.CVITEK
            case "stm":
                self.data.platform = MinerPlatform.STM
            case _:
                self.data.platform = None

    def parse_system_info(self, obj: Any) -> None:
        return super().parse_system_info(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if pool["status"] == "active":
                self.data.active_pool = pool["url"]
                if "." in pool["user"]:
                    user, worker = pool["user"].split(".", 1)
                    self.data.active_user = user
                    self.data.active_worker = worker
                else:
                    self.data.active_user = pool["user"]
                break
