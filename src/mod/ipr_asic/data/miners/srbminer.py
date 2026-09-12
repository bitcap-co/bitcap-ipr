# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from pydantic import BaseModel

from mod.ipr_asic.data import MinerAlgorithm, MinerData, MinerType
from mod.ipr_asic.schemas.srbminer import SRBMinerInfo as SRBMinerSystemInfo
from mod.ipr_asic.schemas.srbminer import SRBPool as SRBMinerPool

# marketing/vendor tokens stripped when building a readable GPU model name.
_GPU_MODEL_NOISE = {"nvidia", "amd", "intel", "geforce", "radeon"}


def _format_gpu_model(model: str) -> str:
    """Turn an SRBMiner device model into a readable name.

    e.g. "nvidia_geforce_rtx_3070" -> "RTX 3070".
    """
    parts = [p for p in model.split("_") if p and p.lower() not in _GPU_MODEL_NOISE]
    if not parts:
        parts = [p for p in model.split("_") if p]
    cleaned: list[str] = []
    for p in parts:
        # short alpha tokens are acronyms (rtx, gtx, rx); keep numbers as-is.
        if p.isalpha() and len(p) <= 3:
            cleaned.append(p.upper())
        elif p.isalpha():
            cleaned.append(p.capitalize())
        else:
            cleaned.append(p)
    return " ".join(cleaned)


class SRBMinerModels(BaseModel):
    system_info: SRBMinerSystemInfo
    pools: list[SRBMinerPool]


class SRBMinerParser:
    def parse(self, models: SRBMinerModels) -> MinerData:
        data = MinerData()
        data.type = MinerType.HIVEGPU
        data.platform = "HiveOS"

        data.api_version = models.system_info.miner_version
        data.uptime = models.system_info.mining_time

        data.subtype = None
        gpus = models.system_info.gpu_devices
        if gpus:
            count = models.system_info.total_gpu_workers or len(gpus)
            model = _format_gpu_model(gpus[0].model)
            data.subtype = f"{count}x {model}" if model else f"{count}x GPU"
        data.hostname = models.system_info.rig_name

        algos = models.system_info.algorithms
        if algos:
            data.algorithm = MinerAlgorithm.from_value(algos[0].name)

        for pool in models.pools:
            if not pool.pool:
                continue
            data.stratum_url = pool.pool
            if "." in pool.wallet:
                user, worker = pool.wallet.split(".", 1)
                data.username = user
                data.worker_name = worker
            else:
                data.username = pool.wallet
            break

        return data
