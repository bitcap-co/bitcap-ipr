# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import re

from pydantic import BaseModel

from mod.ipr_asic import MinerData, MinerFirmware, MinerType
from mod.ipr_asic.data import MinerAlgorithm
from mod.ipr_asic.schemas.antminer import MinerPool as AntminerPool
from mod.ipr_asic.schemas.antminer import MinerSummary as AntminerSummary
from mod.ipr_asic.schemas.antminer import SystemInfo as AntminerSystemInfo
from mod.ipr_asic.schemas.models import ContentResponse as AntminerLog

_PLATFORM_PATTERNS: dict[str, re.Pattern[str]] = {
    "Xilinx": re.compile(r"Zynq|Xilinx|xil"),
    "BeagleBone": re.compile(r"BeagleBone"),
    "AMLogic": re.compile(r"amlogic|aml"),
    "CVITEK": re.compile(r"cvitek|CVITEK"),
}


class AntminerModels(BaseModel):
    system_info: AntminerSystemInfo
    summary: AntminerSummary
    pools: list[AntminerPool]
    log: AntminerLog | None = None


class AntminerParser:
    def parse(self, models: AntminerModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.ANTMINER
        data.firmware = MinerFirmware.STOCK
        data.algorithm = MinerAlgorithm.SHA256

        data.uptime = models.summary.elapsed
        data.subtype = models.system_info.minertype[9:]
        data.hostname = models.system_info.hostname
        data.mac = models.system_info.macaddr
        data.serial = models.system_info.serinum
        data.fw_version = models.system_info.system_filesystem_version

        algo = models.system_info.algorithm
        if algo is not None:
            data.algorithm = MinerAlgorithm.from_value(algo)

        if models.log is not None:
            models.log.text = models.log.text[0 : models.log.text.find("===")]
            for platform, pattern in _PLATFORM_PATTERNS.items():
                if pattern.search(models.log.text):
                    data.platform = platform
                    break

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
