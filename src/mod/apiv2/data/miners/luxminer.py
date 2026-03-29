from typing import Any

from apiv2.data import MinerFirmware, MinerPlatform, MinerType
from apiv2.data.miners.base import BaseParser


class LuxminerParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.ANTMINER
        self.data.firmware = MinerFirmware.LUX_OS

    def parse_api_version(self, obj: Any) -> None:
        self.data.api_version = obj["API"]

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: Any) -> None:
        self.data.hostname = obj["Hostname"]

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["MACAddr"]

    def parse_serial(self, obj: Any) -> None:
        self.data.serial = obj["SerialNumber"]

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: Any) -> None:
        self.data.subtype = obj["Model"]

    def parse_algorithm(self, obj: Any) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Any) -> None:
        self.data.fw_version = obj["LUXMiner"]

    def parse_platform(self, obj: Any) -> None:
        self.data.platform = MinerPlatform.from_value(obj["ControlBoardType"])

    def parse_system_info(self, obj: Any) -> None:
        self.parse_hostname(obj)
        self.parse_mac(obj)
        self.parse_serial(obj)
        self.parse_subtype(obj)
        self.parse_platform(obj)

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
