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
from mod.ipr_asic.schemas.goldshell import AlgoSettings as GoldshellAlgorithm
from mod.ipr_asic.schemas.goldshell import Devs as GoldshellSummary
from mod.ipr_asic.schemas.goldshell import MinerPool as GoldshellPool
from mod.ipr_asic.schemas.goldshell import Settings as GoldshellMinerConfig
from mod.ipr_asic.schemas.goldshell import Status as GoldshellSystemInfo


class GoldshellModels(BaseModel):
    system_info: GoldshellSystemInfo | None = None
    summary: GoldshellSummary | None = None
    miner_config: GoldshellMinerConfig | None = None
    algorithm: GoldshellAlgorithm | None = None
    pools: list[GoldshellPool] | None = None


class GoldshellParser:
    def parse(self, models: GoldshellModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.GOLDSHELL
        data.firmware = MinerFirmware.STOCK

        if models.system_info is not None:
            model = clean_model_name(models.system_info.model, vendor="Goldshell")
            # normalize alpha-numeric model names
            match model:
                case "CAEU14":
                    data.subtype = "SC5 Pro II"
                case "CAEU12":
                    data.subtype = "SC5 Pro"
                case "CBAU12":
                    data.subtype = "CK6"
                    data.algorithm = MinerAlgorithm.EAGLESONG
                case "CBAU13":
                    data.subtype = "CK6 SE"
                    data.algorithm = MinerAlgorithm.EAGLESONG
                case "CDAU12":
                    data.subtype = "KD6"
                    data.algorithm = MinerAlgorithm.BLAKE2S
                case "CDAU14":
                    data.subtype = "KD MAX"
                    data.algorithm = MinerAlgorithm.BLAKE2S
                case "CHAU12":
                    data.subtype = "HS6"
                case "CLAU12":
                    data.subtype = "LT6"
                    data.algorithm = MinerAlgorithm.SCRYPT
                case _:
                    data.subtype = model
            data.fw_version = models.system_info.firmware
        if models.miner_config is not None:
            # Goldshell reports its MAC address in the config name field.
            data.mac = models.miner_config.name
        # for dual algorithm miners, use the selected algorithm
        if models.algorithm is not None and data.algorithm is None:
            data.algorithm = MinerAlgorithm.from_value(
                models.algorithm.algos[models.algorithm.algo_select].name
            )

        for pool in models.pools or []:
            if pool.active:
                data.stratum_url = pool.url
                if "." in pool.user:
                    user, worker = pool.user.split(".", 1)
                    data.username = user
                    data.worker_name = worker
                else:
                    data.username = pool.user
                break

        return data
