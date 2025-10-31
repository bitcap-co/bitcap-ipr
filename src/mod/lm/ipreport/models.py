from __future__ import annotations

import re
from typing import Annotated, Any, List, Optional

from pydantic import BaseModel, Field, RootModel, TypeAdapter, ValidationError

from .constants import IP_PATTERN, MAC_PATTERN

# IP Report Models
msg_patterns = {
    "common": re.compile(f"^{IP_PATTERN},{MAC_PATTERN}"),
    "ir": re.compile(f"^addr:{IP_PATTERN}"),
    "bt": re.compile(f"^IP:{IP_PATTERN}MAC:{MAC_PATTERN}"),
    "elphapex": re.compile("^DG_IPREPORT_ONLY"),
}


class GoldshellIPReport(BaseModel):
    version: str
    ip: Annotated[str, Field(pattern=rf"^{IP_PATTERN}$")]
    dhcp: str
    model: str
    ctrlsn: str
    mac: Annotated[str, Field(pattern=rf"^{MAC_PATTERN}$")]
    mask: str
    gateway: str
    cpbsn: List[Optional[str]]
    dns: Any
    boxsn: str
    time: str
    ledstatus: bool


class BoardSN(BaseModel):
    sn: Annotated[str, Field(validation_alias="SN")] = ""
    bin_ver: Annotated[int, Field(validation_alias="BinVer")] = 0
    bin_num: Annotated[int, Field(validation_alias="BinNum")] = 0


class MinerInfo(BaseModel):
    mac: Annotated[
        str, Field(pattern=rf"^{MAC_PATTERN}$"), Field(validation_alias="MAC")
    ]
    type: Annotated[str, Field(validation_alias="Type")]
    firmware: Annotated[str, Field(validation_alias="Firmware")]
    ctrl_board: Annotated[str, Field(validation_alias="CtrlBoardVersion")]
    iface_count: Annotated[int, Field(validation_alias="NetInterfaceCnt")]
    upgrade: Annotated[int, Field(validation_alias="UpgradeStatus")]
    serial: Annotated[str, Field(validation_alias="MainBoardSN")]
    rated_power: Annotated[int, Field(validation_alias="RatedInputPower")]
    power_limit: Annotated[int, Field(validation_alias="InputPowerLimit")]
    board_serials: Annotated[List[BoardSN], Field(validation_alias="BoardSnArray")]


class Interface(BaseModel):
    iface: Annotated[str, Field(validation_alias="Interface")]
    active: Annotated[bool, Field(validation_alias="Active")]
    dhcp: Annotated[bool, Field(validation_alias="DHCP")]
    ipv4: Annotated[
        str, Field(pattern=rf"^{IP_PATTERN}$"), Field(validation_alias="IPV4")
    ]
    netmask: Annotated[str, Field(validation_alias="Netmask")]
    gateway: Annotated[str, Field(validation_alias="Gateway")]
    dns1: Annotated[str, Field(validation_alias="DNS1")]
    dns2: Annotated[str, Field(validation_alias="DNS2")]
    auto_reboot: Annotated[bool, Field(validation_alias="AutoReboot")]


class InterfaceList(RootModel):
    root: list[Interface]


class SealMinerIPReport:
    def __init__(self, payload: Any) -> None:
        self._data = payload
        self._validate_model()

    @property
    def info(self) -> MinerInfo:
        return self._info

    @property
    def interfaces(self) -> List[Interface]:
        return self._interfaces

    def _validate_model(self) -> None:
        if not isinstance(self._data, list):
            raise ValueError
        if not len(self._data) or len(self._data) != 7:
            raise ValueError
        try:
            self._info = MinerInfo.model_validate(self._data[1])
            iface_list = TypeAdapter(List[Interface])
            self._interfaces = iface_list.validate_python(self._data[2:4])
        except ValidationError as exc:
            raise exc
