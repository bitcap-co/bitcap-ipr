from typing import Any

from mod.apiv2.data import BaseParser, MinerAlgorithm, MinerFirmware, MinerType


class GoldshellParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.GOLDSHELL
        self.data.firmware = MinerFirmware.STOCK

    def parse_api_version(self, obj: dict[str, Any]) -> None:
        return super().parse_api_version(obj)

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: dict[str, Any]) -> None:
        return super().parse_hostname(obj)

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["name"]

    def parse_serial(self, obj: dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: dict[str, Any]) -> None:
        self.data.subtype = obj["model"]

    def parse_algorithm(self, obj: dict[str, Any]) -> None:
        self.data.algorithm = MinerAlgorithm.from_value(
            obj["algos"][obj["algo_select"]]["name"]
        )

    def parse_firmware(self, obj: dict[str, Any]) -> None:
        self.data.fw_version = obj["firmware"]

    def parse_platform(self, obj: dict[str, Any]) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: dict[str, Any]) -> None:
        self.parse_mac(obj)
        self.parse_subtype(obj)
        self.parse_firmware(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if pool["active"]:
                self.data.stratum_url = pool["url"]
                if "." in pool["user"]:
                    user, worker = pool["user"].split(".", 1)
                    self.data.username = user
                    self.data.worker_name = worker
                else:
                    self.data.username = pool["user"]
                break
