# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from pydantic import BaseModel

from mod.ipr_asic.data import (
    MinerAlgorithm,
    MinerData,
    MinerFirmware,
    MinerPlatform,
    MinerType,
)
from mod.ipr_asic.schemas.vnish import (
    Info as VnishSystemInfo,
)
from mod.ipr_asic.schemas.vnish import (
    PoolStats as VnishMinerPool,
)
from mod.ipr_asic.schemas.vnish import (
    Summary as VnishSummary,
)


class VnishModels(BaseModel):
    system_info: VnishSystemInfo
    summary: VnishSummary
    pools: list[VnishMinerPool]


class VnishParser:
    def parse(self, models: VnishModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.ANTMINER
        data.firmware = MinerFirmware.VNISH

        data.uptime = models.summary.miner.miner_status.miner_state_time
        data.subtype = models.system_info.miner[9:]
        net_info = models.system_info.system.network_status
        data.hostname = net_info.hostname
        data.mac = net_info.mac
        data.serial = models.system_info.serial
        data.fw_version = models.system_info.fw_version
        data.algorithm = MinerAlgorithm.from_value(models.system_info.algorithm)

        match models.system_info.platform:
            case "xil":
                data.platform = MinerPlatform.XILINX
            case "bb":
                data.platform = MinerPlatform.BEAGLEBONE
            case "aml":
                data.platform = MinerPlatform.AMLOGIC
            case "cv":
                data.platform = MinerPlatform.CVITEK
            case "stm":
                data.platform = MinerPlatform.STM
            case _:
                data.platform = None

        for pool in models.pools:
            if pool.status == "active":
                data.stratum_url = pool.url
                if "." in pool.user:
                    user, worker = pool.user.split(",", 1)
                    data.username = user
                    data.worker_name = worker
                else:
                    data.username = pool.user
                break

        return data
