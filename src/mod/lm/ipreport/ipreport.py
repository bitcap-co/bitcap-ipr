import json
import logging
import re
import time
import zlib

from pydantic import BaseModel, ConfigDict, ValidationError
from PySide6.QtNetwork import QNetworkDatagram

from mod.lm.ipreport.patterns import (
    ZLIB_DEFAULT_MAGIC,
    GoldshellIPReport,
    MinerTypeHint,
    SealMinerIPReport,
    msg_patterns,
)

logger = logging.getLogger(__name__)


class IPReport(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    created_at: float
    updated_at: float
    port_type: MinerTypeHint
    src_addr: int
    src_ip: str
    src_mac: str
    miner_type: str
    miner_sn: str


class IPReportDatagram:
    """
    Small wrapper around QNetworkDatagram that tries to parse IP Report messages from various ASIC miners.

    Args:
        datagram QNetworkDatagram: datagram received by Listener.
    """

    def __init__(self, datagram: QNetworkDatagram):
        self.src_addr = datagram.senderAddress()
        self.src_port = datagram.senderPort()
        self.dst_addr = datagram.destinationAddress()
        self.dst_port = datagram.destinationPort()
        self.data = datagram.data()
        self.payload: str = ""
        self.compressed = False
        self.valid = False
        self.created_at = time.time()
        self.port_type = MinerTypeHint(0)
        self.ip_addr: str = ""
        self.mac_addr: str = ""
        self.miner_type: str = ""
        self.miner_sn: str = ""

        self._get_miner_type()
        self._validate_payload()

    @property
    def ip_report(self) -> IPReport:
        """
        Returns:
            IPReport: IP Report data from IPRReportDatagram.
        """
        if not self.mac_addr:
            self.mac_addr = self.miner_type
        addr: int = self.src_addr.toIPv4Address()
        result = IPReport(
            created_at=self.created_at,
            updated_at=0,
            port_type=self.port_type,
            src_addr=addr,
            src_ip=self.ip_addr,
            src_mac=self.mac_addr,
            miner_type=self.miner_type,
            miner_sn=self.miner_sn,
        )
        return result

    def _get_miner_type(self) -> None:
        try:
            self.port_type = MinerTypeHint.from_port(self.dst_port)
        except ValueError:
            pass
        self.miner_type = self.port_type.name.lower()

    def _try_decompress_from_type(self) -> bool:
        decomp = None
        match self.port_type:
            case MinerTypeHint.SEALMINER:
                decomp = self._decompress_sealminer()

        if not decomp:
            logger.warning(
                f"{self.miner_type}[{self.src_addr.toString()}] : unable to decompress. Ignore!"
            )
            return False
        self.payload = decomp.decode().rstrip("\x00")
        return True

    def _decompress_sealminer(self) -> bytes:
        if self.data.contains(ZLIB_DEFAULT_MAGIC):
            data_start = self.data.indexOf(ZLIB_DEFAULT_MAGIC)
            data = self.data.slice(data_start)
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

    def _validate_payload(self) -> bool:
        if not self.data.isEmpty():
            if not self.data.isValidUtf8():
                self.compressed = self._try_decompress_from_type()
                if not self.compressed:
                    logger.error(
                        f"{self.miner_type}[{self.src_addr.toString()}] : invalid datagram. Ignore!"
                    )
                    self.valid = False
                    return False
            else:
                self.payload = self.data.toStdString().rstrip("\x00")

            match self.port_type:
                case MinerTypeHint.COMMON:
                    if re.match(msg_patterns["common"], self.payload):
                        self.ip_addr, self.mac_addr = self.payload.split(",")
                        self.valid = True
                case MinerTypeHint.ICERIVER:
                    if re.match(msg_patterns["ir"], self.payload):
                        self.ip_addr = self.payload.split(":")[1]
                        self.valid = True
                case MinerTypeHint.WHATSMINER:
                    if re.match(msg_patterns["bt"], self.payload):
                        self.ip_addr, self.mac_addr = self.payload.split("M")
                        self.ip_addr = self.ip_addr[3:]
                        self.mac_addr = self.mac_addr[3:]
                        self.valid = True
                case MinerTypeHint.ELPHAPEX:
                    if re.match(msg_patterns["elphapex"], self.payload):
                        self.ip_addr = self.src_addr.toString()
                        self.valid = True
                case MinerTypeHint.SEALMINER:
                    try:
                        obj = json.loads(self.payload)
                    except json.JSONDecodeError:
                        self.valid = False
                    else:
                        try:
                            model = SealMinerIPReport(payload=obj)
                            ip = model.interfaces[1].ipv4
                            mac = model.info.mac
                        except (ValueError, ValidationError):
                            self.valid = False
                        else:
                            self.ip_addr = ip
                            self.mac_addr = mac
                            self.valid = True
                case MinerTypeHint.GOLDSHELL:
                    try:
                        obj = json.loads(self.payload)
                    except json.JSONDecodeError:
                        self.valid = False
                    else:
                        try:
                            model = GoldshellIPReport.model_validate(obj)
                            ip = model.ip
                            mac = model.mac
                        except ValidationError:
                            self.valid = False
                        else:
                            self.ip_addr = ip
                            self.mac_addr = mac
                            self.miner_sn = model.boxsn
                            self.valid = True
                case _:
                    self.valid = False

        if not self.valid:
            logger.error(
                f"{self.miner_type}[{self.src_addr.toString()}] : failed to validate ip report packet"
            )
        return self.valid
