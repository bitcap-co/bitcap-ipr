# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import re
from datetime import timedelta

from pydantic import BaseModel

from mod.ipr_asic.data import (
    MinerAlgorithm,
    MinerData,
    MinerFirmware,
    MinerType,
    clean_model_name,
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
            data.uptime = self._parse_uptime(models.summary.elapsed)
        if models.system_info is not None:
            data.subtype = clean_model_name(
                models.system_info.minertype, vendor="VolcMiner"
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

    def _parse_uptime(self, uptime_str: str) -> int:
        match = re.match(
            r"(?:(\d+)d\s*)?(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)", uptime_str.strip()
        )

        if not match:
            return 0

        days = int(match.group(1) or 0)
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        seconds = int(match.group(4) or 0)
        return timedelta(
            days=days, hours=hours, minutes=minutes, seconds=seconds
        ).seconds
