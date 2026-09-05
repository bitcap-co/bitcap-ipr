# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import re

from pydantic import BaseModel

from mod.ipr_asic import MinerData, MinerFirmware, MinerType
from mod.ipr_asic.data import MinerAlgorithm
from mod.ipr_asic.schemas.antminer import MinerPool as AntminerPool
from mod.ipr_asic.schemas.antminer import MinerSummary as AntminerSummary
from mod.ipr_asic.schemas.antminer import SystemInfo as AntminerSystemInfo
from mod.ipr_asic.schemas.models import ContentResponse as AntminerLog


class AntminerModels(BaseModel):
    system_info: AntminerSystemInfo
    summary: AntminerSummary
    pools: list[AntminerPool]
    log: AntminerLog | None = None


class AntminerParser:
    def __init__(self) -> None:
        self.platform_patterns: dict[str, re.Pattern[str]] = {
            "Xilinx": re.compile(r"Zynq|Xilinx|xil"),
            "BeagleBone": re.compile(r"BeagleBone"),
            "AMLogic": re.compile(r"amlogic|aml"),
            "CVITEK": re.compile(r"cvitek|CVITEK"),
        }

    def parse(self, models: AntminerModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.ANTMINER
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        data.uptime = models.summary.elapsed
        data.subtype = models.system_info.minertype[9:]
        data.hostname = models.system_info.hostname
        data.mac = models.system_info.macaddr
        data.serial = models.system_info.serinum
        data.fw_version = models.system_info.system_filesystem_version

        algo = models.system_info.algorithm
        if algo is not None:
            data.algorithm = MinerAlgorithm.from_value(algo)

        if models.log is not None:
            models.log.text = models.log.text[0 : models.log.text.find("===")]
            for platform, pattern in self.platform_patterns.items():
                if pattern.search(models.log.text):
                    data.platform = platform
                    break

        for pool in models.pools:
            if pool.status == "Alive":
                data.stratum_url = pool.url
                if "." in pool.user:
                    user, worker = pool.user.split(".", 1)
                    data.username = user
                    data.worker_name = worker
                else:
                    data.username = pool.user
                break

        return data


# class AntminerParser(BaseParser):
#     def __init__(self) -> None:
#         super().__init__()
#         self.data.type = MinerType.ANTMINER
#         self.data.firmware = MinerFirmware.STOCK
#         self.ctrl_boards = {
#             "Xilinx": r"Zynq|Xilinx|xil",
#             "BeagleBone": r"BeagleBone",
#             "AMLogic": r"amlogic|aml",
#             "CVITEK": r"cvitek|CVITEK",
#         }

#     def parse_api_version(self, obj: dict[str, Any]) -> None:
#         return super().parse_api_version(obj)

#     def parse_uptime(self, obj: Any) -> None:
#         self.data.uptime = obj["Elapsed"]

#     def parse_hostname(self, obj: dict[str, Any]) -> None:
#         self.data.hostname = obj["hostname"]

#     def parse_mac(self, obj: Any) -> None:
#         self.data.mac = obj["macaddr"]

#     def parse_serial(self, obj: dict[str, Any]) -> None:
#         self.data.serial = obj["serinum"]

#     def parse_type(self, obj: Any) -> None:
#         return super().parse_type(obj)

#     def parse_subtype(self, obj: dict[str, Any]) -> None:
#         self.data.subtype = obj["minertype"][9:]

#     def parse_algorithm(self, obj: dict[str, Any]) -> None:
#         if "Algorithm" in obj:
#             self.data.algorithm = MinerAlgorithm.from_value(obj["Algorithm"])
#         else:
#             self.data.algorithm = MinerAlgorithm.SHA256

#     def parse_firmware(self, obj: dict[str, Any]) -> None:
#         self.data.fw_version = obj["system_filesystem_version"]

#     def parse_platform(self, obj: dict[str, Any]) -> None:
#         if "text" in obj:
#             obj["text"] = obj["text"][0 : obj["text"].find("===")]
#             for cb, pattern in self.ctrl_boards.items():
#                 if re.search(pattern, obj["text"]):
#                     self.data.platform = MinerPlatform.from_value(cb)
#                     break

#     def parse_system_info(self, obj: dict[str, Any]) -> None:
#         self.parse_hostname(obj)
#         self.parse_mac(obj)
#         self.parse_serial(obj)
#         self.parse_subtype(obj)
#         self.parse_algorithm(obj)
#         self.parse_firmware(obj)

#     def parse_summary(self, obj: Any) -> None:
#         self.parse_uptime(obj)

#     def parse_pools(self, obj: list[dict[str, Any]]) -> None:
#         for pool in obj:
#             if "Status" in pool and pool["Status"] == "Alive":
#                 self.data.stratum_url = pool["URL"]
#                 if "." in pool["User"]:
#                     user, worker = pool["User"].split(".", 1)
#                     self.data.username = user
#                     self.data.worker_name = worker
#                 else:
#                     self.data.username = pool["User"]
#                 break
