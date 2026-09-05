# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from pydantic import BaseModel

from mod.ipr_asic import MinerData
from mod.ipr_asic.data import MinerAlgorithm, MinerFirmware, MinerType
from mod.ipr_asic.schemas.goldshell import AlgoSettings as GoldshellAlgorithm
from mod.ipr_asic.schemas.goldshell import Devs as GoldshellSummary
from mod.ipr_asic.schemas.goldshell import MinerPool as GoldshellPool
from mod.ipr_asic.schemas.goldshell import Settings as GoldshellMinerConfig
from mod.ipr_asic.schemas.goldshell import Status as GoldshellSystemInfo


class GoldshellModels(BaseModel):
    system_info: GoldshellSystemInfo
    summary: GoldshellSummary
    miner_config: GoldshellMinerConfig
    algorithm: GoldshellAlgorithm
    pools: list[GoldshellPool]


class GoldshellParser:
    def parse(self, models: GoldshellModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.GOLDSHELL
        data.firmware = MinerFirmware.STOCK

        data.subtype = models.system_info.model
        # data.hostname = models.miner_config.name
        data.mac = models.miner_config.name
        data.fw_version = models.system_info.firmware
        data.algorithm = MinerAlgorithm.from_value(
            models.algorithm.algos[models.algorithm.algo_select].name
        )

        for pool in models.pools:
            if pool.active:
                data.stratum_url = pool.url
                if "." in pool.user:
                    user, worker = pool.user.split(".", 1)
                    data.username = user
                    data.worker_name = worker
                else:
                    data.username = pool.user
                break

        return data


# class GoldshellParser(BaseParser):
#     def __init__(self) -> None:
#         super().__init__()
#         self.data.type = MinerType.GOLDSHELL
#         self.data.firmware = MinerFirmware.STOCK

#     def parse_api_version(self, obj: dict[str, Any]) -> None:
#         return super().parse_api_version(obj)

#     def parse_uptime(self, obj: Any) -> None:
#         return super().parse_uptime(obj)

#     def parse_hostname(self, obj: dict[str, Any]) -> None:
#         return super().parse_hostname(obj)

#     def parse_mac(self, obj: Any) -> None:
#         self.data.mac = obj["name"]

#     def parse_serial(self, obj: dict[str, Any]) -> None:
#         return super().parse_serial(obj)

#     def parse_type(self, obj: Any) -> None:
#         return super().parse_type(obj)

#     def parse_subtype(self, obj: dict[str, Any]) -> None:
#         self.data.subtype = obj["model"]

#     def parse_algorithm(self, obj: dict[str, Any]) -> None:
#         self.data.algorithm = MinerAlgorithm.from_value(
#             obj["algos"][obj["algo_select"]]["name"]
#         )

#     def parse_firmware(self, obj: dict[str, Any]) -> None:
#         self.data.fw_version = obj["firmware"]

#     def parse_platform(self, obj: dict[str, Any]) -> None:
#         return super().parse_platform(obj)

#     def parse_system_info(self, obj: dict[str, Any]) -> None:
#         self.parse_subtype(obj)
#         self.parse_firmware(obj)

#     def parse_summary(self, obj: Any) -> None:
#         return super().parse_summary(obj)

#     def parse_pools(self, obj: list[dict[str, Any]]) -> None:
#         for pool in obj:
#             if pool["active"]:
#                 self.data.stratum_url = pool["url"]
#                 if "." in pool["user"]:
#                     user, worker = pool["user"].split(".", 1)
#                     self.data.username = user
#                     self.data.worker_name = worker
#                 else:
#                     self.data.username = pool["user"]
#                 break
