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
        return super().parse_hostname(obj)

    def parse_mac(self, obj: Any) -> None:
        return super().parse_mac(obj)

    def parse_serial(self, obj: Any) -> None:
        return super().parse_serial(obj)

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: Any) -> None:
        return super().parse_subtype(obj)

    def parse_algorithm(self, obj: Any) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: Any) -> None:
        return super().parse_firmware(obj)

    def parse_platform(self, obj: Any) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: Any) -> None:
        return super().parse_system_info(obj)

    def parse_pools(self, obj: list[dict]) -> None:
        return super().parse_pools(obj)
