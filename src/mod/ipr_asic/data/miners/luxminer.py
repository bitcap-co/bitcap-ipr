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
from mod.ipr_asic.schemas.cgminer import Version as LuxOSVersionInfo
from mod.ipr_asic.schemas.luxminer import Config as LuxOSSystemInfo
from mod.ipr_asic.schemas.luxminer import MinerPool as LuxOSPool
from mod.ipr_asic.schemas.luxminer import Summary as LuxOSSummary


class LuxminerModels(BaseModel):
    system_info: LuxOSSystemInfo
    summary: LuxOSSummary
    version_info: LuxOSVersionInfo
    pools: list[LuxOSPool]


class LuxminerParser:
    def parse(self, models: LuxminerModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.ANTMINER
        data.firmware = MinerFirmware.LUX_OS
        data.algorithm = MinerAlgorithm.SHA256

        data.api_version = models.version_info.api
        data.uptime = models.summary.elapsed
        data.hostname = models.system_info.hostname
        data.mac = models.system_info.mac_addr
        data.serial = models.system_info.serial_number
        data.fw_version = models.version_info.luxminer
        data.platform = MinerPlatform.from_value(models.system_info.control_board_type)

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
