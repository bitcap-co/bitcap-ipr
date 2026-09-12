import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel

from .cgminer import BaseDev, BaseDevDetails, BasePool, BaseSummary, BaseVersion
from .models import (
    APIObject,
    MinerPoolModel,
    NetworkInfoModel,
    SummaryModel,
    SystemInfoModel,
)


class BTMinerCommand(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    cmd: str
    token: str | None = None


class BTMinerEncryptedCommand(BaseModel):
    enc: int = 1
    data: str


class Token(BaseModel):
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    sign: str
    key: str


class TokenResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    salt: str
    time: str
    newsalt: str


class BTMinerSystemInfo(SystemInfoModel):
    ntp: list[str] = Field(default_factory=list)
    ip: str | None = None
    proto: str | None = None
    netmask: str | None = None
    gateway: str | None = None
    dns: str | None = None
    hostname: str | None = None
    mac: str | None = None
    ledstat: str | None = None
    minersn: str = ""
    powersn: str = ""
    upfreq_speed: str | None = None


class BTMinerVersion(BaseVersion):
    api_ver: str
    fw_ver: str
    platform: str
    chip: str
    miner_type: str | None = None


class BTMinerSummary(BaseSummary):
    elapsed: float = Field(default=0.0, alias="Elapsed")
    uptime: int = Field(default=0, alias="Uptime")
    mhs_1m: float = Field(default=0.0, alias="MHS 1m")
    mhs_5m: float = Field(default=0.0, alias="MHS 5m")
    mhs_15m: float = Field(default=0.0, alias="MHS 15m")
    mhs_av: float = Field(default=0.0, alias="MHS av")
    freq_avg: float = Field(default=0.0)
    fan_in: int = Field(default=0, alias="Fan Speed In")
    fan_out: int = Field(default=0, alias="Fan Speed Out")
    accepted: int = Field(default=0, alias="Accepted")
    rejected: int = Field(default=0, alias="Rejected")

    power: float = Field(default=0.0, alias="Power")
    power_rate: float = Field(default=0.0, alias="Power Rate")
    power_mode: Literal["Low", "Normal", "High"] = Field(
        default="Normal", alias="Power Mode"
    )
    power_limit: int = Field(default=0, alias="Power Limit")
    factory_ghs: int = Field(default=0, alias="Factory GHS")
    temperature: float = Field(default=0.0, alias="Temperature")
    env_temp: float = Field(default=0.0, alias="Env Temp")
    chip_temp_min: float = Field(default=0.0, alias="Chip Temp Min")
    chip_temp_max: float = Field(default=0.0, alias="Chip Temp Max")
    chip_temp_avg: float = Field(default=0.0, alias="Chip Temp Avg")
    debug: str = Field(default="", alias="Debug")
    btminer_fast_boot: str = Field(default="disable", alias="Btminer Fast Boot")


class BTMinerPool(BasePool):
    pass


class BTMinerDevice(BaseDev):
    slot: int = Field(alias="Slot")
    temperature: float = Field(default=0.0, alias="Temperature")
    chip_freq: int = Field(default=0, alias="Chip Frequency")
    mhs_5s: float = Field(default=0.0, alias="MHS 5s")
    mhs_1m: float = Field(default=0.0, alias="MHS 1m")
    mhs_15m: float = Field(default=0.0, alias="MHS 15m")
    mhs_avg: float = Field(default=0.0, alias="MHS av")
    factory_ghs: int = Field(default=0, alias="Factory GHS")
    upfreq_complete: int = Field(default=0, alias="Upfreq Complete")
    effective_chips: int = Field(default=0, alias="Effective Chips")
    pcb_sn: str = Field(default="", alias="PCB SN")
    chip_data: str = Field(default="", alias="Chip Data")


class BTMinerDevDetails(BaseDevDetails):
    devdetails: int = Field(alias="DEVDETAILS")
    name: str = Field(alias="Name")
    id: int = Field(alias="ID")
    driver: str = Field(alias="Driver")
    kernel: str = Field(alias="Kernel")
    model: str = Field(alias="Model")


class BTMinerPSU(BaseModel):
    name: str
    hw_version: str
    sw_version: str
    model: str
    iin: int
    vin: int
    pin: int
    fan_speed: int
    version: str
    serial_no: str
    vendor: str
    temp0: float


class BTMinerV3Command(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    cmd: str
    param: str | int | APIObject | list[APIObject] | None = None
    ts: int | None = None
    account: str | None = None
    token: str | None = None


class BTMinerV3CommandResponse(BaseModel):
    code: int
    when: int
    msg: str | APIObject
    desc: str

    def error(self) -> str | None:
        if self.code != 0:
            return f"API error ({self.code}) {self.msg} - {self.desc}"


class BTMinerV3SystemInfo(SystemInfoModel):
    api: str
    platform: str
    fwversion: str
    control_board_version: str = Field(alias="control-board-version")
    btrom: str | None = None
    apiswitch: str
    ledstatus: str


class BTMinerV3NetworkInfo(NetworkInfoModel):
    ip: str
    proto: str
    netmask: str
    dns: str
    mac: str
    gateway: str
    hostname: str


class BTMinerV3Miner(BaseModel):
    working: str
    type: str
    hash_board: str = Field(alias="hash-board")
    detect_hash_rate: str = Field(alias="detect-hash-rate")
    cointype: str
    pool_strategy: str = Field(alias="pool-strategy")
    heatmode: str
    hash_percent: str = Field(alias="hash-percent")
    eeprom_liquid_cooling: str | None = Field(None, alias="eeprom-liquid-cooling")
    chipdata0: str
    chipdata1: str
    chipdata2: str
    fast_boot: str = Field(alias="fast-boot")
    board_num: int = Field(alias="board-num")
    pcbsn0: str
    pcbsn1: str
    pcbsn2: str
    miner_sn: str = Field(alias="miner-sn")
    power_limit_set: str = Field(alias="power-limit-set")
    web_pool: int = Field(alias="web-pool")


class BTMinerV3PSU(BaseModel):
    type: str
    mode: int
    hwversion: str
    swversion: str
    model: str
    iin: float
    vin: float
    vout: int
    pin: int
    fanspeed: int
    temp0: float
    sn: str
    vendor: str


class BTMinerV3DeviceInfo(SystemInfoModel):
    network: BTMinerV3NetworkInfo | None = None
    miner: BTMinerV3Miner | None = None
    system: BTMinerV3SystemInfo | None = None
    power: BTMinerV3PSU | None = None
    salt: str | None = None


class CumulativeStats(BaseModel):
    energy_ws: int = Field(alias="energy-ws")
    total_ths: int = Field(alias="total-ths")
    total_pool_ths: int = Field(alias="total-pool-ths")
    total_secs: int = Field(alias="total-secs")


class PowerOnStats(BaseModel):
    energy_ws: int = Field(alias="energy-ws")
    total_ths: int = Field(alias="total-ths")
    total_pool_ths: int = Field(alias="total-pool-ths")
    reject_percent: float = Field(alias="reject-percent")


class BTMinerV3Summary(SummaryModel):
    elapsed: int
    bootup_time: int = Field(alias="bootup-time")
    freq_avg: int = Field(alias="freq-avg")
    target_freq: int = Field(alias="target-freq")
    factory_hash: float = Field(alias="factory-hash")
    hash_average: float = Field(alias="hash-average")
    hash_1m: float = Field(alias="hash-1min")
    hash_15m: float = Field(alias="hash-15min")
    hash_realtime: float = Field(alias="hash-realtime")
    power_rate: float = Field(alias="power-rate")
    power_5m: float = Field(alias="power-5min")
    cumulative_stats: CumulativeStats | None = Field(None, alias="cumulative-stats")
    power_on_stats: PowerOnStats | None = Field(None, alias="power-on-stats")
    power_realtime: int = Field(alias="power-realtime")
    environment_tempurature: float = Field(alias="environment-tempurature")
    board_tempurature: list[float] = Field(
        alias="board-tempurature", default_factory=list
    )
    chip_temp_min: float = Field(alias="chip-temp-min")
    chip_temp_max: float = Field(alias="chip-temp-max")
    chip_temp_avg: float = Field(alias="chip-temp-avg")
    power_limit: int = Field(alias="power-limit")
    up_freq_finish: int = Field(alias="up-freq-finish")
    fan_speed_in: int = Field(alias="fan-speed-in")
    fan_speed_out: int = Field(alias="fan-speed-out")


class BTMinerV3Pool(MinerPoolModel):
    id: int
    url: str
    status: str
    account: str
    stratum_active: bool = Field(alias="stratum-active")
    reject_rate: float = Field(alias="reject-rate")
    last_share_time: int = Field(alias="last-share-time")


class BTMinerV3Device(BaseDev):
    id: int
    slot: int
    hash_average: float = Field(alias="hash-average")
    factory_hash: float = Field(alias="factory-hash")
    freq: int
    effective_chips: int = Field(alias="effective-chips")
    chip_temp_min: float = Field(alias="chip-temp-min")
    chip_temp_max: float = Field(alias="chip-temp-max")
    chip_temp_avg: float = Field(alias="chip-temp-avg")


class BTMinerV3Status(BaseModel):
    pools: list[BTMinerV3Pool] | None = Field(None, alias="pools")
    edevs: list[BTMinerV3Device] | None = Field(None, alias="edevs")
    summary: BTMinerV3Summary | None = Field(None, alias="summary")


class BTMinerV3PoolConfigParam(BaseModel):
    pool: str
    worker: str
    passwd: str


class BTMinerV3PoolConfig(RootModel[list[BTMinerV3PoolConfigParam]]):
    pass


class BTMinerV3PasswdConfig(BaseModel):
    account: str
    new: str
    old: str
