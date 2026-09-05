# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pydantic import BaseModel, Field

from .models import (
    MinerConfigModel,
    MinerPoolModel,
    NetworkInfoModel,
    PoolConfig,
    SummaryModel,
    SystemInfoModel,
)


class ActionResult(BaseModel):
    code: int
    msg: str = ""
    data: str = ""


class SystemInfo(SystemInfoModel):
    minertype: str
    nettype: str
    netdevice: str
    macaddr: str
    hostname: str
    ipaddress: str
    netmask: str
    gateway: str
    dnsservers: str
    curtime: str
    uptime: str
    loadaverage: str
    mem_total: str
    mem_used: str
    mem_free: str
    mem_buffers: str
    mem_cached: str
    system_mode: str
    bb_hwv: str
    system_kernel_version: str
    system_filesystem_version: str
    cgminer_version: str


class NetworkInfo(NetworkInfoModel):
    nettype: str
    netdevice: str
    macaddr: str
    ipaddress: str
    netmask: str
    conf_nettype: str
    conf_hostname: str
    conf_ipaddress: str
    conf_netmask: str
    conf_gateway: str
    conf_dnsservers: str


class NetworkInfoV1(NetworkInfoModel):
    bb_nettype: str
    bb_netdevice: str
    bb_macaddr: str
    bb_ipaddress: str
    bb_netmask: str
    bb_conf_nettype: str
    bb_conf_hostname: str
    bb_conf_ipaddress: str
    bb_conf_netmask: str
    bb_conf_gateway: str
    bb_conf_dnsservers: str


class MinerConfig(MinerConfigModel):
    fan_ctrl: bool = Field(False, alias="fan-ctrl")
    fan_pwm_front: str | None = Field(None, alias="fan-pwn-front")
    fan_pwm_back: str | None = Field(None, alias="fan-pwn-back")
    use_vil: bool = Field(alias="use-vil")
    freq: str
    sram_voltage: str = Field(alias="sram-voltage")
    coin_type: str = Field(alias="coin-type")
    pools: PoolConfig


class DebugConfig(BaseModel):
    bb_debug_enable: bool
    tm: str
    bb_pll_switch_time: int
    bb_pll_switch_step: int
    bb_chain0_active_chipnum: int
    bb_chain1_active_chipnum: int
    bb_chain2_active_chipnum: int
    bb_chain3_active_chipnum: int
    bb_chain4_active_chipnum: int
    bb_chain5_active_chipnum: int
    bb_chain6_active_chipnum: int
    bb_chain7_active_chipnum: int
    bb_chain0_freq: int
    bb_chain1_freq: int
    bb_chain2_freq: int
    bb_chain3_freq: int
    bb_chain4_freq: int
    bb_chain5_freq: int
    bb_chain6_freq: int
    bb_chain7_freq: int
    bb_startup_voltage: int
    bb_target_voltage: int


class MinerConfigV1(MinerConfigModel):
    miner: MinerConfig
    debug: DebugConfig = Field(alias="debug")
    keepower: str
    runmode: str
    voltage: str


class MinerPool(MinerPoolModel):
    index: int
    url: str
    user: str
    status: str
    diff: float
    getworks: str
    priority: int
    accepted: str
    nonce: str
    diffa: str
    diffr: str
    diffs: str
    rejected: str
    discarded: str
    stale: str
    lsdiff: str
    lstime: str


class Chain(BaseModel):
    index: int
    chain_acn: int
    temp: int
    hw: int
    chain_rate: float
    chain_acs: str
    freq: str


class FanInfo(BaseModel):
    fan1: str
    fan2: str
    fan3: str
    fan4: str


class PoolTotal(BaseModel):
    t_getworks: str
    t_accepted: str
    t_nonce: str
    t_diffa: str
    t_diffr: str
    t_diffs: str
    t_rejected: str
    t_discarded: str
    t_stale: str


class HwTotal(BaseModel):
    h_hw: int
    h_diff1_ratio: float
    h_diffa_ratio: float


class PoolStats(BaseModel):
    total: PoolTotal
    hw: HwTotal
    pool_dtls: list[MinerPool]


class Summary(BaseModel):
    elapsed: str
    ghs5s: str
    ghsav: str
    localwork: str
    utility: float
    wu: str
    bestshare: int


class MinerStatus(SummaryModel):
    elapsed: str
    ghs5s: str
    ghsav: str
    localwork: str
    utility: float
    wu: str
    bestshare: int
    pools: PoolStats
    chains: list[Chain]
    fan: FanInfo
