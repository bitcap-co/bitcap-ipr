import time
import re
import logging

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QUdpSocket, QHostAddress


logger = logging.getLogger(__name__)

reg_ip = r"((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}"
reg_mac = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
msg_patterns = {
    "common": re.compile(f"^{reg_ip},{reg_mac}"),
    "ir": re.compile(f"^addr:{reg_ip}"),
    "bt": re.compile(f"^IP:{reg_ip}MAC:{reg_mac}"),
}


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
    result = Signal()
    error = Signal()

    def __init__(self, parent: QObject, port: int):
        super().__init__(parent)
        self.port = port
        self.max_buf = 40
        self.record = Record(size=10)
        self.msg = ""
        self.addr = QHostAddress()
        self.addr.setAddress(QHostAddress.SpecialAddress.AnyIPv4)
        self.sock = QUdpSocket()
        self.sock.bind(self.addr, self.port)

        self.sock.errorOccurred.connect(self.emit_error)
        self.sock.readyRead.connect(self.process_datagram)

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
        logger.warning(f"Listener[{self.port}] : Failed to validate msg. Ignoring...")
        return False

    def parse_msg(self, type: str) -> tuple:
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
        return ip, mac

    @Slot()
    def process_datagram(self):
        while self.sock.hasPendingDatagrams():
            datagram = self.sock.receiveDatagram(self.max_buf)
            if not datagram.isValid():
                return
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
            logger.debug(f"Listener[{self.port}] : found type {type} from port.")
            if self.validate_msg(type):
                ip, mac = self.parse_msg(type)
                if self.record.dict:
                    prev_entry = False
                    self.record.dict = dict(
                        sorted(
                            self.record.dict.items(),
                            reverse=True,
                            key=lambda item: float(item[1][1]),
                        )
                    )
                    for record in self.record.dict.keys():
                        data = self.record.dict.get(record)
                        if ip == record and self.msg == data[0]:
                            prev_entry = True
                            if time.time() - data[1] <= 10.0:
                                logger.warning(
                                    f"Listener[{self.port}] : duplicate packet."
                                )
                                break
                            else:
                                self.emit_result([ip, mac, type])
                    if not prev_entry:
                        self.emit_result([ip, mac, type])
                else:
                    self.emit_result([ip, mac, type])

    def emit_result(self, received):
        logger.info(f"Listener[{self.port}] : emit result.")
        self.record[received[0]] = [self.msg, time.time()]
        self.msg = ",".join(received)
        self.result.emit()

    def emit_error(self, err):
        logger.error(f"Listener[{self.port}] : emit error! got {err}")
        self.error.emit()

    def close(self):
        logger.info(f"Listener[{self.port}] : close socket.")
        self.record.dict = {}  # clear record
        self.sock.close()
        del self.sock
