# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import ipaddress
import re
from enum import IntEnum
from typing import Any, override

from pydantic import BaseModel, Field, RootModel

ZLIB_MAGIC = b"\x78"
_ZLIB_SEALMINER_OFFSET: int = 8
ZLIB_OFFSETS: list[int] = [0, _ZLIB_SEALMINER_OFFSET]

_IP_PATTERN = (
    r"((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.)){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
)
_MAC_PATTERN = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"


def parse_ipv4(addr: str) -> str:
    if addr == "":
        raise ValueError("IP address is empty")
    addr = addr.strip()
    try:
        addr = str(ipaddress.IPv4Address(addr))
    except ipaddress.AddressValueError:
        raise ValueError("invalid IP address")
    return addr


def parse_mac(addr: str) -> str:
    if addr == "":
        raise ValueError("MAC address is empty")
    addr = addr.strip().lower()
    match len(addr):
        case 17:
            addr = addr.replace("-", ":")
        case 12:
            addr = ":".join(addr[i : i + 2] for i in range(0, 12, 2))
        case _:
            raise ValueError("invalid MAC address length")
    if not re.match(_MAC_PATTERN, addr):
        raise ValueError("invalid MAC address")
    return addr


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
    IBELINK = 6667

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
    MinerTypeHint.COMMON: re.compile(
        f"^(?P<IP>{_IP_PATTERN}),(?P<MAC>{_MAC_PATTERN})$"
    ),
    MinerTypeHint.ICERIVER: re.compile(f"^addr:(?P<IP>{_IP_PATTERN})$"),
    MinerTypeHint.WHATSMINER: re.compile(
        f"^IP:(?P<IP>{_IP_PATTERN})MAC:(?P<MAC>{_MAC_PATTERN})$"
    ),
    MinerTypeHint.ELPHAPEX: re.compile("^DG_IPREPORT_ONLY$"),
    MinerTypeHint.IPOLLO: re.compile(
        f"^IP Addr:\\[(?P<IP>{_IP_PATTERN})\\].*?MAC Addr:\\[(?P<MAC>{_MAC_PATTERN})\\]"
    ),
    MinerTypeHint.HIVEGPU: re.compile(f"^HiveOS (?P<IP>{_IP_PATTERN})$"),
}


def get_msg_pattern(hint: MinerTypeHint) -> tuple[re.Pattern[str], bool]:
    """Get the message pattern for the given miner type hint.
    Returns a tuple of the pattern and a boolean indicating if the pattern was found.
    """
    if hint in _MSG_PATTERNS:
        return _MSG_PATTERNS[hint], True
    return re.compile(""), False


def parse_pattern_match(match: re.Match[str]) -> tuple[str, str]:
    """Parse a match object from a message pattern.
    Returns the extracted IP and MAC as a tuple.
    """
    ip = parse_ipv4(match.group("IP")) if "IP" in match.groupdict() else ""
    mac = parse_mac(match.group("MAC")) if "MAC" in match.groupdict() else ""
    return ip, mac


class IPReportModel(BaseModel):
    ip: str = ""
    mac: str = ""
    serial: str = ""

    @property
    def ip_report(self) -> tuple[str, str, str]:
        return self.ip, self.mac, self.serial

    @classmethod
    def parse_json(cls, data: Any) -> "IPReportModel":
        if not data:
            raise ValueError("data is empty")
        obj = cls.model_validate(data)
        obj.ip = parse_ipv4(obj.ip)
        obj.mac = parse_mac(obj.mac)
        return obj

    @classmethod
    def parse_data(cls, data: bytes) -> "IPReportModel":
        raise NotImplementedError(f"parse_data is not implemented for {cls.__name__}")


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


class SealminerBoardInfo(BaseModel):
    sn: str = Field("", validation_alias="SN")
    bin_ver: int = Field(0, validation_alias="BinVer")
    bin_num: int = Field(0, validation_alias="BinNum")


class SealminerInfo(BaseModel):
    mac: str = Field(validation_alias="MAC")
    type: str = Field(validation_alias="Type")
    firmware: str = Field(validation_alias="Firmware")
    ctrl_board_version: str = Field(validation_alias="CtrlBoardVersion")
    net_interface_cnt: int = Field(validation_alias="NetInterfaceCnt")
    upgrade_status: int = Field(validation_alias="UpgradeStatus")
    main_board_sn: str = Field(validation_alias="MainBoardSN")
    rated_input_power: int = Field(validation_alias="RatedInputPower")
    input_power_limit: int = Field(validation_alias="InputPowerLimit")
    board_sn_array: list[SealminerBoardInfo] = Field(validation_alias="BoardSnArray")


class SealminerInterface(BaseModel):
    interface: str = Field(validation_alias="Interface")
    active: bool = Field(validation_alias="Active")
    dhcp: bool = Field(validation_alias="DHCP")
    ipv4: str = Field(validation_alias="IPV4")
    netmask: str = Field(validation_alias="Netmask")
    gateway: str = Field(validation_alias="Gateway")
    dns1: str = Field(validation_alias="DNS1")
    dns2: str = Field(validation_alias="DNS2")
    auto_reboot: bool = Field(validation_alias="AutoReboot")


class SealminerInterfaceList(RootModel[list[SealminerInterface]]):
    root: list[SealminerInterface]


class SealminerIPReport(IPReportModel):
    info: SealminerInfo
    interfaces: SealminerInterfaceList

    @override
    @classmethod
    def parse_json(cls, data: Any) -> "SealminerIPReport":
        if not data:
            raise ValueError("data is empty")
        if not isinstance(data, list):
            raise TypeError("data is not an array")
        if not len(data) or len(data) != 7:
            raise ValueError(f"invalid data length: {len(data)}")
        info = SealminerInfo.model_validate(data[1])
        interfaces = SealminerInterfaceList.model_validate(
            data[2 : 2 + info.net_interface_cnt]
        )
        model = cls(info=info, interfaces=interfaces)
        active_interfaces = [i for i in interfaces.root if i.active]
        if active_interfaces:
            model.ip = parse_ipv4(active_interfaces[0].ipv4)
        model.mac = parse_mac(info.mac)
        return model


class AuradineIPReport(IPReportModel):
    command: str
    serial_no: str = Field(validation_alias="SerialNo")
    model: str
    version: str
    hostname: str
    internal_type: str | None = Field(None, validation_alias="InternalType")


_IBELINK_MAGIC = b"AZZ\xf0\x01"
_IBELINK_HEADER_SIZE = 8
_IBELINK_ADDRESS_FIELDS = 4


class IBeLinkIPReport(IPReportModel):
    @override
    @classmethod
    def parse_data(cls, data: bytes) -> "IBeLinkIPReport":
        if not data:
            raise ValueError("data is empty")
        if len(data) < _IBELINK_HEADER_SIZE:
            raise ValueError(f"data is too short: {len(data)}")
        if not data.startswith(_IBELINK_MAGIC):
            raise ValueError("invalid magic")

        fields = [
            field for field in data[_IBELINK_HEADER_SIZE:].split(b"\x00") if field
        ][:_IBELINK_ADDRESS_FIELDS]
        if len(fields) < _IBELINK_ADDRESS_FIELDS:
            raise ValueError("invalid data length")

        raw_ip, _, _, raw_mac = (field.decode(encoding="ascii") for field in fields)
        model = cls()
        model.ip = parse_ipv4(raw_ip)
        model.mac = parse_mac(raw_mac)
        return model


_OBJ_MODELS = {
    MinerTypeHint.AURADINE: AuradineIPReport,
    MinerTypeHint.GOLDSHELL: GoldshellIPReport,
    MinerTypeHint.SEALMINER: SealminerIPReport,
    MinerTypeHint.IBELINK: IBeLinkIPReport,
}


def get_ip_model(hint: MinerTypeHint) -> tuple[type[IPReportModel], bool]:
    """Get the IP report model for the given miner type hint.
    Returns a tuple of the model and a boolean indicating if the model was found.
    """
    if hint in _OBJ_MODELS:
        return _OBJ_MODELS[hint], True
    return IPReportModel, False
