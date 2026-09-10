# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from pydantic import Field

from .cgminer import (
    BaseCGMinerResponse,
    BaseDev,
    BaseDevDetails,
    BasePool,
    BaseStat,
    BaseSummary,
)
from .models import (
    SystemInfoModel,
)


class Config(SystemInfoModel):
    asc_count: int = Field(alias="ASC Count")
    actual_power_target: int = Field(alias="ActualPowerTarget")
    bcast_addr: str = Field(alias="BcastAddr")
    control_board_type: str = Field(alias="ControlBoardType")
    cooling: str = Field(alias="Cooling")
    curtail_mode: str = Field(alias="CurtailMode")
    dhcp: bool = Field(alias="DHCP")
    dns_servers: str = Field(alias="DNS Servers")
    device_code: str = Field(alias="Device Code")
    fpga_build_id_hex: str = Field(alias="FPGABuildIdHex")
    fpga_build_id_str: str = Field(alias="FPGABuildIdStr")
    fee_status: str = Field(alias="FeeStatus")
    gateway: str = Field(alias="Gateway")
    green_led: str = Field(alias="GreenLed")
    hostname: str = Field(alias="Hostname")
    hotplug: str = Field(alias="Hotplug")
    ip_addr: str = Field(alias="IPAddr")
    ideal_power_target: int = Field(alias="IdealPowerTarget")
    immersion_mode: bool = Field(alias="ImmersionMode")
    is_atm_enabled: bool = Field(alias="IsAtmEnabled")
    is_power_supply_on: bool = Field(alias="IsPowerSupplyOn")
    is_power_target_enabled: bool = Field(alias="IsPowerTargetEnabled")
    is_power_target_supported: bool = Field(alias="IsPowerTargetSupported")
    is_single_voltage: bool = Field(alias="IsSingleVoltage")
    is_tuning: bool = Field(alias="IsTuning")
    log_interval: int = Field(alias="Log Interval")
    log_file_level: str = Field(alias="LogFileLevel")
    mac_addr: str = Field(alias="MACAddr")
    model: str = Field(alias="Model")
    nameplate_ths: float = Field(alias="NameplateTHS")
    netmask: str = Field(alias="Netmask")
    os: str = Field(alias="OS")
    pga_count: int = Field(alias="PGA Count")
    pic: str = Field(alias="PIC")
    psu_hw_version: str = Field(alias="PSUHwVersion")
    psu_label: str = Field(alias="PSULabel")
    pool_count: int = Field(alias="Pool Count")
    power_limit: int = Field(alias="PowerLimit")
    profile: str = Field(alias="Profile")
    profile_step: str = Field(alias="ProfileStep")
    red_led: str = Field(alias="RedLed")
    serial_number: str = Field(alias="SerialNumber")
    strategy: str = Field(alias="Strategy")
    system_status: str = Field(alias="SystemStatus")
    update_on_startup: str = Field(alias="UpdateOnStartup")
    update_on_timeout: str = Field(alias="UpdateOnTimeout")
    update_on_user: str = Field(alias="UpdateOnUser")
    update_source: str = Field(alias="UpdateSource")
    update_timeout: int = Field(alias="UpdateTimeout")


class Summary(BaseSummary):
    elapsed: int = Field(alias="Elapsed")
    ghs_5s: float = Field(alias="GHS 5s")
    ghs_30m: float = Field(alias="GHS 30m")
    ghs_av: float = Field(alias="GHS av")
    total_mh: float = Field(alias="Total MH")
    accepted: int = Field(alias="Accepted")
    rejected: int = Field(alias="Rejected")
    discarded: int = Field(alias="Discarded")
    hw_errors: int = Field(alias="Hardware Errors")
    pool_rejected_per: float = Field(alias="Pool Rejected%")
    pool_stale_per: float = Field(alias="Pool Stale%")
    stale: int = Field(alias="Stale")
    getworks: int = Field(alias="Getworks")
    last_getwork: int = Field(alias="Last getwork")
    best_share: int = Field(alias="Best Share")
    best_session_share: int = Field(alias="Best Session Share")
    diffa: int = Field(alias="Difficulty Accepted")
    diffr: int = Field(alias="Difficulty Rejected")
    diffs: int = Field(alias="Difficulty Stale")
    utility: float = Field(alias="Utility")
    work_utility: float = Field(alias="Work Utility")


class MinerPool(BasePool):
    diff: str = Field(alias="Diff")
    diff1_shares: int = Field(alias="Diff1 Shares")
    group: int = Field(alias="GROUP")
    pool_rejected_per: float = Field(alias="Pool Rejected%")
    pool_stale_per: float = Field(alias="Pool Stale%")
    best_share: int = Field(alias="Best Share")
    diffa: int = Field(alias="Difficulty Accepted")
    diffr: int = Field(alias="Difficulty Rejected")
    diffs: int = Field(alias="Difficulty Stale")
    last_share_diff: int = Field(alias="Last Share Diff")


class Stat(BaseStat):
    pass


class Dev(BaseDev):
    asc: int = Field(alias="ASC")
    accepted: int = Field(alias="Accepted")
    board: str = Field(alias="Board")
    connector: str = Field(alias="Connector")
    controller_ip_version_hex: str = Field(alias="ControllerIPVersionHex")
    controller_ip_version_str: str = Field(alias="ControllerIPVersionStr")
    device_elapsed: int = Field(alias="Device Elapsed")
    device_hardware_per: int = Field(alias="Device Hardware%")
    device_rejected_per: int = Field(alias="Device Rejected%")
    diff1_work: int = Field(alias="Diff1 Work")
    difficulty_accepted: int = Field(alias="Difficulty Accepted")
    difficulty_rejected: int = Field(alias="Difficulty Rejected")
    enabled: str = Field(alias="Enabled")
    hardware_error_mhs_15m: int = Field(alias="Hardware Error MHS 15m")
    hardware_errors: int = Field(alias="Hardware Errors")
    id: int = Field(alias="ID")
    is_ramping: bool = Field(alias="IsRamping")
    is_user_shutdown: bool = Field(alias="IsUserShutdown")
    last_share_difficulty: int = Field(alias="Last Share Difficulty")
    last_share_pool: int = Field(alias="Last Share Pool")
    last_share_time: int = Field(alias="Last Share Time")
    last_valid_work: int = Field(alias="Last Valid Work")
    mhs_15m: float = Field(alias="MHS 15m")
    mhs_1m: float = Field(alias="MHS 1m")
    mhs_30m: float = Field(alias="MHS 30m")
    mhs_5m: float = Field(alias="MHS 5m")
    mhs_5s: float = Field(alias="MHS 5s")
    mhs_60m: float = Field(alias="MHS 60m")
    mhs_av: float = Field(alias="MHS av")
    name: str = Field(alias="Name")
    nominal_mhs: float = Field(alias="Nominal MHS")
    profile: str = Field(alias="Profile")
    rejected: int = Field(alias="Rejected")
    serial_number: str = Field(alias="SerialNumber")
    status: str = Field(alias="Status")
    temperature: float = Field(alias="Temperature")
    total_mh: float = Field(alias="Total MH")
    utility: int = Field(alias="Utility")


class Devdetail(BaseDevDetails):
    board: str = Field(alias="Board")
    chips: int = Field(alias="Chips")
    cores: int = Field(alias="Cores")
    devdetails: int = Field(alias="DEVDETAILS")
    device_path: str = Field(alias="Device Path")
    driver: str = Field(alias="Driver")
    frequency: int = Field(alias="Frequency")
    id: int = Field(alias="ID")
    kernel: str = Field(alias="Kernel")
    model: str = Field(alias="Model")
    name: str = Field(alias="Name")
    profile: str = Field(alias="Profile")
    serial_number: str = Field(alias="SerialNumber")
    voltage: float = Field(alias="Voltage")


class CGMinerResponse(BaseCGMinerResponse):
    config: list[Config] | None = Field(None, alias="CONFIG")
    devs: list[Dev] | None = Field(None, alias="DEVS")
    dev_details: list[Devdetail] | None = Field(None, alias="DEVDETAILS")
    summary: list[Summary] | None = Field(None, alias="SUMMARY")
    pools: list[MinerPool] | None = Field(None, alias="POOLS")
