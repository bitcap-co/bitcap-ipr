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
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerDevDetails as WhatsminerDevDetails,
)
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerPool as WhatsminerPool,
)
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerSummary as WhatsminerSummary,
)
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerSystemInfo as WhatsminerSystemInfo,
)
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerV3DeviceInfo as WhatsminerV3DeviceInfo,
)
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerV3Pool as WhatsminerV3Pool,
)
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerV3Summary as WhatsminerV3Summary,
)
from mod.ipr_asic.schemas.whatsminer import (
    BTMinerVersion as WhatsminerVersionInfo,
)


class WhatsminerModels(BaseModel):
    system_info: WhatsminerSystemInfo
    summary: WhatsminerSummary
    version_info: WhatsminerVersionInfo
    pools: list[WhatsminerPool]
    dev_details: list[WhatsminerDevDetails]


class WhatsminerV3Models(BaseModel):
    device_info: WhatsminerV3DeviceInfo
    summary: WhatsminerV3Summary
    pools: list[WhatsminerV3Pool]


class WhatsminerParser:
    def parse(self, models: WhatsminerModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.WHATSMINER
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        data.api_version = models.version_info.api_ver
        try:
            data.uptime = int(models.summary.elapsed)
        except ValueError:
            data.uptime = None
        data.hostname = models.system_info.hostname
        data.mac = models.system_info.mac
        data.serial = models.system_info.minersn
        data.fw_version = models.version_info.fw_ver
        data.platform = models.version_info.platform

        miner_type = models.version_info.miner_type
        if miner_type is not None:
            data.subtype = miner_type
        else:
            # get from devices
            data.subtype = models.dev_details[0].model

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


class WhatsminerV3Parser:
    def parse(self, models: WhatsminerV3Models) -> MinerData:
        data = MinerData()
        data.type = MinerType.WHATSMINER
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        system = models.device_info.system
        if system is not None:
            data.api_version = system.api
            data.fw_version = system.fwversion
            data.platform = system.platform
        data.uptime = models.summary.elapsed
        network = models.device_info.network
        if network is not None:
            data.hostname = network.hostname
            data.mac = network.mac
        miner = models.device_info.miner
        if miner is not None:
            data.serial = miner.miner_sn
            data.subtype = miner.type

        for pool in models.pools:
            if pool.status == "alive":
                data.stratum_url = pool.url
                if "." in pool.account:
                    user, worker = pool.account.split(".", 1)
                    data.username = user
                    data.worker_name = worker
                else:
                    data.username = pool.account
                break

        return data
