from pydantic import BaseModel

from mod.ipr_asic.data import (
    MinerAlgorithm,
    MinerData,
    MinerFirmware,
    MinerType,
    clean_model_name,
)
from mod.ipr_asic.schemas.auradine import IPReport as AuradineSystemInfo
from mod.ipr_asic.schemas.auradine import Pool as AuradinePool
from mod.ipr_asic.schemas.auradine import Summary as AuradineSummary


class AuradineModels(BaseModel):
    system_info: AuradineSystemInfo | None = None
    summary: AuradineSummary | None = None
    pools: list[AuradinePool] | None = None


class AuradineParser:
    def parse(self, models: AuradineModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.AURADINE
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        if models.summary is not None:
            data.uptime = models.summary.elapsed
        if models.system_info is not None:
            data.subtype = clean_model_name(models.system_info.model, vendor="Auradine")
            data.hostname = models.system_info.hostname
            data.mac = models.system_info.mac
            data.serial = models.system_info.chassis_serial
            data.fw_version = models.system_info.version

        for pool in models.pools or []:
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
