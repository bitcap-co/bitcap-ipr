import time
import logging
from typing import Any, Dict, List

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QUdpSocket, QHostAddress

from .ipreport import IPReportDatagram

logger = logging.getLogger(__name__)
RECORD_MIN_AGE = 10.0


class Record:
    def __init__(self, size: int):
        self.size = size
        self.dict: Dict[str, Any] = {}

    def __setitem__(self, key: str, value: Any):
        if len(self.dict) >= self.size:
            self.dict.popitem()
        self.dict[key] = value

    def __getitem__(self, key: str):
        return self.dict[key]


class Listener(QObject):
    result = Signal(list)
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

    def is_dup_packet(self, parsed_msg: List[str]) -> bool:
        prev_entry = False
        self.record.dict = dict(
            sorted(
                self.record.dict.items(),
                reverse=True,
                key=lambda item: float(item[1]["created_at"]),
            )
        )
        ip, mac, type, *_ = parsed_msg
        for ip_record in self.record.dict.keys():
            rec_data = self.record.dict.get(ip_record)
            if ip == ip_record and mac == rec_data["mac"] and type == rec_data["type"]:
                prev_entry = True
                if time.time() - rec_data["created_at"] <= RECORD_MIN_AGE:
                    logger.warning(f"Listener[{self.port}] : duplicate packet.")
                    return True
                else:
                    return False
        if not prev_entry:
            return False

    @Slot()
    def process_datagram(self) -> None:
        while self.sock.hasPendingDatagrams():
            datagram = self.sock.receiveDatagram(self.max_buf)
            if not datagram.isValid():
                return
            logger.info(f"Listener[{self.port}] : received datagram.")
            ipreport = IPReportDatagram(datagram)
            if not ipreport.is_msg_valid:
                logger.warning(
                    f"Listener[{self.port}] : invalid IP report datagram. Ignoring..."
                )
                return
            parsed_msg = ipreport.parse_msg()
            if self.record.dict:
                if not self.is_dup_packet(parsed_msg):
                    self.emit_result(parsed_msg)
            else:
                self.emit_result(parsed_msg)

    def emit_result(self, received: List[str]) -> None:
        logger.info(f"Listener[{self.port}] : emit result.")
        ip, mac, type, *_ = received
        self.record[ip] = {
            "type": type,
            "mac": mac,
            "created_at": time.time(),
        }
        self.result.emit(received)

    def emit_error(self, err) -> None:
        logger.error(f"Listener[{self.port}] : emit error! got {err}")
        self.error.emit()

    def close(self) -> None:
        logger.info(f"Listener[{self.port}] : close socket.")
        self.record.dict = {}  # clear record
        self.sock.close()
        del self.sock
