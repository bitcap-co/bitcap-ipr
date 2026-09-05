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
