import json
import logging
import re
import time
import zlib
from typing import List

from pydantic import ValidationError
from PySide6.QtNetwork import QNetworkDatagram

from .constants import (
    ZLIB_DEFAULT_MAGIC,
    PortType,
)
from .models import GoldshellIPReport, SealMinerIPReport, msg_patterns

logger = logging.getLogger(__name__)


class IPReportDatagram:
    """
    Small wrapper around QNetworkDatagram that automatically handle IP Report messages from various ASIC types.

    Args:
        datagram: QNetworkDatagram - initial datagram received by Listener.
    """

    def __init__(self, datagram: QNetworkDatagram):
        self._src_addr = datagram.senderAddress().toString()
        self._src_port = datagram.senderPort()
        self._dst_addr = datagram.destinationAddress().toString()
        self._dst_port = datagram.destinationPort()
        self._data = datagram.data()
        self._is_valid = False
        self._port_type = PortType(0)
        self._is_compressed = False
        self._created_at = time.time()
        self._msg = ""
        self._ip_addr = ""
        self._mac_addr = ""
        self._miner_type = ""
        self._serial = ""

        self._get_miner_type()
        self._validate_msg()

    @property
    def valid(self) -> bool:
        return self._is_valid

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def ip(self) -> str:
        return self._ip_addr

    @property
    def mac(self) -> str:
        return self._mac_addr

    @property
    def miner_type(self) -> str:
        return self._miner_type

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def result(self) -> List[str]:
        if not self._mac_addr:
            self._mac_addr = self._miner_type
        return [
            self._ip_addr,
            self._mac_addr,
            self._miner_type,
            self._serial,
        ]

    def _get_miner_type(self):
        try:
            self._port_type = PortType.from_port(self._dst_port)
        except ValueError:
            pass
        self._miner_type = self._port_type.name.lower()

    def _try_decompress_from_type(self) -> bool:
        decomp = None
        match self._port_type:
            case PortType.SEALMINER:
                decomp = self._decompress_sealminer()

        if not decomp:
            logger.warning(
                f"{self._miner_type}[{self._src_addr}] : unable to decompress. Ignore"
            )
            return False
        self._msg = decomp.decode().rstrip("\x00")
        return True

    def _decompress_sealminer(self) -> bytes:
        if self._data.contains(ZLIB_DEFAULT_MAGIC):
            data_start = self._data.indexOf(ZLIB_DEFAULT_MAGIC)
            data = self._data.slice(data_start)
            try:
                out = zlib.decompress(data.data())
            except zlib.error:
                return bytes()
            else:
                # fix data to be valid json
                out = out.replace(b"\x00", b"")
                out = out.replace(b"}{", b"}, {")
                out = b"[" + out + b"]"
                return out
        return bytes()

    def _validate_msg(self) -> bool:
        if not self._data.isEmpty():
            if not self._data.isValidUtf8():
                self._is_compressed = self._try_decompress_from_type()
                if not self._is_compressed:
                    logger.error(
                        f"{self._miner_type}[{self._src_addr}] : failed to decode datagram. Ignore!"
                    )
                    self._is_valid = False
                    return False
            else:
                self._msg = self._data.toStdString().rstrip("\x00")

            match self._port_type:
                case PortType.COMMON:
                    if re.match(msg_patterns["common"], self._msg):
                        self._is_valid = True
                        self._ip_addr, self._mac_addr = self._msg.split(",")
                case PortType.ICERIVER:
                    if re.match(msg_patterns["ir"], self._msg):
                        self._is_valid = True
                        self._ip_addr = self._msg.split(":")[1]
                case PortType.WHATSMINER:
                    if re.match(msg_patterns["bt"], self._msg):
                        self._is_valid = True
                        self._ip_addr, self._mac_addr = self._msg.split("M")
                        self._ip_addr = self._ip_addr[3:]
                        self._mac_addr = self._mac_addr[3:]
                case PortType.ELPHAPEX:
                    if re.match(msg_patterns["elphapex"], self._msg):
                        self._is_valid = True
                        self._ip_addr = self._src_addr
                case PortType.SEALMINER:
                    try:
                        obj = json.loads(self._msg)
                    except json.JSONDecodeError:
                        self._is_valid = False
                    else:
                        try:
                            model = SealMinerIPReport(payload=obj)
                            ip = model.interfaces[1].ipv4
                            mac = model.info.mac
                        except (ValueError, ValidationError):
                            self._is_valid = False
                        else:
                            self._is_valid = True
                            self._ip_addr = ip
                            self._mac_addr = mac
                case PortType.GOLDSHELL:
                    try:
                        obj = json.loads(self._msg)
                    except json.JSONDecodeError:
                        self._is_valid = False
                    else:
                        try:
                            model = GoldshellIPReport.model_validate(obj)
                            ip = model.ip
                            mac = model.mac
                        except ValidationError:
                            self._is_valid = False
                        else:
                            self._is_valid = True
                            self._ip_addr = ip
                            self._mac_addr = mac
                            self._serial = model.boxsn
                case _:
                    self._is_valid = False

        if not self._is_valid:
            logger.error(
                f"{self._miner_type}[{self._src_addr}] : failed to validate ip report packet. Ignore!"
            )
        return self._is_valid
