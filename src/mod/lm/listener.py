import logging
import time
from collections import OrderedDict
from typing import Any, List, Optional

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QUdpSocket

from .ipreport import IPReportDatagram

logger = logging.getLogger(__name__)

RECORD_MIN_AGE = 10.0


class Record(OrderedDict[str, Any]):
    """
    Record is a OrderedDict with a set size of record entries.
    """

    def __init__(self, size: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._record_size = size
        self._check_record_size()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._check_record_size()

    def _check_record_size(self):
        while len(self) > self._record_size:
            self.popitem(last=False)

    @property
    def size(self) -> int:
        return self._record_size


class Listener(QObject):
    """
    UDP socket listener class

    Args:
        port (int): UDP port to listen on. Listens for all IPv4 interfaces (0.0.0.0).
        parent (QObject): Optional parent object.

    Attributes:
        bound: A boolean indicating successful socket bind.
        record: A Record with set size of parsed IPReportDatagram results.

    Signals:
        result (Signal(dict)): emits on valid IPReportDatagram with parsed result.
        error (Signal(str)): emits on socket error with error message.
    """

    result = Signal(dict)
    error = Signal(str)

    def __init__(self, port: int, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._addr = QHostAddress()
        self._addr.setAddress(QHostAddress.SpecialAddress.AnyIPv4)
        self._port = port
        self._buf_size = 1024
        self._sock = QUdpSocket()
        self.bound = self._sock.bind(self._addr, self._port)
        self.record: Record = Record(size=10)

        self._sock.errorOccurred.connect(self._emit_error)
        self._sock.readyRead.connect(self._process_datagram)

    @property
    def port(self) -> int:
        """Get port of Listener

        Returns:
            int: the port number of Listener.
        """
        return self._port

    def _is_dup_packet(self, received: List[str]) -> bool:
        ip, mac, *_ = received
        if len(self.record):
            for rec in self.record.items():
                rec_key, rec_data = rec
                if rec_key == ip and rec_data["mac"] == mac:
                    if time.time() - rec_data["updated_at"] <= RECORD_MIN_AGE:
                        logger.warning(f"Listener[{self._port}] : dupicate packet.")
                        return True
                    else:
                        return False
        return False

    @Slot()
    def _process_datagram(self) -> None:
        while self._sock.hasPendingDatagrams():
            datagram = self._sock.receiveDatagram(self._buf_size)
            if not datagram.isValid():
                return
            logger.info(f"Listener[{self._port}] : received datagram.")
            ip_report = IPReportDatagram(datagram)
            if not ip_report.valid:
                logger.warning(
                    f"Listener[{self._port}] : invalid IP Report datagram. Ignoring..."
                )
                return
            if not self._is_dup_packet(ip_report.result):
                self._emit_result(ip_report)

    def _emit_result(self, ip_report: IPReportDatagram) -> None:
        logger.info(f"Listener[{self._port}] : emit result.")
        self.record[ip_report.ip] = {
            "miner_type": ip_report.miner_type,
            "ip": ip_report.ip,
            "mac": ip_report.mac,
            "serial": ip_report.serial,
            "created_at": ip_report.created_at,
            "updated_at": time.time(),
        }
        self.result.emit(self.record[ip_report.ip])

    def _emit_error(self, error: QAbstractSocket.SocketError) -> None:
        logger.error(
            f"Listener[{self._port}] : emit error! got {self._sock.errorString()}"
        )
        self.error.emit(error._name_)

    def close(self) -> None:
        logger.info(f"Listener[{self._port}] : close socket.")
        self.record.clear()
        self._sock.close()
        del self._sock
        del self
