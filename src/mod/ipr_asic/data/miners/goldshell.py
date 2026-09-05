# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from pydantic import BaseModel

from mod.ipr_asic import MinerData
from mod.ipr_asic.data import MinerAlgorithm, MinerFirmware, MinerType
from mod.ipr_asic.schemas.goldshell import AlgoSettings as GoldshellAlgorithm
from mod.ipr_asic.schemas.goldshell import Devs as GoldshellSummary
from mod.ipr_asic.schemas.goldshell import MinerPool as GoldshellPool
from mod.ipr_asic.schemas.goldshell import Settings as GoldshellMinerConfig
from mod.ipr_asic.schemas.goldshell import Status as GoldshellSystemInfo


class GoldshellModels(BaseModel):
    system_info: GoldshellSystemInfo
    summary: GoldshellSummary
    miner_config: GoldshellMinerConfig
    algorithm: GoldshellAlgorithm
    pools: list[GoldshellPool]


class GoldshellParser:
    def parse(self, models: GoldshellModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.GOLDSHELL
        data.firmware = MinerFirmware.STOCK

        data.subtype = models.system_info.model
        # data.hostname = models.miner_config.name
        data.mac = models.miner_config.name
        data.fw_version = models.system_info.firmware
        data.algorithm = MinerAlgorithm.from_value(
            models.algorithm.algos[models.algorithm.algo_select].name
        )

        for pool in models.pools:
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
