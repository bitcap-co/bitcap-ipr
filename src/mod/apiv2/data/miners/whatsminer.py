from typing import Any

from .. import MinerAlgorithm, MinerFirmware, MinerType
from .base import BaseParser


class WhatsminerParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.WHATSMINER
        self.data.firmware = MinerFirmware.STOCK
        self.data.algo = MinerAlgorithm.SHA256

    def parse_api_version(self, obj: dict[str, Any]) -> None:
        self.data.api_version = obj["api_ver"]

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: dict[str, Any]) -> None:
        self.data.hostname = obj["hostname"]

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["mac"]

    def parse_serial(self, obj: dict[str, Any]) -> None:
        self.data.serial = obj["minersn"]

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: list[dict]) -> None:
        dev = obj[0]
        self.data.subtype = dev["Model"]

    def parse_algorithm(self, obj: Any) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Any) -> None:
        self.data.fw_version = obj["fw_ver"]

    def parse_platform(self, obj: Any) -> None:
        self.data.platform = obj["platform"]

    def parse_system_info(self, obj: Any) -> None:
        self.parse_hostname(obj)
        self.parse_mac(obj)
        self.parse_serial(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if pool["Status"] == "Alive":
                self.data.active_pool = pool["URL"]
                if "." in pool["User"]:
                    user, worker = pool["User"].split(".", 1)
                    self.data.active_user = user
                    self.data.active_worker = worker
                else:
                    self.data.active_user = pool["User"]
                break

    def parse_version_info(self, obj: dict[str, Any]) -> None:
        self.parse_api_version(obj)
        self.parse_firmware(obj)
        self.parse_platform(obj)


class WhatsminerV3Parser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.WHATSMINER
        self.data.firmware = MinerFirmware.STOCK
        self.data.algo = MinerAlgorithm.SHA256

    def parse_api_version(self, obj: Any) -> None:
        self.data.api_version = obj["system"]["api"]

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: Any) -> None:
        self.data.hostname = obj["network"]["hostname"]

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["network"]["mac"]

    def parse_serial(self, obj: Any) -> None:
        self.data.serial = obj["miner"]["miner-sn"]

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: Any) -> None:
        self.data.subtype = obj["miner"]["type"]

    def parse_algorithm(self, obj: Any) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Any) -> None:
        self.data.fw_version = obj["system"]["fwversion"]

    def parse_platform(self, obj: Any) -> None:
        self.data.platform = obj["system"]["platform"]

    def parse_system_info(self, obj: Any) -> None:
        self.parse_api_version(obj)
        self.parse_hostname(obj)
        self.parse_mac(obj)
        self.parse_platform(obj)
        self.parse_firmware(obj)
        self.parse_serial(obj)
        self.parse_subtype(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if pool["status"] == "alive":
                self.data.active_pool = pool["url"]
                if "." in pool["account"]:
                    user, worker = pool["account"].split(".", 1)
                    self.data.active_user = user
                    self.data.active_worker = worker
                else:
                    self.data.active_user = pool["account"]
                break
