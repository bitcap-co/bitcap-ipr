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
