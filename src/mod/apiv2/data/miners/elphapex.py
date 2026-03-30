from typing import Any

from mod.apiv2.data import BaseParser, MinerAlgorithm, MinerFirmware, MinerType


class ElphapexParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.ELPHAPEX
        self.data.firmware = MinerFirmware.STOCK
        self.data.algo = MinerAlgorithm.SCRYPT

    def parse_api_version(self, obj: dict[str, Any]) -> None:
        return super().parse_api_version(obj)

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: dict[str, Any]) -> None:
        self.data.hostname = obj["hostname"]

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["macaddr"]

    def parse_serial(self, obj: dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: dict[str, Any]) -> None:
        self.data.subtype = obj["minertype"]

    def parse_algorithm(self, obj: Any) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: dict[str, Any]) -> None:
        self.data.fw_version = obj["system_filesystem_version"]

    def parse_platform(self, obj: dict[str, Any]) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: dict[str, Any]) -> None:
        self.parse_hostname(obj)
        self.parse_mac(obj)
        self.parse_subtype(obj)
        self.parse_firmware(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if pool["status"] == "Alive":
                self.data.active_pool = pool["url"]
                if "." in pool["user"]:
                    user, worker = pool["user"].split(".", 1)
                    self.data.active_user = user
                    self.data.active_worker = worker
                else:
                    self.data.active_user = pool["user"]
                break
