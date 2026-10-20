from typing import Literal

from pydantic import BaseModel, Field, field_validator

from mod.ipr_asic.schemas.models import (
    NetworkInfoModel,
    PoolConfig,
    SystemInfoModel,
    VersionInfoModel,
)


class ActionResponse(BaseModel):
    decorator: str = ""
    ctx: str = ""
    cxt: str = ""
    success: bool
    message: str | None = ""
    timestamp: int | None = None

    def error(self) -> str | None:
        if self.success:
            return None
        return (
            f"API error: {self.message}" if self.message else "API error: unknown error"
        )


class AuthResponse(ActionResponse):
    jwt: str
    session_id: str = Field(
        default="", validation_alias="org.eclipse.jetty.server.newSessionId"
    )


class VersionInfo(VersionInfoModel):
    model: str = ""
    hardware_version: str = Field("", validation_alias="hardwareVersion")
    release_date: str = Field("", validation_alias="releaseDate")
    kernel_version: str = Field("", validation_alias="kernelVersion")
    miner_version: str = Field("", validation_alias="minerVersion")
    cgminer_version: str = ""
    api_version: str = ""

    @field_validator("miner_version", mode="before")
    @classmethod
    def split_miner_version(cls, v: str) -> None:
        miner_ver = v.split("/")
        cls.cgminer_version = miner_ver[0]
        cls.api_version = miner_ver[1]


class SystemInfo(SystemInfoModel):
    os: str
    kernel_version: str = Field("", validation_alias="kernelVersion")
    usage_mem: int = Field(0, validation_alias="usageMem")
    available_mem: int = Field(0, validation_alias="availableMem")
    cache_mem: int = Field(0, validation_alias="cacheMem")
    load_average: str = Field("", validation_alias="loadAverage")
    total_mem: int = Field(0, validation_alias="totalMem")
    release_date: str = Field("", validation_alias="releaseDate")
    hardware_version: str = Field("", validation_alias="hardwareVersion")
    uptime: str = Field("", validation_alias="upTime")
    protocol: str = Field("", validation_alias="protocol")
    ip: str = Field("", validation_alias="ip")
    mac: str = Field("", validation_alias="macAddress")
    model: str = ""
    miner_version: str = Field("", validation_alias="minerVersion")
    hashboard_serials: list[str] = Field(default_factory=list, validation_alias="sn")

    @field_validator("hashboard_serials", mode="before")
    @classmethod
    def split_hashboard_serials(cls, v: str) -> list[str]:
        return v.split("<br>")

    @field_validator("mac", "load_average", "uptime", mode="after")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class OverviewResponse(ActionResponse):
    miner_info: SystemInfo = Field(validation_alias="minerInfo")


class OverviewResponseVersion(ActionResponse):
    version_info: VersionInfo = Field(validation_alias="minerInfo")


class NetworkInfo(NetworkInfoModel):
    ip: str
    dns: str
    type: str
    gateway: str
    mask: str

    @field_validator("ip", "dns", "type", "gateway", "mask", mode="after")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class NetworkResponse(ActionResponse):
    network_info: NetworkInfo = Field(validation_alias="network")


# updateNetwork
class MinerNetworkConfig(BaseModel):
    type: Literal["static", "dhcp"] = "static"
    ip: str = ""
    mask: str = ""
    gateway: str = ""
    dns: str = ""


class PoolConfigResponse(ActionResponse):
    pools: PoolConfig


class MinerPasswdConfig(BaseModel):
    username: str = ""
    curr_passwd: str = Field("", serialization_alias="curPassword")
    new_passwd: str = Field("", serialization_alias="newPassword")


class MinerPoolConfigForm(BaseModel):
    pool1: str = Field(default="", serialization_alias="Pool1")
    user1: str = Field(default="", serialization_alias="UserName1")
    pass1: str = Field(default="", serialization_alias="Password1")
    pool2: str = Field(default="", serialization_alias="Pool2")
    user2: str = Field(default="", serialization_alias="UserName2")
    pass2: str = Field(default="", serialization_alias="Password2")
    pool3: str = Field(default="", serialization_alias="Pool3")
    user3: str = Field(default="", serialization_alias="UserName3")
    pass3: str = Field(default="", serialization_alias="Password3")


class CGMinerLogResponse(ActionResponse):
    logs: str
