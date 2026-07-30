from typing import Any

from mod.ipr_asic.data import BaseParser, MinerAlgorithm, MinerFirmware, MinerType


class IPolloParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.IPOLLO
        self.data.firmware = MinerFirmware.STOCK

    def parse_api_version(self, obj: dict[str, Any]) -> None:
        return super().parse_api_version(obj)

    def parse_uptime(self, obj: Any) -> None:
        self.data.uptime = obj["uptime"]

    def parse_hostname(self, obj: dict[str, Any]) -> None:
        return super().parse_hostname(obj)

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj[0]["macaddr"]

    def parse_serial(self, obj: dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: dict[str, Any]) -> None:
        if self.data.algorithm == MinerAlgorithm.CUCKATOO:
            self.data.subtype = "G1"

    def parse_algorithm(self, obj: dict[str, Any]) -> None:
        algo = obj["algo"]
        if algo == "mwc" or algo == "grin":
            self.data.algorithm = MinerAlgorithm.CUCKATOO
        else:
            self.data.algorithm = MinerAlgorithm.from_value(algo)

    def parse_firmware(self, obj: dict[str, Any]) -> None:
        self.data.fw_version = obj["version"]

    def parse_platform(self, obj: dict[str, Any]) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: dict[str, Any]) -> None:
        self.parse_uptime(obj)

    def parse_summary(self, obj: Any) -> None:
        self.parse_algorithm(obj)
        self.parse_subtype(obj)
        self.parse_firmware(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        # stratum+tcp://mwc.2miners.com:7575,PING=152.83 ms
        self.data.stratum_url = obj[0]["url"].split(",")[0]
        if "." in obj[0]["user"]:
            user, worker = obj[0]["user"].split(".", 1)
            self.data.username = user
            self.data.worker_name = worker
        else:
            self.data.username = obj[0]["user"]
