from pydantic import BaseModel

from mod.ipr_asic import MinerData
from mod.ipr_asic.data import MinerAlgorithm, MinerFirmware, MinerType
from mod.ipr_asic.schemas.ipollo import MinerPool as IpolloPool
from mod.ipr_asic.schemas.ipollo import MinerStatus as IpolloSummary
from mod.ipr_asic.schemas.ipollo import NetworkInfo as IpolloNetworkInfo
from mod.ipr_asic.schemas.ipollo import SystemInfo as IpolloSystemInfo


class IPolloModels(BaseModel):
    system_info: IpolloSystemInfo
    summary: IpolloSummary
    pools: list[IpolloPool]
    network_info: IpolloNetworkInfo


class IPolloParser:
    def parse(self, models: IPolloModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.IPOLLO
        data.firmware = MinerFirmware.STOCK

        data.uptime = models.system_info.uptime
        for iface in models.network_info.ifaces:
            if iface.is_up:
                data.hostname = iface.name
                data.mac = iface.macaddr
                break
        data.fw_version = models.summary.version

        data.algorithm = None
        algo = models.summary.algo
        if algo:
            if algo == "mwc" or algo == "grin":
                data.algorithm = MinerAlgorithm.CUCKATOO
            else:
                data.algorithm = MinerAlgorithm.from_value(algo)

        if data.algorithm is MinerAlgorithm.CUCKATOO:
            data.subtype = "G1"

        # no active indicator, use first pool
        pool = models.pools[0]
        # stratum+tcp://mwc.2miners.com:7575,PING=152.83 ms; chop off ping
        data.stratum_url = pool.url.split(",")[0]
        if "." in pool.user:
            user, worker = pool.user.split(".", 1)
            data.username = user
            data.worker_name = worker
        else:
            data.username = pool.user

        return data


# class IPolloParser(BaseParser):
#     def __init__(self) -> None:
#         super().__init__()
#         self.data.type = MinerType.IPOLLO
#         self.data.firmware = MinerFirmware.STOCK

#     def parse_api_version(self, obj: dict[str, Any]) -> None:
#         return super().parse_api_version(obj)

#     def parse_uptime(self, obj: Any) -> None:
#         self.data.uptime = obj["uptime"]

#     def parse_hostname(self, obj: dict[str, Any]) -> None:
#         return super().parse_hostname(obj)

#     def parse_mac(self, obj: Any) -> None:
#         self.data.mac = obj[0]["macaddr"]

#     def parse_serial(self, obj: dict[str, Any]) -> None:
#         return super().parse_serial(obj)

#     def parse_type(self, obj: Any) -> None:
#         return super().parse_type(obj)

#     def parse_subtype(self, obj: dict[str, Any]) -> None:
#         if self.data.algorithm == MinerAlgorithm.CUCKATOO:
#             self.data.subtype = "G1"

#     def parse_algorithm(self, obj: dict[str, Any]) -> None:
#         algo = obj["algo"]
#         if algo == "mwc" or algo == "grin":
#             self.data.algorithm = MinerAlgorithm.CUCKATOO
#         else:
#             self.data.algorithm = MinerAlgorithm.from_value(algo)

#     def parse_firmware(self, obj: dict[str, Any]) -> None:
#         self.data.fw_version = obj["version"]

#     def parse_platform(self, obj: dict[str, Any]) -> None:
#         return super().parse_platform(obj)

#     def parse_system_info(self, obj: dict[str, Any]) -> None:
#         self.parse_uptime(obj)

#     def parse_summary(self, obj: Any) -> None:
#         self.parse_algorithm(obj)
#         self.parse_subtype(obj)
#         self.parse_firmware(obj)

#     def parse_pools(self, obj: list[dict[str, Any]]) -> None:
#         # stratum+tcp://mwc.2miners.com:7575,PING=152.83 ms
#         self.data.stratum_url = obj[0]["url"].split(",")[0]
#         if "." in obj[0]["user"]:
#             user, worker = obj[0]["user"].split(".", 1)
#             self.data.username = user
#             self.data.worker_name = worker
#         else:
#             self.data.username = obj[0]["user"]
