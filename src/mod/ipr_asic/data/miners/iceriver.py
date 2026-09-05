# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from pydantic import BaseModel

from mod.ipr_asic import MinerData
from mod.ipr_asic.data import MinerAlgorithm, MinerFirmware, MinerType
from mod.ipr_asic.schemas.iceriver import MinerPool as IceriverPool
from mod.ipr_asic.schemas.iceriver import UserPanel as IceriverSummary


class IceriverModels(BaseModel):
    summary: IceriverSummary
    pools: list[IceriverPool]


class IceriverParser:
    def parse(self, models: IceriverModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.ICERIVER
        data.firmware = MinerFirmware.STOCK

        uptime_str = models.summary.runtime
        days, hours, mins, secs = map(int, uptime_str.split(":"))
        uptime = days * 86400 + hours * 3600 + mins * 60 + secs
        data.uptime = uptime

        if models.summary.model == "none":
            slug = models.summary.softver1
            split_ver = slug.split("_")
            if split_ver[-1] == "miner":
                model_ver = split_ver[-2]
            else:
                model_ver = split_ver[-1].replace("miner", "")
            match model_ver:
                case "10306":
                    data.subtype = "AL3"
                case "11304":
                    data.subtype = "KS7"
                case _:
                    data.subtype = model_ver.upper()
        else:
            data.subtype = models.summary.model

        data.hostname = models.summary.host
        data.mac = models.summary.mac
        data.fw_version = models.summary.softver1

        data.algorithm = None
        algo = models.summary.algo
        if algo != "none":
            data.algorithm = MinerAlgorithm.from_value(algo)
        elif data.subtype:
            if data.subtype == "AL3":
                data.algorithm = MinerAlgorithm.BLAKE3
            elif data.subtype.__contains__("KS"):
                data.algorithm = MinerAlgorithm.KHEAVYHASH

        for pool in models.pools:
            if pool.connect == 1:
                data.stratum_url = pool.addr
                if "." in pool.user:
                    user, worker = pool.user.split(".", 1)
                    data.username = user
                    data.worker_name = worker
                else:
                    data.username = pool.user
                break

        return data


# class IceriverParser(BaseParser):
#     def __init__(self) -> None:
#         super().__init__()
#         self.data.type = MinerType.ICERIVER
#         self.data.firmware = MinerFirmware.STOCK

#     def parse_api_version(self, obj: dict[str, Any]) -> None:
#         return super().parse_api_version(obj)

#     def parse_uptime(self, obj: Any) -> None:
#         uptime_str = obj["runtime"]
#         days, hours, mins, secs = map(int, uptime_str.split(":"))
#         uptime = days * 86400 + hours * 3600 + mins * 60 + secs
#         self.data.uptime = uptime

#     def parse_hostname(self, obj: dict[str, Any]) -> None:
#         self.data.hostname = obj["host"]

#     def parse_mac(self, obj: Any) -> None:
#         self.data.mac = obj["mac"]

#     def parse_serial(self, obj: dict[str, Any]) -> None:
#         return super().parse_serial(obj)

#     def parse_type(self, obj: Any) -> None:
#         return super().parse_type(obj)

#     def parse_subtype(self, obj: dict[str, Any]) -> None:
#         if obj["model"] == "none":
#             slug: str = obj["softver1"]
#             split_ver = slug.split("_")
#             if split_ver[-1] == "miner":
#                 model_ver = split_ver[-2]
#             else:
#                 model_ver = split_ver[-1].replace("miner", "")
#             match model_ver:
#                 case "10306":
#                     self.data.subtype = "AL3"
#                 case "11304":
#                     self.data.subtype = "KS7"
#                 case _:
#                     self.data.subtype = model_ver.upper()
#         else:
#             self.data.subtype = obj["model"]

#     def parse_algorithm(self, obj: dict[str, Any]) -> None:
#         if obj["algo"] != "none":
#             self.data.algorithm = MinerAlgorithm.from_value(obj["algo"])
#         elif self.data.subtype is not None:
#             if self.data.subtype == "AL3":
#                 self.data.algorithm = MinerAlgorithm.BLAKE3
#             elif self.data.subtype.__contains__("KS"):
#                 self.data.algorithm = MinerAlgorithm.KHEAVYHASH
#             else:
#                 self.data.algorithm = None
#         else:
#             self.data.algorithm = None

#     def parse_firmware(self, obj: dict[str, Any]) -> None:
#         self.data.fw_version = obj["softver1"]

#     def parse_platform(self, obj: dict[str, Any]) -> None:
#         return super().parse_platform(obj)

#     def parse_system_info(self, obj: dict[str, Any]) -> None:
#         return super().parse_system_info(obj)

#     def parse_summary(self, obj: Any) -> None:
#         self.parse_uptime(obj)

#     def parse_pools(self, obj: list[dict[str, Any]]) -> None:
#         for pool in obj:
#             if pool["connect"] == 1:
#                 self.data.stratum_url = pool["addr"]
#                 if "." in pool["user"]:
#                     user, worker = pool["user"].split(".", 1)
#                     self.data.username = user
#                     self.data.worker_name = worker
#                 else:
#                     self.data.username = pool["user"]
#                 break
