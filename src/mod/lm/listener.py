# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from typing import override

from pydantic import BaseModel
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QUdpSocket

from mod.lm.ipreport import IPReport, IPReportDatagram, MinerTypeHint

logger = logging.getLogger(__name__)


class ListenerError(BaseModel):
    listener: str
    port: int
    port_name: str
    error_name: QAbstractSocket.SocketError | None = None
    message: str

    @override
    def __str__(self) -> str:
        return (
            f"{self.listener}: {self.error_name}({self.message})"
            if self.error_name is not None
            else f"{self.listener}: {self.message}"
        )


class Listener(QObject):
    """
    UDP Socket Listener.
    Listens on 0.0.0.0 (Any IPv4) on given port for IP Report datagrams.

    Args:
        port (int) : UDP port to listen on.
        parent (QObject | None) : Optional parent object.

    Signals:
        result (IPReport): emits IPReport data on valid IP Report datagram.
        error (ListenerError) : emits socket error string on socket error.
    """

    # Signals
    result: Signal = Signal(IPReport)
    error: Signal = Signal(ListenerError)

    def __init__(self, port: int, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.addr: QHostAddress = QHostAddress(QHostAddress.SpecialAddress.AnyIPv4)
        self.port: int = int(port)
        self._port_type: MinerTypeHint = MinerTypeHint.UNKNOWN
        self.port_name: str = ""
        self._get_listener_name()

        self._closed: bool = False
        self.listen_error: ListenerError | None = None
        self._snap_len: int = 1600
        self._sock: QUdpSocket = QUdpSocket(self)
        self.bound: bool = self._sock.bind(self.addr, self.port)
        if not self.bound:
            self.listen_error = self.set_listen_error(
                error_msg=self._sock.errorString(),
                error=self._sock.error(),
            )

        self._sock.errorOccurred.connect(self.emit_error)
        self._sock.readyRead.connect(self._process_datagram)

    @override
    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}[{self.port_name}:{self.port}]"

    def _get_listener_name(self) -> None:
        try:
            self._port_type = MinerTypeHint.from_port(self.port)
        except ValueError:
            pass
        self.port_name = self._port_type.display_name

    def set_listen_error(
        self, error_msg: str, error: QAbstractSocket.SocketError | None = None
    ) -> ListenerError:
        err = ListenerError(
            listener=self.__repr__(),
            port=self.port,
            port_name=self.port_name,
            error_name=error,
            message=error_msg,
        )
        self.listen_error = err
        return err

    @Slot()
    def _process_datagram(self) -> None:
        while self._sock.hasPendingDatagrams():
            datagram = self._sock.receiveDatagram(self._snap_len)
            if not datagram.isValid():
                continue
            logger.info(f"{self.__repr__()} : received datagram.")
            ipr = IPReportDatagram(datagram)
            if not ipr.valid:
                logger.warning(
                    f"{self.__repr__()} : invalid IP report datagram - ignore"
                )
                continue
            self.emit_result(ipr.ip_report)

    def emit_result(self, result: IPReport) -> None:
        logger.info(f"{self.__repr__()} : emit result.")
        self.result.emit(result)

    def emit_error(self, error: QAbstractSocket.SocketError) -> None:
        listen_error = self.set_listen_error(
            error=error, error_msg=self._sock.errorString()
        )
        logger.error(f"{self.__repr__()} : emit error! {listen_error.message}")
        self.error.emit(listen_error)
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        logger.info(f"{self.__repr__()} : close socket.")
        self._sock.readyRead.disconnect(self._process_datagram)
        self._sock.errorOccurred.disconnect(self.emit_error)
        self._sock.close()
