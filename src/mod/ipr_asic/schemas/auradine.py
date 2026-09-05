from pydantic import BaseModel, Field

from mod.ipr_asic.schemas.cgminer import BaseCGMinerResponse
from mod.ipr_asic.schemas.models import (
    APIObject,
    BlinkStatusModel,
    MinerConfigModel,
    MinerPasswdConfigModel,
    MinerPoolModel,
    NetworkInfoModel,
    SummaryModel,
    SystemInfoModel,
)


class NetworkInfo(NetworkInfoModel):
    command: str
    protocol: str
    ip: str
    mask: str
    gateway: str
    dns: str
    hostname: str


class IPReport(SystemInfoModel):
    command: str
    serial: str = Field(alias="SerialNo")
    ip: str
    mac: str
    model: str
    gateway: str | None = None
    mask: str | None = None
    model_version: str | None = Field(None, alias="ModelVersion")
    version: str
    hostname: str
    orgid: str | None = None
    pubkey: str = Field(alias="pubKey")
    tpm_pubkey: str = Field(alias="tpmPubKey")
    cb_serial: str = Field(alias="CBSerialNo")
    chassis_serial: str = Field(alias="ChassisSerialNo")
    hb_serials: list[str] = Field(default_factory=list[str], alias="HBSerialNo")
    internal_type: str | None = Field(None, alias="InternalType")


class Pool(MinerPoolModel):
    pool: int = Field(alias="POOL")
    url: str = Field(alias="URL")
    status: str = Field(alias="Status")
    priority: int = Field(alias="Priority")
    quota: int = Field(alias="Quota")
    long_poll: str = Field(alias="Long Poll")
    getworks: int = Field(alias="Getworks")
    accepted: int = Field(alias="Accepted")
    rejected: int = Field(alias="Rejected")
    works: int = Field(alias="Works")
    discarded: int = Field(alias="Discarded")
    stale: int = Field(alias="Stale")
    get_failures: int = Field(alias="Get Failures")
    remote_failures: int = Field(alias="Remote Failures")
    user: str = Field(alias="User")
    passwd: str = Field(validation_alias="Pass")
    last_share_time: int = Field(alias="Last Share Time")
    diff1_shares: int = Field(alias="Diff1 Shares")
    proxy_type: str = Field(alias="Proxy Type")
    proxy: str = Field(alias="Proxy")
    diffa: int = Field(alias="Difficulty Accepted")
    diffr: int = Field(alias="Difficulty Rejected")
    diffs: int = Field(alias="Difficulty Stale")
    last_share_difficulty: int = Field(alias="Last Share Difficulty")
    work_difficulty: int = Field(alias="Work Difficulty")
    has_stratum: bool = Field(alias="Has Stratum")
    stratum_active: bool = Field(alias="Stratum Active")
    stratum_url: str = Field(alias="Stratum URL")
    stratum_diff: int = Field(alias="Stratum Difficulty")
    has_vmask: bool = Field(alias="Has Vmask")
    has_gbt: bool = Field(alias="Has GBT")
    best_share: int = Field(alias="Best Share")
    pool_rejected_: float = Field(alias="Pool Rejected%")
    pool_stale_: float = Field(alias="Pool Stale%")
    bad_work: int = Field(alias="Bad Work")
    current_block_height: int = Field(alias="Current Block Height")
    current_block_version: int = Field(alias="Current Block Version")
    protocol: str = Field(alias="Protocol")


class Summary(SummaryModel):
    elapsed: int = Field(alias="Elapsed")
    mhs_av: float = Field(alias="MHS av")
    mhs_5s: float = Field(alias="MHS 5s")
    mhs_1m: float = Field(alias="MHS 1m")
    mhs_5m: float = Field(alias="MHS 5m")
    mhs_15m: float = Field(alias="MHS 15m")
    mhs_24h: float = Field(alias="MHS 24h")
    gmhs_av: float = Field(alias="GMHS av")
    gmhs_5s: float = Field(alias="GMHS 5s")
    gmhs_1m: float = Field(alias="GMHS 1m")
    gmhs_5m: float = Field(alias="GMHS 5m")
    gmhs_15m: float = Field(alias="GMHS 15m")
    gmhs_24h: float = Field(alias="GMHS 24h")
    pool_mhs_30m: int = Field(alias="Pool MHS 30m")
    pool_mhs_60m: int = Field(alias="Pool MHS 60m")
    pool_mhs_24h: int = Field(alias="Pool MHS 24h")
    getworks: int = Field(alias="Getworks")
    accepted: int = Field(alias="Accepted")
    rejected: int = Field(alias="Rejected")
    hardware_errors: int = Field(alias="Hardware Errors")
    utility: float = Field(alias="Utility")
    discarded: int = Field(alias="Discarded")
    stale: int = Field(alias="Stale")
    get_failures: int = Field(alias="Get Failures")
    local_work: int = Field(alias="Local Work")
    remote_failures: int = Field(alias="Remote Failures")
    total_mh: int = Field(alias="Total MH")
    total_gmh: int = Field(alias="Total GMH")
    work_utility: int = Field(alias="Work Utility")
    difficulty_accepted: int = Field(alias="Difficulty Accepted")
    difficulty_rejected: int = Field(alias="Difficulty Rejected")
    difficulty_stale: int = Field(alias="Difficulty Stale")
    best_share: int = Field(alias="Best Share")
    device_hardware_: int = Field(alias="Device Hardware%")
    device_rejected_: int = Field(alias="Device Rejected%")
    pool_rejected_: float = Field(alias="Pool Rejected%")
    pool_stale_: int = Field(alias="Pool Stale%")
    last_getwork: int = Field(alias="Last getwork")
    wattage: int = Field(alias="Wattage")
    ths_throttle: float = Field(alias="ThsThrottle")
    jths_1m: float = Field(alias="JTHS 1m")


class Mode(BaseModel):
    command: str = "mode"
    mode: str | None = Field(None, pattern=r"normal|eco|turbo|custom")
    sleep: str | None = Field(None, pattern=r"on|off")
    tune: str | None = Field(None, pattern=r"ths|power")
    ths: float | None = Field(None)
    power: int | None = Field(None, ge=0, le=10000)
    fans_in_standby: str | None = Field(
        None, pattern=r"on|off", serialization_alias="fansInStandby"
    )
    coolant_default_action: str | None = Field(
        None, pattern=r"on|off", serialization_alias="coolantDefaultAction"
    )
    retune_time: int | None = Field(
        None, ge=30, le=2880, serialization_alias="retuneTime"
    )
    optimize_eco: str | None = Field(
        None, pattern=r"on|off", serialization_alias="optimizeEco"
    )
    mining_if_net_down: str | None = Field(
        None, pattern=r"on|off", serialization_alias="miningIfNetDown"
    )
    persist_standby: str | None = Field(
        None, pattern=r"on|off", serialization_alias="persistStandby"
    )
    leak_detected: str | None = Field(
        None, pattern=r"on|off", serialization_alias="leakDetected"
    )


class ModeResponse(MinerConfigModel):
    mode: str | None = Field(None, alias="Mode")
    sleep: str | None = Field(None, alias="Sleep")
    tune: str | None = Field(None, alias="Tune")
    ths: float | None = Field(None, alias="Ths")
    power: int | None = Field(None, alias="Power")
    fans_in_standby: str | None = Field(None, alias="FansInStandby")
    coolant_default_action: str | None = Field(None, alias="coolantDefaultAction")
    retune_time: int | None = Field(None, alias="reTuneTime")
    retune_count: int | None = Field(None, alias="reTuneCount")
    optimize_eco: str | None = Field(None, alias="optimizeEco")
    mining_if_net_down: str | None = Field(None, alias="miningIfNetDown")
    persist_standby: str | None = Field(None, alias="persistStandby")
    leak_detected: str | None = Field(None, alias="leakDetected")


class LED(BaseModel):
    command: str = "led"
    code: int
    led1: int | None = None
    led2: int | None = None
    msg: str | None = None


class LEDResponse(BlinkStatusModel):
    code: int = Field(
        validation_alias="Code",
    )
    led1: int = Field(validation_alias="LED1")
    led2: int = Field(validation_alias="LED2")
    msg: str = Field(validation_alias="Msg")
    standby_reason: str | None = Field(None, validation_alias="standbyReason")
    display_msg: str | None = Field(None, validation_alias="DisplayMsg")


class Token(BaseModel):
    name: str = Field(alias="Name")
    when: int = Field(alias="When")
    token: str = Field(alias="Token")


class WhitelistPools(BaseModel):
    accepted_pools_urls: list[str] = Field(
        default_factory=list[str], validation_alias="acceptedPoolUrls"
    )


class UpdatePoolsResponse(BaseModel):
    msg: str


class MinerPasswdConfig(MinerPasswdConfigModel):
    command: str = "password"
    user: str
    old: str
    new: str


class CGMinerResponse(BaseCGMinerResponse):
    summary: list[Summary] | None = Field(None, alias="SUMMARY")
    stats: list[APIObject] | None = Field(None, alias="STATS")
    devs: list[APIObject] | None = Field(None, alias="DEVS")
    dev_details: list[APIObject] | None = Field(None, alias="DEVDETAILS")
    pools: list[Pool] | None = Field(None, alias="POOLS")
    network: list[NetworkInfo] | None = Field(None, alias="Network")
    ip_report: list[IPReport] | None = Field(None, alias="IPReport")
    led: list[LEDResponse] | None = Field(None, alias="LED")
    mode: list[ModeResponse] | None = Field(None, alias="Mode")
    whitelist_pools: list[WhitelistPools] | None = Field(None, alias="whitelistPools")
    update_pools: list[UpdatePoolsResponse] | None = Field(None, alias="UPDATEPOOLS")
    token: list[Token] | None = Field(None, alias="Token")
