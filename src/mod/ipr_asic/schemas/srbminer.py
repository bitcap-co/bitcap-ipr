# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pydantic import BaseModel, Field

from .models import MinerPoolModel, SystemInfoModel


class GPUDevice(BaseModel):
    device: str = ""
    vendor: str = ""
    model: str = ""


class SRBPool(MinerPoolModel):
    pool: str = ""
    wallet: str = ""


class SRBAlgorithm(BaseModel):
    name: str = ""
    pool: SRBPool = SRBPool()


class SRBMinerInfo(SystemInfoModel):
    rig_name: str = ""
    miner_version: str = ""
    mining_time: int = 0
    total_cpu_workers: int = 0
    total_gpu_workers: int = 0
    gpu_devices: list[GPUDevice] = Field(default_factory=list)
    algorithms: list[SRBAlgorithm] = Field(default_factory=list)
