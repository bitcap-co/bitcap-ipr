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
from mod.ipr_asic.schemas.iceriver import MinerPool as IceriverPool
from mod.ipr_asic.schemas.iceriver import UserPanel as IceriverSummary


class IceriverModels(BaseModel):
    summary: IceriverSummary | None = None
    pools: list[IceriverPool] | None = None


class IceriverParser:
    def parse(self, models: IceriverModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.ICERIVER
        data.firmware = MinerFirmware.STOCK

        if models.summary is not None:
            self._parse_summary(models.summary, data)

        for pool in models.pools or []:
            if pool.connect == 1:
                data.stratum_url = pool.addr
                if "." in pool.user:
                    user, worker = pool.user.split(".", 1)
                    data.username = user
                    data.worker_name = worker
                else:
                    data.username = pool.user
                break

        return data

    def _parse_summary(self, summary: IceriverSummary, data: MinerData) -> None:
        uptime_str = summary.runtime
        days, hours, mins, secs = map(int, uptime_str.split(":"))
        data.uptime = days * 86400 + hours * 3600 + mins * 60 + secs

        if summary.model == "none":
            slug = summary.softver1
            split_ver = slug.split("_")
            if split_ver[-1] == "miner":
                model_ver = split_ver[-2]
            else:
                model_ver = split_ver[-1].replace("miner", "")
            match model_ver:
                case "10306":
                    data.subtype = "AL3"
                case "11304":
                    data.subtype = "KS7"
                case _:
                    data.subtype = model_ver.upper()
        else:
            data.subtype = clean_model_name(summary.model, vendor="IceRiver")

        data.hostname = summary.host
        data.mac = summary.mac
        data.fw_version = summary.softver1

        data.algorithm = None
        algo = summary.algo
        if algo != "none":
            data.algorithm = MinerAlgorithm.from_value(algo)
        elif data.subtype:
            if data.subtype == "AL3":
                data.algorithm = MinerAlgorithm.BLAKE3
            elif data.subtype.__contains__("KS"):
                data.algorithm = MinerAlgorithm.KHEAVYHASH
