from typing import Any

from pydantic import BaseModel, Field

from mod.ipr_asic.schemas.models import (
    MinerConfigModel,
    MinerPoolModel,
    NetworkInfoModel,
    SummaryModel,
    SystemInfoModel,
)


class ActionResult(BaseModel):
    error: int
    message: str
    data: dict[str, Any] = Field(default_factory=dict)

    def error_(self) -> str | None:
        if self.error != 0:
            return f"API Error ({self.error}): {self.message}"


class NetworkInfo(NetworkInfoModel):
    nic: str
    mac: str
    ip: str
    netmask: str
    host: str
    dhcp: bool
    gateway: str
    dns: str


class MinerPool(MinerPoolModel):
    no: int
    addr: str
    user: str
    passwd: str = Field(validation_alias="pass")
    connect: int
    diff: str
    priority: int
    accepted: int
    rejected: int
    diffa: int
    diffr: int
    state: int
    lsdiff: int
    lstime: str


class MinerConfig(MinerConfigModel):
    pools: list[MinerPool]
    ratio: int
    mode: int
    locate: int


class MinerStatus(BaseModel):
    netstate: bool
    powstate: bool
    tempstate: bool
    fanstate: bool


class Board(BaseModel):
    no: int
    chipnum: int
    chipsuc: int
    error: int
    freq: int
    rtpow: str
    avgpow: str
    idealpow: str
    pcbtemp: str
    intmp: int
    outtmp: int
    state: bool
    false: list[int]


class UserPanel(SummaryModel, SystemInfoModel):
    nic: str
    mac: str
    ip: str
    netmask: str
    host: str
    dhcp: bool
    gateway: str
    dns: str
    model: str
    algo: str
    online: bool
    firmver1: str
    firmver2: str
    softver1: str
    softver2: str
    firmtype: str
    locate: bool
    rtpow: str
    avgpow: str
    reject: float
    runtime: str
    unit: str
    netstate: bool
    powstate: bool
    tempstate: bool
    fanstate: bool
    fans: list[int]
    pools: list[MinerPool]
    boards: list[Board]
    reftime: str = Field(alias="refTime")


class MinerConfigPasswd(BaseModel):
    curr_passwd: str = Field(alias="nowpwd")
    new_passwd: str = Field(alias="newpwd")
    confirm_passwd: str = Field(alias="compwd")
