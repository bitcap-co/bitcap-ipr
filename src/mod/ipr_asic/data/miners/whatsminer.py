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
    system_info: WhatsminerSystemInfo | None = None
    summary: WhatsminerSummary | None = None
    version_info: WhatsminerVersionInfo | None = None
    pools: list[WhatsminerPool] | None = None
    dev_details: list[WhatsminerDevDetails] | None = None


class WhatsminerV3Models(BaseModel):
    device_info: WhatsminerV3DeviceInfo | None = None
    summary: WhatsminerV3Summary | None = None
    pools: list[WhatsminerV3Pool] | None = None


class WhatsminerParser:
    def parse(self, models: WhatsminerModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.WHATSMINER
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        if models.version_info is not None:
            data.api_version = models.version_info.api_ver
            data.fw_version = models.version_info.fw_ver
            data.platform = models.version_info.platform
            data.subtype = models.version_info.miner_type
        if models.summary is not None:
            try:
                data.uptime = int(models.summary.elapsed)
            except ValueError:
                data.uptime = None
        if models.system_info is not None:
            data.hostname = models.system_info.hostname
            data.mac = models.system_info.mac
            data.serial = models.system_info.minersn
        if data.subtype is None and models.dev_details:
            data.subtype = models.dev_details[0].model

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


class WhatsminerV3Parser:
    def parse(self, models: WhatsminerV3Models) -> MinerData:
        data = MinerData()
        data.type = MinerType.WHATSMINER
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        if models.device_info is not None:
            version = models.device_info.version
            if version is not None:
                data.api_version = version.api
                data.fw_version = version.fwversion
                data.platform = version.platform
            network = models.device_info.network
            if network is not None:
                data.hostname = network.hostname
                data.mac = network.mac
            system = models.device_info.system
            if system is not None:
                data.serial = system.miner_sn
                data.subtype = system.type
        if models.summary is not None:
            data.uptime = models.summary.elapsed

        for pool in models.pools or []:
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
