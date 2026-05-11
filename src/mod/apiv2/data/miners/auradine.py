from typing import Any

from mod.apiv2.data import BaseParser, MinerAlgorithm, MinerFirmware, MinerType


class AuradineParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.AURADINE
        self.data.firmware = MinerFirmware.STOCK
        self.data.algorithm = MinerAlgorithm.SHA256

    def parse_api_version(self, obj: Any) -> None:
        return super().parse_api_version(obj)

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: Any) -> None:
        self.data.hostname = obj["hostname"]

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["mac"]

    def parse_serial(self, obj: Any) -> None:
        self.data.serial = obj["ChassisSerialNo"]

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: Any) -> None:
        self.data.subtype = obj["model"]

    def parse_algorithm(self, obj: Any) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Any) -> None:
        self.data.fw_version = obj["version"]

    def parse_platform(self, obj: Any) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: Any) -> None:
        self.parse_hostname(obj)
        self.parse_mac(obj)
        self.parse_serial(obj)
        self.parse_subtype(obj)
        self.parse_firmware(obj)

    def parse_pools(self, obj: list[dict]) -> None:
        for pool in obj:
            if pool["Status"] == "Alive":
                self.data.stratum_url = pool["URL"]
                if "." in pool["User"]:
                    user, worker = pool["User"].split(".", 1)
                    self.data.username = user
                    self.data.worker_name = worker
                else:
                    self.data.username = pool["User"]
                break
