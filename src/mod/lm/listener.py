# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QUdpSocket

from mod.lm.ipreport import IPReport, IPReportDatagram

logger = logging.getLogger(__name__)


class Listener(QObject):
    """
    UDP Socket Listener class

    Listens on 0.0.0.0 (Any IPv4) on given port for IP Report datagrams.

    Args:
        port (int) : UDP port to listen on.
        parent (QObject | None) : Optional parent object.

    Signals:
        result (IPReport): emits IPReport data on valid IP Report datagram.
        error (str) : emits socket error string on socket error.
    """

    # Signals
    result = Signal(IPReport)
    error = Signal(str)

    def __init__(self, port: int, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.addr = QHostAddress()
        self.addr.setAddress(QHostAddress.SpecialAddress.AnyIPv4)
        self.port = port
        self.snap_len = 1600
        self.sock = QUdpSocket()
        self.bound = self.sock.bind(self.addr, self.port)

        self.sock.errorOccurred.connect(self.emit_error)
        self.sock.readyRead.connect(self._process_datagram)

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}[{self.port}]"

    @Slot()
    def _process_datagram(self) -> None:
        while self.sock.hasPendingDatagrams():
            datagram = self.sock.receiveDatagram(self.snap_len)
            if not datagram.isValid():
                # ignore if not a valid datagram
                return
            logger.info(f"{self.__repr__()} : received datagram.")
            ipr_dgram = IPReportDatagram(datagram)
            if not ipr_dgram.valid:
                logger.warning(
                    f"{self.__repr__()} : invalid IP Report datagram. Ignoring..."
                )
                return
            self.emit_result(ipr_dgram.ip_report)

    def emit_result(self, result: IPReport) -> None:
        logger.info(f"{self.__repr__()} : emit result.")
        self.result.emit(result)

    def emit_error(self, error: QAbstractSocket.SocketError) -> None:
        logger.error(f"{self.__repr__()} : emit error! {self.sock.errorString()}")
        self.error.emit(error.name)
        self.close()

    def close(self) -> None:
        logger.info(f"{self.__repr__()} : close socket.")
        self.sock.readyRead.disconnect(self._process_datagram)
        self.sock.errorOccurred.disconnect(self.emit_error)
        self.sock.close()
