import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QUdpSocket

from .ipreport import IPReport, IPReportDatagram

logger = logging.getLogger(__name__)


class Listener(QObject):
    """
    UDP Socket Listener class

    Listens on 0.0.0.0 (Any IPv4) on specified port for IPReportDatagram.

    Args:
        port (int): UDP port to listen on.
        parent (QObject): Optional parent object.

    Signals:
        result (IPReport): emits IPReport data on valid IPReportDatagram.
        error (str): emits sock.errorString() on socket error.
    """

    result = Signal(IPReport)
    error = Signal(str)

    def __init__(self, port: int, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.addr = QHostAddress()
        self.addr.setAddress(QHostAddress.SpecialAddress.AnyIPv4)
        self.port = port
        self.buf_size = 1024
        self.sock = QUdpSocket()
        self.bound = self.sock.bind(self.addr, self.port)

        self.sock.errorOccurred.connect(self.emit_error)
        self.sock.readyRead.connect(self.__process_datagram)

    @Slot()
    def __process_datagram(self) -> None:
        while self.sock.hasPendingDatagrams():
            datagram = self.sock.receiveDatagram(self.buf_size)
            if not datagram.isValid():
                return
            logger.info(f"Listener[{self.port}] : received datagram.")
            ip_dgram = IPReportDatagram(datagram)
            if not ip_dgram.valid:
                logger.warning(
                    f"Listener[{self.port}] : invalid IP Report datagram. Ignoring..."
                )
                return
            self.emit_result(ip_dgram.ip_report)

    def emit_result(self, result: IPReport) -> None:
        logger.info(f"Listener[{self.port}] : emit result.")
        self.result.emit(result)

    def emit_error(self, error: QAbstractSocket.SocketError) -> None:
        logger.error(f"Listener[{self.port}] : emit error! {self.sock.errorString()}")
        self.error.emit(error.name)
        self.close()

    def close(self) -> None:
        logger.info(f"Listener[{self.port}] : close socket.")
        self.sock.readyRead.disconnect(self.__process_datagram)
        self.sock.errorOccurred.disconnect(self.emit_error)
        self.sock.close()
