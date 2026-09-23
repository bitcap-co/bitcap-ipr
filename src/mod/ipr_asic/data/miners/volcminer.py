# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from pydantic import BaseModel

from mod.ipr_asic.data import (
    MinerAlgorithm,
    MinerData,
    MinerFirmware,
    MinerType,
)
from mod.ipr_asic.schemas.volcminer import MinerPool as VolcminerPool
from mod.ipr_asic.schemas.volcminer import MinerStatus as VolcminerSummary
from mod.ipr_asic.schemas.volcminer import SystemInfo as VolcminerSystemInfo


class VolcminerModels(BaseModel):
    system_info: VolcminerSystemInfo | None = None
    summary: VolcminerSummary | None = None
    pools: list[VolcminerPool] | None = None


class VolcminerParser:
    def parse(self, models: VolcminerModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.VOLCMINER
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SCRYPT

        if models.summary is not None:
            data.uptime = int(models.summary.elapsed)
        if models.system_info is not None:
            data.subtype = models.system_info.minertype[10:]
            data.hostname = models.system_info.hostname
            data.mac = models.system_info.macaddr
            data.fw_version = models.system_info.system_filesystem_version

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
