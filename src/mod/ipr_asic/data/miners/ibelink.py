import re
from datetime import timedelta

from pydantic import BaseModel

from mod.ipr_asic.data import MinerAlgorithm, MinerData, MinerFirmware, MinerType
from mod.ipr_asic.schemas.ibelink import SystemInfo as IBeLinkSystemInfo


class IBeLinkModels(BaseModel):
    system_info: IBeLinkSystemInfo | None = None


class IBeLinkParser:
    def parse(self, models: IBeLinkModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.IBELINK
        data.firmware = MinerFirmware.STOCK

        if models.system_info is not None:
            data.uptime = self._parse_uptime(models.system_info.uptime)
            fw_ver, api_ver = models.system_info.miner_version.split("/")
            data.fw_version = fw_ver
            data.api_version = api_ver
            data.mac = models.system_info.mac
            data.subtype = models.system_info.model
            match data.subtype:
                case "BM-S3":
                    data.algorithm = MinerAlgorithm.BLAKE2B
                case _:
                    pass
        return data

    def _parse_uptime(self, uptime_str: str) -> int:
        match = re.match(
            r"(?:(\d+)d\s*)?(?:(\d+)h\s*)?(?:(\d+)min)?", uptime_str.strip()
        )

        if not match:
            return 0

        days = int(match.group(1) or 0)
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        return timedelta(days=days, hours=hours, minutes=minutes).seconds
