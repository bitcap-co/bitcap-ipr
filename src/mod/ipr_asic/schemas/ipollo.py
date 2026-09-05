from typing import Literal

from pydantic import BaseModel, Field

from src.mod.ipr_asic.schemas.models import (
    MinerConfigModel,
    MinerPoolConfig,
    MinerPoolModel,
    NetworkInfoModel,
    SummaryModel,
    SystemInfoModel,
)


class SystemSwap(BaseModel):
    free: int
    total: int


class SystemMemory(BaseModel):
    buffered: int
    total: int
    shared: int
    free: int


class SystemWAN(BaseModel):
    proto: str
    ipaddr: str
    netmask: str
    gwaddr: str
    uptime: int
    ifname: str
    dns: list[str]


class SystemInfo(SystemInfoModel):
    swap: SystemSwap
    conncount: int
    memory: SystemMemory
    uptime: int
    wan: SystemWAN
    localtime: str


class MinerPool(MinerPoolModel):
    pool: int
    user: str
    url: str
    accept: int
    diff: int


class MinerStatus(SummaryModel):
    pool: list[MinerPool]
    temp: str | None
    fan: str | None
    accepted: int | None
    rejected: int | None
    unit: str | None
    version: str
    algo: str | None
    mmodel: str | None
    hashrate: float | None


class IPAddresses(BaseModel):
    netmask: str
    addr: str
    prefix: int


class Subdevice(BaseModel):
    type: str
    name: str
    macaddr: str
    is_up: bool
    ifname: str


class Interface(BaseModel):
    ifname: str
    ipaddrs: list[IPAddresses]
    gwaddr: str
    dnsaddrs: list[str]
    proto: str
    id: str
    uptime: int
    subdevices: list[Subdevice]
    is_up: bool
    macaddr: str
    type: str
    name: str


class NetworkInfo(NetworkInfoModel):
    ifaces: list[Interface]


class MinerSubmitForm(BaseModel):
    submit: int | None = Field(default=1, serialization_alias="cbi.submit")
    apply: Literal["Save & Apply"] = Field(
        default="Save & Apply", serialization_alias="cbi.apply"
    )


class MinerNetworkConfig(MinerSubmitForm):
    proto: Literal["dhcp", "static"] = Field(
        "dhcp", serialization_alias="cbid.network.lan.proto"
    )
    ipaddr: str | None = Field(None, serialization_alias="cbid.network.lan.ipaddr")
    netmask: str | None = Field(None, serialization_alias="cbid.network.lan.netmask")
    gateway: str | None = Field(None, serialization_alias="cbid.network.lan.gateway")
    dns: str | None = Field(None, serialization_alias="cbid.network.lan.dns")


class MinerConfig(MinerSubmitForm, MinerConfigModel):
    show_fan: Literal["fan1", "fan2", "fan3", "fan4"] = Field(
        "fan1", serialization_alias="cbid.cgminer.default.show_fan"
    )
    show_temp: Literal["temp1", "temp2", "temp3", "temp4", "temp5", "temp6"] = Field(
        "temp2", serialization_alias="cbid.cgminer.default.show_temp"
    )
    alarm_temp: int = Field(
        90, ge=-55, le=155, serialization_alias="cbid.cgminer.default.asic_alarm_temp"
    )
    fan_min: int = Field(
        20, ge=0, le=100, serialization_alias="cbid.cgminer.default.fan_min"
    )
    fan_max: int = Field(
        100, ge=0, le=100, serialization_alias="cbid.cgminer.default.fan_max"
    )
    default_pwm: int = Field(
        30, ge=0, le=100, serialization_alias="cbid.cgminer.default.pwm_default"
    )
    fan_ctrl: int = Field(
        1, ge=0, le=1, serialization_alias="cbid.cgminer.default.fan_ctrl"
    )
    pre_boot_time: int = Field(
        3, ge=0, le=10, serialization_alias="cbid.cgminer.default.pre_boot_time"
    )
    pre_boot_fan: int = Field(
        100, ge=0, le=100, serialization_alias="cbid.cgminer.default.pre_boot_fan"
    )


class MinerConfigPool(MinerSubmitForm):
    select_coin: Literal["mwc", "grin"] = Field(
        "mwc", serialization_alias="cbid.cgminer.default.select_coin"
    )
    mwc_pool1_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool1url"
    )
    mwc_pool1_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool1user"
    )
    mwc_pool1_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool1pw"
    )
    mwc_pool2_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool2url"
    )
    mwc_pool2_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool2user"
    )
    mwc_pool2_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool2pw"
    )
    mwc_pool3_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool3url"
    )
    mwc_pool3_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool3user"
    )
    mwc_pool3_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool3pw"
    )
    grin_pool1_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool1url"
    )
    grin_pool1_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool1user"
    )
    grin_pool1_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool1pw"
    )
    grin_pool2_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool2url"
    )
    grin_pool2_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool2user"
    )
    grin_pool2_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool2pw"
    )
    grin_pool3_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool3url"
    )
    grin_pool3_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool3user"
    )
    grin_pool3_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool3pw"
    )
    api_allow: str = Field("", serialization_alias="cbid.cgminer.default.api_allow")
    more_options: str = Field(
        "", serialization_alias="cbid.cgminer.default.more_options"
    )
    ntp_enable: str = Field("", serialization_alias="cbid.cgminer.default.ntp_enable")

    def active_pools(self) -> list[MinerPoolConfig]:
        coin = self.select_coin
        return [
            MinerPoolConfig.model_validate(
                {
                    "url": getattr(self, f"{coin}_pool{index}_url"),
                    "user": getattr(self, f"{coin}_pool{index}_user"),
                    "pass": getattr(self, f"{coin}_pool{index}_pw"),
                }
            )
            for index in range(1, 4)
        ]


class MinerPasswdConfig(MinerSubmitForm):
    new_passwd: str = Field(default="", serialization_alias="cbid.system._pass.pw1")
    confirm_passwd: str = Field(default="", serialization_alias="cbid.system._pass.pw2")
