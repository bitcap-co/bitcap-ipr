# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pydantic import BaseModel, Field

from .models import MinerPoolModel, SystemInfoModel


class GPUDevice(BaseModel):
    id: int = 0
    topology_id: str = ""
    bus_id: int = 0
    device: str = ""
    vendor: str = ""
    model: str = ""
    fan_speed_rpm: int = 0
    core_clock: int = 0
    memory_clock: int = 0
    temperature: int = 0
    asic_power: int = 0
    off_temperature: int = 0


class CPUDevice(BaseModel):
    id: int = 0
    device: str = ""
    model: str = ""
    L1: int = 0
    L2: int = 0
    L3: int = 0
    package_power: float = 0.0


class SRBPool(MinerPoolModel):
    pool: str = ""
    wallet: str = ""
    time_connected: str = ""
    uptime: int = 0
    difficulty: float = 0.0
    last_job_received: int = 0
    latency: int = 0


class SRBShares(BaseModel):
    total: int = 0
    accepted: int = 0
    rejected: int = 0
    avg_find_time: int = 0


class SRBCPUHashrate(BaseModel):
    total: float = 0.0


class SRBGPUHashrate(BaseModel):
    total: float = 0.0


class SRBHashrate(BaseModel):
    one_min: float = Field(default=0.0, validation_alias="1min")
    fifteen_min: float = Field(default=0.0, validation_alias="15min")
    one_hour: float = Field(default=0.0, validation_alias="1hr")
    six_hour: float = Field(default=0.0, validation_alias="6hr")
    cpu: SRBCPUHashrate = SRBCPUHashrate()
    gpu: SRBGPUHashrate = SRBGPUHashrate()


class SRBAlgorithm(BaseModel):
    id: int = 0
    name: str = ""
    pool: SRBPool = SRBPool()
    shares: SRBShares = SRBShares()
    hashrate: SRBHashrate = SRBHashrate()


class SRBMinerInfo(SystemInfoModel):
    rig_name: str = ""
    miner_version: str = ""
    mining_time: int = 0
    total_cpu_workers: int = 0
    total_gpu_workers: int = 0
    cpu_devices: list[CPUDevice] = Field(default_factory=list)
    gpu_devices: list[GPUDevice] = Field(default_factory=list)
    algorithms: list[SRBAlgorithm] = Field(default_factory=list)
