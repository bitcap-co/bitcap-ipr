import time
import logging
import json

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QUdpSocket, QHostAddress, QNetworkInterface


logger = logging.getLogger(__name__)
RECORD_MIN_AGE = 15.0


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

    def validate_msg(self, type: str) -> bool:
        match type:
            case "goldshell":
                try:
                    self.msg = json.loads(self.msg)
                    return True
                except json.JSONDecodeError:
                    logger.warning(
                        f"Listener[{self.port}] : Failed to validate msg. Ignoring..."
                    )
                    return False
            case _:
                return True

    def parse_sn_from_msg(self, type: str) -> str:
        sn = ""
        if self.validate_msg(type):
            match type:
                case "goldshell":
                    if "boxsn" in self.msg:
                        sn = self.msg["boxsn"]
        return sn

    def is_dup_packet(self, mac: str) -> bool:
        prev_entry = False
        self.record.dict = dict(
            sorted(
                self.record.dict.items(),
                reverse=True,
                key=lambda item: float(item[1][0]),
            )
        )
        for rec in self.record.dict.keys():
            entry = self.record.dict.get(rec)
            if mac == rec:
                prev_entry = True
                if time.time() - entry[0] <= RECORD_MIN_AGE:
                    logger.warning(f"Listener[{self.port}] : duplicate packet.")
                    return True
                else:
                    return False
        if not prev_entry:
            return False

    @Slot()
    def process_datagram(self):
        while self.sock.hasPendingDatagrams():
            datagram = self.sock.receiveDatagram(self.max_buf)
            if not datagram.isValid():
                return
            logger.info(f"Listener[{self.port}] : received datagram.")
            ip = datagram.senderAddress().toString()
            # get mac address from sender interface
            ifaceIndex = datagram.interfaceIndex()
            iface = QNetworkInterface().interfaceFromIndex(ifaceIndex)
            mac = iface.hardwareAddress()
            logger.debug(f"Listener[{self.port}] : received IP: {ip}, MAC: {mac}.")
            # get msg from packet for extra miner info i.e SN
            self.msg = datagram.data().data().decode().rstrip("\x00")
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
            sn = self.parse_sn_from_msg(type)
            if self.record.dict:
                if not self.is_dup_packet(mac):
                    self.emit_result(ip, mac, type, sn)
            else:
                self.emit_result(ip, mac, type, sn)

    def emit_result(self, *received):
        logger.info(f"Listener[{self.port}] : emit result.")
        self.record[received[1]] = [time.time()]
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
