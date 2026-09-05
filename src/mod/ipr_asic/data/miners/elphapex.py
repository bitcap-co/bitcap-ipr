# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from pydantic import BaseModel

from mod.ipr_asic import MinerData
from mod.ipr_asic.data import MinerAlgorithm, MinerFirmware, MinerType
from mod.ipr_asic.schemas.antminer import SystemInfo as ElphapexSystemInfo
from mod.ipr_asic.schemas.elphapex import MinerPool as ElphapexPool
from mod.ipr_asic.schemas.elphapex import MinerSummary as ElphapexSummary


class ElphapexModels(BaseModel):
    system_info: ElphapexSystemInfo
    summary: ElphapexSummary
    pools: list[ElphapexPool]


class ElphapexParser:
    def parse(self, models: ElphapexModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.ELPHAPEX
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SCRYPT

        data.uptime = models.summary.elapsed
        data.subtype = models.system_info.minertype
        data.hostname = models.system_info.hostname
        data.mac = models.system_info.macaddr
        data.fw_version = models.system_info.system_filesystem_version

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


#     def parse_api_version(self, obj: dict[str, Any]) -> None:
#         return super().parse_api_version(obj)

#     def parse_uptime(self, obj: Any) -> None:
#         self.data.uptime = obj["SUMMARY"][0]["elapsed"]

#     def parse_hostname(self, obj: dict[str, Any]) -> None:
#         self.data.hostname = obj["hostname"]

#     def parse_mac(self, obj: Any) -> None:
#         self.data.mac = obj["macaddr"]

#     def parse_serial(self, obj: dict[str, Any]) -> None:
#         return super().parse_serial(obj)

#     def parse_type(self, obj: Any) -> None:
#         return super().parse_type(obj)

#     def parse_subtype(self, obj: dict[str, Any]) -> None:
#         self.data.subtype = obj["minertype"]

#     def parse_algorithm(self, obj: Any) -> None:
#         return super().parse_algorithm(obj)

#     def parse_firmware(self, obj: dict[str, Any]) -> None:
#         self.data.fw_version = obj["system_filesystem_version"]

#     def parse_platform(self, obj: dict[str, Any]) -> None:
#         return super().parse_platform(obj)

#     def parse_system_info(self, obj: dict[str, Any]) -> None:
#         self.parse_hostname(obj)
#         self.parse_mac(obj)
#         self.parse_subtype(obj)
#         self.parse_firmware(obj)

#     def parse_summary(self, obj: Any) -> None:
#         self.parse_uptime(obj)

#     def parse_pools(self, obj: list[dict[str, Any]]) -> None:
#         for pool in obj:
#             if pool["status"] == "Alive":
#                 self.data.stratum_url = pool["url"]
#                 if "." in pool["user"]:
#                     user, worker = pool["user"].split(".", 1)
#                     self.data.username = user
#                     self.data.worker_name = worker
#                 else:
#                     self.data.username = pool["user"]
#                 break
