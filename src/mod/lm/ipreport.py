import logging
import re
import json
from typing import List, Optional
import zlib

from PySide6.QtNetwork import QNetworkDatagram

reg_ip = r"((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?){4}"
reg_mac = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
msg_patterns = {
    "common": re.compile(f"^{reg_ip},{reg_mac}"),
    "ir": re.compile(f"^addr:{reg_ip}"),
    "bt": re.compile(f"^IP:{reg_ip}MAC:{reg_mac}"),
    "elphapex": re.compile("^DG_IPREPORT_ONLY"),
}
ZLIB_DEFAULT_MAGIC = b"\x78\x9c"

logger = logging.getLogger(__name__)


class IPReportDatagram:
    """
    Small wrapper around QNetworkDatagram that automatically handles IP Report messages from various miners.

    Args:
        datagram: QNetworkDatagram - initial datagram received by Listener.

    Automatically finds miner type based off of the destination port. Based off of the miner type,
    it will process the datagram data and sets the flag `is_msg_valid` if valid.
    """

    def __init__(self, datagram: QNetworkDatagram):
        self.src_addr: str = datagram.senderAddress().toString()
        self.src_port: int = datagram.senderPort()
        self.dst_addr: str = datagram.destinationAddress().toString()
        self.dst_port: int = datagram.destinationPort()
        self.data: bytes = datagram.data().data()
        self.msg: Optional[str] = None
        self.is_msg_valid = False
        self.is_msg_compressed = False
        self.miner_type = ""

        self.__get_miner_type_from_port()
        self.__validate_msg_from_type()

    def __get_miner_type_from_port(self) -> None:
        match self.dst_port:
            case 14235:  # common port
                self.miner_type = "bitmain-common"
            case 11503:
                self.miner_type = "iceriver"
            case 8888:
                self.miner_type = "whatsminer"
            case 18650:
                self.miner_type = "sealminer"
                self.is_msg_compressed = True
            case 1314:
                self.miner_type = "goldshell"
            case 9999:
                self.miner_type = "elphapex"

    def __decompress_sealminer(self) -> bytes:
        # sealminer data is compressed with ZLIB_DEFAULT compression
        data_start = self.data.find(ZLIB_DEFAULT_MAGIC)
        data = self.data[data_start:]
        try:
            out = zlib.decompress(data)
        except zlib.errror as e:
            raise e
        # fix data to valid json
        out = out.replace(b"\x00", b"")
        out = out.replace(b"}{", b"}, {")
        out = b"[" + out + b"]"
        return out

    def __decompress_data_from_type(self):
        match self.miner_type:
            case "sealminer":
                try:
                    self.msg = self.__decompress_sealminer()
                except zlib.error as e:
                    self.msg = ""
                    logger.debug(
                        f"{self.miner_type}[{self.src_addr}] : decompress err: {e}"
                    )
        if self.msg == "":
            logger.error(
                f"{self.miner_type}[{self.src_addr}] : failed to decompress data message. Ignore!"
            )

    def __msg_to_json(self) -> bool:
        try:
            self.msg = json.loads(self.msg)
            return True
        except json.JSONDecodeError:
            return False

    def __validate_msg_from_type(self):
        if self.data:
            if self.is_msg_compressed:
                self.__decompress_data_from_type()
            else:
                try:
                    self.msg = self.data.decode().rstrip("\x00")
                except UnicodeDecodeError:
                    logger.debug(self.data)
                    logger.warning(
                        f"{self.miner_type}[{self.src_addr}] : failed to decode datagram. Possibly intercepted from another source."
                    )
                    return

            match self.miner_type:
                case "bitmain-common":
                    if re.match(msg_patterns["common"], self.msg):
                        self.is_msg_valid = True
                case "iceriver":
                    if re.match(msg_patterns["ir"], self.msg):
                        self.is_msg_valid = True
                case "whatsminer":
                    if re.match(msg_patterns["bt"], self.msg):
                        self.is_msg_valid = True
                case "elphapex":
                    if re.match(msg_patterns["elphapex"], self.msg):
                        self.is_msg_valid = True
                case "sealminer":
                    if self.__msg_to_json():
                        if re.match(reg_ip, self.msg[3]["IPV4"]) and re.match(
                            reg_mac, self.msg[1]["MAC"]
                        ):
                            self.is_msg_valid = True
                case "goldshell":
                    if self.__msg_to_json():
                        if re.match(reg_ip, self.msg["ip"]) and re.match(
                            reg_mac, self.msg["mac"]
                        ):
                            self.is_msg_valid = True
        if not self.is_msg_valid:
            logger.error(
                f"{self.miner_type}[{self.src_addr}] : failed to validate data message. Ignore!"
            )

    def parse_msg(self) -> List[str]:
        mac = ""
        sn = ""
        match self.miner_type:
            case "bitmain-common":
                ip, mac = self.msg.split(",")
            case "iceriver":
                ip = self.msg.split(":")[1]
            case "whatsminer":
                ip, mac = self.msg.split("M")
                ip = ip[3:]
                mac = mac[3:]
            case "elphapex":
                ip = self.src_addr
            case "sealminer":
                ip = self.msg[3]["IPV4"]
                mac = self.msg[1]["MAC"]
            case "goldshell":
                ip = self.msg["ip"]
                mac = self.msg["mac"]
                if "boxsn" in self.msg:
                    sn = self.msg["boxsn"]
        if not mac:
            mac = self.miner_type
        return [ip, mac, self.miner_type, sn]
