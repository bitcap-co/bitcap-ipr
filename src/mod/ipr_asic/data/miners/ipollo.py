from pydantic import BaseModel

from mod.ipr_asic.data import MinerAlgorithm, MinerData, MinerFirmware, MinerType
from mod.ipr_asic.schemas.ipollo import MinerPool as IpolloPool
from mod.ipr_asic.schemas.ipollo import MinerStatus as IpolloSummary
from mod.ipr_asic.schemas.ipollo import NetworkInfo as IpolloNetworkInfo
from mod.ipr_asic.schemas.ipollo import SystemInfo as IpolloSystemInfo


class IPolloModels(BaseModel):
    system_info: IpolloSystemInfo | None = None
    summary: IpolloSummary | None = None
    pools: list[IpolloPool] | None = None
    network_info: IpolloNetworkInfo | None = None


class IPolloParser:
    def parse(self, models: IPolloModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.IPOLLO
        data.firmware = MinerFirmware.STOCK

        if models.system_info is not None:
            data.uptime = models.system_info.uptime
            if models.network_info is not None:
                lan_iface = models.system_info.wan.ifname
                for iface in models.network_info.ifaces.root:
                    if iface.name == lan_iface:
                        data.mac = iface.macaddr
                        break

        if models.summary is not None:
            data.fw_version = models.summary.version
            algo = models.summary.algo
            if algo:
                if algo == "mwc" or algo == "grin":
                    data.algorithm = MinerAlgorithm.CUCKATOO
                else:
                    data.algorithm = MinerAlgorithm.from_value(algo)

        if data.algorithm is MinerAlgorithm.CUCKATOO:
            data.subtype = "G1"

        # Miner status returns the active pool.
        if models.pools:
            pool = models.pools[0]
            # Chop the trailing ping from values such as "url,PING=152.83 ms".
            data.stratum_url = pool.url.split(",")[0]
            if "." in pool.user:
                user, worker = pool.user.split(".", 1)
                data.username = user
                data.worker_name = worker
            else:
                data.username = pool.user

        return data
