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
        lan_iface = models.system_info.wan.ifname
        for iface in models.network_info.ifaces:
            if iface.name == lan_iface:
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

        # miner status returns active pool
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
