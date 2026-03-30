from typing import Any

from mod.apiv2.data import BaseParser, MinerAlgorithm, MinerFirmware, MinerType


class IceriverParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.ICERIVER
        self.data.firmware = MinerFirmware.STOCK

    def parse_api_version(self, obj: dict[str, Any]) -> None:
        return super().parse_api_version(obj)

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: dict[str, Any]) -> None:
        self.data.hostname = obj["host"]

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["mac"]

    def parse_serial(self, obj: dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: dict[str, Any]) -> None:
        if obj["model"] == "none":
            slug: str = obj["softver1"]
            split_ver = slug.split("_")
            if split_ver[-1] == "miner":
                model_ver = split_ver[-2]
            else:
                model_ver = split_ver[-1].replace("miner", "")
            match model_ver:
                case "10306":
                    self.data.subtype = "AL3"
                case "11304":
                    self.data.subtype = "KS7"
                case _:
                    self.data.subtype = model_ver.upper()
        else:
            self.data.subtype = obj["model"]

    def parse_algorithm(self, obj: dict[str, Any]) -> None:
        if not obj["algo"] == "none":
            self.data.algo = MinerAlgorithm.from_value(obj["algo"])
        elif self.data.subtype is not None:
            if self.data.subtype == "AL3":
                self.data.algo = MinerAlgorithm.BLAKE3
            elif self.data.subtype.__contains__("KS"):
                self.data.algo = MinerAlgorithm.KHEAVYHASH
            else:
                self.data.algo = None
        else:
            self.data.algo = None

    def parse_firmware(self, obj: dict[str, Any]) -> None:
        self.data.fw_version = obj["softver1"]

    def parse_platform(self, obj: dict[str, Any]) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: dict[str, Any]) -> None:
        return super().parse_system_info(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if pool["connect"] == 1:
                self.data.active_pool = pool["addr"]
                if "." in pool["user"]:
                    user, worker = pool["user"].split(".", 1)
                    self.data.active_user = user
                    self.data.active_worker = worker
                else:
                    self.data.active_user = pool["user"]
                break
