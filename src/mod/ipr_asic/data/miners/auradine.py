from pydantic import BaseModel

from mod.ipr_asic import MinerData
from mod.ipr_asic.data import MinerAlgorithm, MinerFirmware, MinerType
from mod.ipr_asic.schemas.auradine import IPReport as AuradineSystemInfo
from mod.ipr_asic.schemas.auradine import Pool as AuradinePool
from mod.ipr_asic.schemas.auradine import Summary as AuradineSummary


class AuradineModels(BaseModel):
    system_info: AuradineSystemInfo
    summary: AuradineSummary
    pools: list[AuradinePool]


class AuradineParser:
    def parse(self, models: AuradineModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.AURADINE
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        data.uptime = models.summary.elapsed
        data.subtype = models.system_info.model
        data.hostname = models.system_info.hostname
        data.mac = models.system_info.mac
        data.serial = models.system_info.chassis_serial
        data.fw_version = models.system_info.version

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


# class AuradineParser(BaseParser):
#     def __init__(self) -> None:
#         super().__init__()
#         self.data.type = MinerType.AURADINE
#         self.data.firmware = MinerFirmware.TOCK
#         self.data.algorithm = MinerAlgorithm.SHA256

#     def parse_api_version(self, obj: Any) -> None:
#         return super().parse_api_version(obj)

#     def parse_uptime(self, obj: Any) -> None:
#         self.data.uptime = obj["Elapsed"]

#     def parse_hostname(self, obj: Any) -> None:
#         self.data.hostname = obj["hostname"]

#     def parse_mac(self, obj: Any) -> None:
#         self.data.mac = obj["mac"]

#     def parse_serial(self, obj: Any) -> None:
#         self.data.serial = obj["ChassisSerialNo"]

#     def parse_type(self, obj: Any) -> None:
#         return super().parse_type(obj)

#     def parse_subtype(self, obj: Any) -> None:
#         self.data.subtype = obj["model"]

#     def parse_algorithm(self, obj: Any) -> None:
#         return super().parse_algorithm(obj)

#     def parse_firmware(self, obj: Any) -> None:
#         self.data.fw_version = obj["version"]

#     def parse_platform(self, obj: Any) -> None:
#         return super().parse_platform(obj)

#     def parse_system_info(self, obj: Any) -> None:
#         self.parse_hostname(obj)
#         self.parse_mac(obj)
#         self.parse_serial(obj)
#         self.parse_subtype(obj)
#         self.parse_firmware(obj)

#     def parse_summary(self, obj: Any) -> None:
#         self.parse_uptime(obj)

#     def parse_pools(self, obj: list[dict]) -> None:
#         for pool in obj:
#             if pool["Status"] == "Alive":
#                 self.data.stratum_url = pool["URL"]
#                 if "." in pool["User"]:
#                     user, worker = pool["User"].split(".", 1)
#                     self.data.username = user
#                     self.data.worker_name = worker
#                 else:
#                     self.data.username = pool["User"]
#                 break
