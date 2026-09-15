# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
import re
import time
import zlib
from typing import Any, ClassVar, override

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_core import from_json
from PySide6.QtCore import QByteArray
from PySide6.QtNetwork import QHostAddress, QNetworkDatagram

from mod.lm.ipreport.patterns import (
    ZLIB_MAGIC,
    ZLIB_OFFSETS,
    MinerTypeHint,
    get_ip_model,
    get_msg_pattern,
    parse_match,
)

logger = logging.getLogger(__name__)


class IPReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    created_at: float = Field(default_factory=time.time)
    updated_at: float = 0
    hint: MinerTypeHint = MinerTypeHint.UNKNOWN
    miner_hint: str = ""
    sort_ip: int = -1
    ip: str = ""
    mac: str = ""
    serial: str = ""


class IPReportDatagram:
    """
    Small wrapper around QNetworkDatagram that facilitates payload validation/parsing into IPReport objects.

    Args:
        datagram (QNetworkDatagram): datagram received
    """

    def __init__(self, datagram: QNetworkDatagram):
        self._dgram: QNetworkDatagram = datagram
        self.src_addr: QHostAddress = self._dgram.senderAddress()
        self.dst_port: int = self._dgram.destinationPort()
        self.data: QByteArray = self._dgram.data()
        self.payload: str = ""
        self.valid: bool = False
        self.report: IPReport = IPReport()
        self._compressed: bool = False

        self._get_miner_hint()
        self._parse_datagram()

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{self.src_addr.toString()}] - {self.report.miner_hint}"

    @property
    def ip_report(self) -> IPReport:
        """Returns the extracted IP report data from the datagram."""
        if self.report.ip == "":
            self.report.ip = self.src_addr.toString()
        self.report.sort_ip = self._sort_ip()
        if self.report.mac == "":
            self.report.mac = self.report.miner_hint
        self.report.mac = self.report.mac.lower()
        return self.report

    def _sort_ip(self) -> int:
        if self.src_addr.isNull():
            return -1
        ipv4 = self.src_addr.toIPv4Address()
        return ipv4[0] if isinstance(ipv4, tuple) else ipv4

    def _get_miner_hint(self) -> None:
        try:
            self.report.hint = MinerTypeHint.from_port(self.dst_port)
        except ValueError:
            pass
        self.report.miner_hint = str(self.report.hint)

    def _decompress_payload(self) -> bool:
        zlib_offset: int = -1
        magic = QByteArray(ZLIB_MAGIC)
        for offset in ZLIB_OFFSETS:
            if self.data.mid(offset, magic.size()) == magic:
                zlib_offset = offset
                break
        if zlib_offset == -1:
            return False
        candidate = self.data.mid(zlib_offset)
        try:
            out = zlib.decompress(candidate.data())
        except zlib.error as ex:
            logger.warning(f"{self.__repr__()}: failed to decompress payload - ignore")
            logger.debug(f"{self.__repr__()}: {ex} - {self.data.data().hex()}")
            return False
        if self.report.hint == MinerTypeHint.SEALMINER:
            # wrap the decompressed data in JSON array to be able to fully parse
            out = b"[" + out + b"]"
        self.data = QByteArray(out)
        return True

    def _unmarshal_payload(self) -> Any:
        # replace null bytes, JSON delimiters, and boolean literals to make the data valid JSON
        self.data = self.data.replace(b"\x00", b"")
        self.data = self.data.replace(b"}{", b"}, {")
        self.data = self.data.replace(b"TRUE", b"true")
        self.data = self.data.replace(b"FALSE", b"false")
        self.payload = self.data.toStdString()
        try:
            return from_json(self.payload)
        except ValueError as ex:
            logger.error(
                f"{self.__repr__()}: failed to unmarshal payload - invalid JSON"
            )
            logger.debug(f"{self.__repr__()}: {ex} - {self.payload}")
            return None

    def _parse_datagram(self) -> None:
        if not self.data.isEmpty():
            self._compressed = self._decompress_payload()
            if not self._compressed and not self.data.isValidUtf8():
                self.valid = False
                return logger.error(
                    f"{self.__repr__()}: failed to parse datagram - invalid UTF-8"
                )
            self.payload = self.data.toStdString().rstrip("\x00")

            # string patterns
            pattern, ok = get_msg_pattern(self.report.hint)
            if ok:
                if not (match := re.match(pattern, self.payload)):
                    self.valid = False
                    return
                self.report.ip, self.report.mac = parse_match(match)
                self.valid = True
                return
            # obj patterns
            if not (obj := self._unmarshal_payload()):
                self.valid = False
                return
            model, ok = get_ip_model(self.report.hint)
            if ok:
                try:
                    model = model.model_validate(obj)
                    self.report.ip, self.report.mac, self.report.serial = (
                        model.ip_report
                    )
                    self.valid = True
                except (TypeError, ValueError, ValidationError):
                    self.valid = False
                    return
        if not self.valid:
            logger.error(f"{self.__repr__()}: failed to validate IP report")
            logger.debug(f"{self.__repr__()}: {self.payload}")
