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
    clean_model_name,
)
from mod.ipr_asic.schemas.antminer import SystemInfo as ElphapexSystemInfo
from mod.ipr_asic.schemas.elphapex import MinerPool as ElphapexPool
from mod.ipr_asic.schemas.elphapex import MinerSummary as ElphapexSummary


class ElphapexModels(BaseModel):
    system_info: ElphapexSystemInfo | None = None
    summary: ElphapexSummary | None = None
    pools: list[ElphapexPool] | None = None


class ElphapexParser:
    def parse(self, models: ElphapexModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.ELPHAPEX
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SCRYPT

        if models.summary is not None:
            data.uptime = models.summary.elapsed
        if models.system_info is not None:
            data.subtype = clean_model_name(
                models.system_info.minertype, vendor="Elphapex"
            )
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
