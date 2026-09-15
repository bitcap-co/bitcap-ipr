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
from mod.ipr_asic.schemas.sealminer import (
    MinerPool as SealminerPool,
)
from mod.ipr_asic.schemas.sealminer import (
    Summary as SealminerSummary,
)
from mod.ipr_asic.schemas.sealminer import (
    SystemInfo as SealminerSystemInfo,
)


class SealminerModels(BaseModel):
    system_info: SealminerSystemInfo
    summary: SealminerSummary
    pools: list[SealminerPool]


class SealminerParser:
    def parse(self, models: SealminerModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.SEALMINER
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        data.uptime = models.summary.summary.elapsed
        data.subtype = models.system_info.miner_type
        data.mac = models.system_info.macaddr
        data.fw_version = models.system_info.firmware_version
        data.platform = models.system_info.ctrl_version

        for pool in models.pools:
            if pool.is_active:
                data.stratum_url = pool.url
                if pool.user is not None and "." in pool.user:
                    user, worker = pool.user.split(".", 1)
                    data.username = user
                    data.worker_name = worker
                else:
                    data.username = pool.user
                break

        return data
