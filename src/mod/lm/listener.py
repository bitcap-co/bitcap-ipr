import time
import re
import logging
import json
import zlib

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QUdpSocket, QHostAddress


logger = logging.getLogger(__name__)

reg_ip = r"((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?){4}"
reg_mac = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
msg_patterns = {
    "common": re.compile(f"^{reg_ip},{reg_mac}"),
    "ir": re.compile(f"^addr:{reg_ip}"),
    "bt": re.compile(f"^IP:{reg_ip}MAC:{reg_mac}"),
}
RECORD_MIN_AGE = 10.0
ZLIB_DEFAULT_MAGIC = b"\x78\x9c"


class Record:
    def __init__(self, size: int):
        self.size = size
        self.dict = {}

    def __setitem__(self, key, value):
        if len(self.dict) >= self.size:
            self.dict.popitem()
        self.dict[key] = value

    def __getitem__(self, key):
        return self.dict[key]


class Listener(QObject):
    result = Signal(str)
    error = Signal()

    def __init__(self, parent: QObject, port: int):
        super().__init__(parent)
        self.port = port
        self.max_buf = 1024
        self.record = Record(size=10)
        self.msg = ""
        self.addr = QHostAddress()
        self.addr.setAddress(QHostAddress.SpecialAddress.AnyIPv4)
        self.sock = QUdpSocket()
        self.bound = self.sock.bind(self.addr, self.port)

        self.sock.errorOccurred.connect(self.emit_error)
        self.sock.readyRead.connect(self.process_datagram)

    def validate_json(self) -> bool:
        try:
            self.msg = json.loads(self.msg)
            return True
        except json.JSONDecodeError:
            logger.error(
                f"Listener[{self.port}] : Failed to decode json msg."
            )
            return False

    def validate_msg(self, type: str) -> bool:
        match type:
            case "antminer":
                if re.match(msg_patterns["common"], self.msg):
                    return True
            case "whatsminer":
                if re.match(msg_patterns["bt"], self.msg):
                    return True
            case "iceriver":
                if re.match(msg_patterns["ir"], self.msg):
                    return True
            case "goldshell":
                if self.validate_json():
                    if re.match(reg_ip, self.msg["ip"]) and re.match(reg_mac, self.msg["mac"]):
                        return True
            case "sealminer":
                if self.validate_json():
                    if re.match(reg_ip, self.msg[3]["IPV4"]) and re.match(reg_mac, self.msg[1]["MAC"]):
                        return True
        logger.warning(f"Listener[{self.port}] : Failed to validate msg. Ignoring...")
        return False

    def parse_msg(self, type: str) -> tuple:
        sn = ""
        match type:
            case "antminer":
                ip, mac = self.msg.split(",")
            case "whatsminer":
                ip, mac = self.msg.split("M")
                ip = ip[3:]
                mac = mac[3:]
            case "iceriver":
                ip = self.msg.split(":")[1]
                mac = "ice-river"
            case "goldshell":
                ip = self.msg["ip"]
                mac = self.msg["mac"]
                if "boxsn" in self.msg:
                    sn = self.msg["boxsn"]
            case "sealminer":
                ip = self.msg[3]["IPV4"]
                mac = self.msg[1]["MAC"]
        return ip, mac, sn

    def is_dup_packet(self, ip: str) -> bool:
        prev_entry = False
        self.record.dict = dict(
            sorted(
                self.record.dict.items(),
                reverse=True,
                key=lambda item: float(item[1][1]),
            )
        )
        for rec in self.record.dict.keys():
            entry = self.record.dict.get(rec)
            if ip == rec and self.msg == entry[0]:
                prev_entry = True
                if time.time() - entry[1] <= RECORD_MIN_AGE:
                    logger.warning(f"Listener[{self.port}] : duplicate packet.")
                    return True
                else:
                    return False
        if not prev_entry:
            return False

    def is_zlib_compressed(self, data: bytes) -> bool:
        if ZLIB_DEFAULT_MAGIC in data:
            return True
        return False

    def decompress_data(self, data: bytes, header: bytes):
        data_start = data.find(header)
        data = data[data_start:]
        try:
            out = zlib.decompress(data)
        except Exception as e:
            logger.error(f"Listener[{self.port}]: Failed to decompress msg data: {e}.")
            return
        # clean up data
        out = out.replace(b"\x00", b"")
        out = out.replace(b"}{", b"}, {")
        out = b"[" + out + b"]"
        return out

    @Slot()
    def process_datagram(self):
        while self.sock.hasPendingDatagrams():
            datagram = self.sock.receiveDatagram(self.max_buf)
            if not datagram.isValid():
                return
            if self.is_zlib_compressed(datagram.data().data()):
                self.msg = self.decompress_data(
                    datagram.data().data(), ZLIB_DEFAULT_MAGIC
                )
            else:
                self.msg = datagram.data().data().decode().rstrip("\x00")
            if not self.msg:
                logger.warning(f"Listener[{self.port}] : msg empty. Ignoring...")
                return
            logger.info(f"Listener[{self.port}] : received msg.")
            logger.debug(f"Listener[{self.port}] : decoded {self.msg}")
            match self.port:
                case 14235:
                    type = "antminer"
                case 11503:
                    type = "iceriver"
                case 8888:
                    type = "whatsminer"
                case 1314:
                    type = "goldshell"
                case 18650:
                    type = "sealminer"
            logger.debug(f"Listener[{self.port}] : found type {type} from port.")
            if self.validate_msg(type):
                ip, mac, sn = self.parse_msg(type)
                if self.record.dict:
                    if not self.is_dup_packet(ip):
                        self.emit_result(ip, mac, type, sn)
                else:
                    self.emit_result(ip, mac, type, sn)

    def emit_result(self, *received):
        logger.info(f"Listener[{self.port}] : emit result.")
        self.record[received[0]] = [self.msg, time.time()]
        self.msg = ",".join(received)
        self.result.emit(self.msg)

    def emit_error(self, err):
        logger.error(f"Listener[{self.port}] : emit error! got {err}")
        self.error.emit()

    def close(self):
        logger.info(f"Listener[{self.port}] : close socket.")
        self.record.dict = {}  # clear record
        self.sock.close()
        del self.sock
