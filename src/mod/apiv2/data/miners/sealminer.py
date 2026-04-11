# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import Any

from mod.apiv2.data import BaseParser, MinerAlgorithm, MinerFirmware, MinerType


class SealminerParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.SEALMINER
        self.data.firmware = MinerFirmware.STOCK
        self.data.algorithm = MinerAlgorithm.SHA256

    def parse_api_version(self, obj: dict[str, Any]) -> None:
        return super().parse_api_version(obj)

    def parse_uptime(self, obj: Any) -> None:
        return super().parse_uptime(obj)

    def parse_hostname(self, obj: dict[str, Any]) -> None:
        return super().parse_hostname(obj)

    def parse_mac(self, obj: Any) -> None:
        self.data.mac = obj["macaddr"]

    def parse_serial(self, obj: dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: dict[str, Any]) -> None:
        self.data.subtype = obj["miner_type"]

    def parse_algorithm(self, obj: dict[str, Any]) -> None:
        return super().parse_algorithm(obj)

    def parse_firmware(self, obj: dict[str, Any]) -> None:
        self.data.fw_version = obj["firmware_version"]

    def parse_platform(self, obj: dict[str, Any]) -> None:
        self.data.platform = obj["ctrl_version"]

    def parse_system_info(self, obj: dict[str, Any]) -> None:
        return super().parse_system_info(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if pool["isActive"]:
                self.data.stratum_url = pool["url"]
                if "." in pool["user"]:
                    user, worker = pool["user"].split(".", 1)
                    self.data.username = user
                    self.data.worker_name = worker
                else:
                    self.data.username = pool["user"]
                break
