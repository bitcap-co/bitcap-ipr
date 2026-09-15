# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import re
from enum import IntEnum
from typing import Any, ClassVar, override

from pydantic import BaseModel, ConfigDict, Field, RootModel

ZLIB_MAGIC = b"\x78"
_ZLIB_SEALMINER_OFFSET: int = 8
ZLIB_OFFSETS: list[int] = [0, _ZLIB_SEALMINER_OFFSET]

_IP_PATTERN = (
    r"((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.)){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
)
_MAC_PATTERN = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"


class MinerTypeHint(IntEnum):
    UNKNOWN = 0
    COMMON = 14235
    ICERIVER = 11503
    WHATSMINER = 8888
    SEALMINER = 18650
    GOLDSHELL = 1314
    ELPHAPEX = 9999
    AURADINE = 12345
    IPOLLO = 54321
    HIVEGPU = 42069

    @override
    def __str__(self) -> str:
        # return "antminer" as generic name
        if self == MinerTypeHint.COMMON:
            return "antminer"
        return str(self.name.lower())

    @property
    def display_name(self) -> str:
        return self.__str__().capitalize()

    @classmethod
    def from_port(cls, port: int):
        """Create a MinerTypeHint from a port number.

        Raises:
            ValueError: If the port is not a valid miner port.
        """
        return cls(port)


_MSG_PATTERNS = {
    MinerTypeHint.COMMON: re.compile(f"^(?P<IP>{_IP_PATTERN}),(?P<MAC>{_MAC_PATTERN})"),
    MinerTypeHint.ICERIVER: re.compile(f"^addr:(?P<IP>{_IP_PATTERN})"),
    MinerTypeHint.WHATSMINER: re.compile(
        f"^IP:(?P<IP>{_IP_PATTERN})MAC:(?P<MAC>{_MAC_PATTERN})"
    ),
    MinerTypeHint.ELPHAPEX: re.compile("^DG_IPREPORT_ONLY"),
    MinerTypeHint.IPOLLO: re.compile(
        f"^IP Addr:\\[(?P<IP>{_IP_PATTERN})\\].*?MAC Addr:\\[(?P<MAC>{_MAC_PATTERN})\\]"
    ),
    MinerTypeHint.HIVEGPU: re.compile(f"^HiveOS (?P<IP>{_IP_PATTERN})"),
}


def get_msg_pattern(hint: MinerTypeHint) -> tuple[re.Pattern[str], bool]:
    """Get the message pattern for the given miner type hint.
    Returns a tuple of the pattern and a boolean indicating if the pattern was found.
    """
    if hint in _MSG_PATTERNS:
        return _MSG_PATTERNS[hint], True
    return re.compile(""), False


def parse_match(match: re.Match[str]) -> tuple[str, str]:
    """Parse a match object from a message pattern.
    Returns the extracted IP and MAC as a tuple.
    """
    ip = mac = ""
    for name, value in match.groupdict().items():
        if name == "IP":
            ip = value
        elif name == "MAC":
            mac = value
    return ip, mac


class IPReportModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(validate_assignment=True)
    ip: str = Field(default="", pattern=rf"^{_IP_PATTERN}$")
    mac: str = Field(default="", pattern=rf"^{_MAC_PATTERN}$")
    serial: str = ""

    @property
    def ip_report(self) -> tuple[str, str, str]:
        """Returns the IP, MAC, and serial as a tuple."""
        return self.ip, self.mac, self.serial


class GoldshellIPReport(IPReportModel):
    version: str
    dhcp: str
    model: str
    ctrlsn: str
    mask: str
    gateway: str
    cpbsn: list[str | None]
    serial: str = Field(default="", validation_alias="boxsn")
    time: str
    ledstatus: bool


class BoardInfo(BaseModel):
    sn: str = Field("", validation_alias="SN")
    bin_ver: int = Field(0, validation_alias="BinVer")
    bin_num: int = Field(0, validation_alias="BinNum")


class Info(BaseModel):
    mac: str = Field(validation_alias="MAC")
    type: str = Field(validation_alias="Type")
    firmware: str = Field(validation_alias="Firmware")
    ctrl_board_version: str = Field(validation_alias="CtrlBoardVersion")
    net_interface_cnt: int = Field(validation_alias="NetInterfaceCnt")
    upgrade_status: int = Field(validation_alias="UpgradeStatus")
    main_board_sn: str = Field(validation_alias="MainBoardSN")
    rated_input_power: int = Field(validation_alias="RatedInputPower")
    input_power_limit: int = Field(validation_alias="InputPowerLimit")
    board_sn_array: list[BoardInfo] = Field(validation_alias="BoardSnArray")


class Interface(BaseModel):
    interface: str = Field(validation_alias="Interface")
    active: bool = Field(validation_alias="Active")
    dhcp: bool = Field(validation_alias="DHCP")
    ipv4: str = Field(validation_alias="IPV4")
    netmask: str = Field(validation_alias="Netmask")
    gateway: str = Field(validation_alias="Gateway")
    dns1: str = Field(validation_alias="DNS1")
    dns2: str = Field(validation_alias="DNS2")
    auto_reboot: bool = Field(validation_alias="AutoReboot")


class InterfaceList(RootModel[list[Interface]]):
    root: list[Interface]


class SealMinerIPReport(IPReportModel):
    def __init__(self) -> None:
        super().__init__()

    @override
    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> "SealMinerIPReport":
        if not isinstance(obj, list):
            raise TypeError
        if not len(obj) or len(obj) != 7:
            raise ValueError
        info = Info.model_validate(obj[1])
        interfaces = InterfaceList.model_validate(obj[2 : 2 + info.net_interface_cnt])
        self = cls()
        active_interfaces = [i for i in interfaces.root if i.active]
        if active_interfaces:
            self.ip = active_interfaces[0].ipv4
        self.mac = info.mac
        return self


class AuradineIPReport(IPReportModel):
    command: str
    serial_no: str = Field(validation_alias="SerialNo")
    model: str
    version: str
    hostname: str
    internal_type: str | None = Field(None, validation_alias="InternalType")


_OBJ_MODELS = {
    MinerTypeHint.AURADINE: AuradineIPReport,
    MinerTypeHint.GOLDSHELL: GoldshellIPReport,
    MinerTypeHint.SEALMINER: SealMinerIPReport,
}


def get_ip_model(hint: MinerTypeHint) -> tuple[type[IPReportModel], bool]:
    """Get the IP report model for the given miner type hint.
    Returns a tuple of the model and a boolean indicating if the model was found.
    """
    if hint in _OBJ_MODELS:
        return _OBJ_MODELS[hint], True
    return IPReportModel, False
