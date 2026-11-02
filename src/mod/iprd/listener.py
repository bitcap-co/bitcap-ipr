# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
import socket
import time
from typing import override

from pydantic import BaseModel, Field, ValidationError
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QTcpSocket

from mod.lm.ipreport import IPReport, MinerTypeHint
from utils import CURR_PLATFORM

from .socket import IPRD_CMD_SUBSCRIBE, IPRDCommand

logger = logging.getLogger(__name__)


class IPRDReportMessage(BaseModel):
    """Represents a report message from the IPRD daemon."""

    timestamp: int
    packet_id: str = Field(validation_alias="packetID")
    dst_port: int = Field(validation_alias="dstPort")
    src_ip: str = Field(validation_alias="srcIP")
    src_mac: str = Field(validation_alias="srcMAC")
    miner_hint: str = Field(validation_alias="minerHint")


class IPRDListener(QObject):
    """
    TCP listener for IPR Daemon.

    IPR Daemon is a standalone listening backend for receiving IP reports live on the wire across
    the network. IP report messages are forwarded over a subscribable TCP stream.
    See the project repository for more information. https://github.com/bitcap-co/ipr-daemon

    Args:
        parent (QObject): Optional parent object.

    Signals:
        subscribed: emits when socket successfully connects and is subscribed to TCP stream.
        stopped: emits when socket successfully disconnects from stream.
        result (IPReport): emits IPReport on received data from the stream.
        error (str): emits error string on unintentional socket failures for policy handling.
    """

    # Signals
    subscribed: Signal = Signal()
    stopped: Signal = Signal()
    result: Signal = Signal(IPReport)
    error: Signal = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.addr: QHostAddress = QHostAddress()
        self.port: int = 7788
        # active flag for socket when socket is actively reading from stream.
        self.active: bool = False
        self.sock: QTcpSocket = QTcpSocket()

        # listener was explicitly stopped by the user.
        self._intentional_stop: bool = False

        _ = self.sock.errorOccurred.connect(self.emit_error)
        _ = self.sock.connected.connect(self._send_subscribe)
        _ = self.sock.readyRead.connect(self._process_message)

    @override
    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}[{self.addr.toString()}:{self.port}]"

    def _enable_keepalive(self) -> None:
        fd = self.sock.socketDescriptor()
        if fd == -1:
            logger.warning(f"{self!r} : no socket descriptor; skipping keepalive")
            return
        try:
            # Wrap Qt's native handle. We must NOT let this python object close it,
            # so we detach() before it goes out of scope (see finally).
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, fileno=int(fd))
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                if CURR_PLATFORM == "win32":
                    # (onoff, keepalive_time_ms, keepalive_interval_ms)
                    # start probing after 15s idle, then every 3s.
                    s.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 15000, 3000))
            finally:
                # Release the fd back to Qt without closing the underlying socket.
                _ = s.detach()
            logger.debug(f"{self!r} : keepalive enabled")
        except OSError as exc:
            logger.warning(f"{self!r} : failed to set keepalive: {exc}")

    def _send_subscribe(self) -> None:
        if self._intentional_stop:
            self.sock.abort()
            self.active = False
            return
        logger.info(f"{self!r} : connected to {self.addr.toString()}:{self.port}.")
        self._enable_keepalive()
        cmd = IPRDCommand(command=IPRD_CMD_SUBSCRIBE)
        sub_msg = cmd.model_dump_json() + "\n"
        wrote = self.sock.write(sub_msg.encode())
        logger.debug(f"{self!r} : write subscribe ({wrote}).")
        # if we failed to write, emit error
        if wrote == -1:
            self.active = False
            logger.error(f"{self!r} : failed to write subscribe message!")
            return self.error.emit("Failed to write command.")
        self.active = True
        self.subscribed.emit()

    @Slot()
    def _process_message(self) -> None:
        # Leave partial frames in QTcpSocket's buffer and process every complete
        # newline-delimited message already available from the TCP stream.
        while self.sock.canReadLine():
            msg_data = self.sock.readLine().toStdString().strip()
            if not msg_data:
                continue
            logger.debug(f"{self!r} : read {msg_data} ({len(msg_data)})")
            logger.info(f"{self!r} : received report.")
            try:
                report = IPRDReportMessage.model_validate_json(msg_data, by_alias=True)
            except ValidationError as exc:
                logger.error(f"{self!r} : invalid IP report data: {exc}.")
                continue
            self.emit_result(report)

    def set_socket_addr(self, addr: str, port: int) -> bool:
        """Sets host IP address and port for IPRD TCP stream endpoint.
        Returns False on invalid address/port."""
        host_addr = QHostAddress(addr)
        if host_addr.isNull():
            logger.error(
                f"{self!r} : failed to set socket address! IP address ({addr}) is invalid."
            )
            return False
        if port < 1 or port > 65535:
            logger.error(
                f"{self!r} : failed to set socket address! Port ({port}) is invalid."
            )
            return False
        self.port = port
        self.addr = host_addr
        return True

    def start(self) -> None:
        """Connects to the IPRD TCP stream endpoint and start reading from the stream."""
        if self.addr.isNull():
            logger.error(
                f"{self!r} : failed to start IPRD listener! Socket address not set."
            )
            return self.error.emit("Socket address not set.")
        self._intentional_stop = False
        if not self.active:
            self.sock.connectToHost(self.addr, self.port)

    def stop(self) -> None:
        """Closes connection to IPRD TCP stream endpoint."""
        self._intentional_stop = True
        was_connected = (
            self.sock.state() != QAbstractSocket.SocketState.UnconnectedState
        )
        if was_connected:
            logger.info(f"{self!r} : disconnect from host.")
            self.sock.abort()
        self.active = False
        if was_connected:
            self.stopped.emit()

    def emit_result(self, report: IPRDReportMessage) -> None:
        logger.info(f"{self!r} : emit result.")
        hint = MinerTypeHint.UNKNOWN
        try:
            hint = MinerTypeHint.from_port(report.dst_port)
        except ValueError:
            pass
        miner_hint = str(hint)
        addr_result = QHostAddress(report.src_ip).toIPv4Address()
        addr = addr_result[0] if isinstance(addr_result, tuple) else addr_result
        ip_report = IPReport(
            created_at=report.timestamp / 1000.0,
            updated_at=time.time(),
            hint=hint,
            miner_hint=miner_hint,
            sort_ip=addr,
            ip=report.src_ip,
            mac=report.src_mac,
            serial="",
        )
        self.result.emit(ip_report)

    def emit_error(self, error: QAbstractSocket.SocketError) -> None:
        self.active = False
        if self._intentional_stop:
            return
        logger.error(f"{self!r} : emit error! {self.sock.errorString()}")
        self.error.emit(error.name)

    def close(self) -> None:
        self.stop()
        logger.info(f"{self!r} : close socket.")
        _ = self.sock.readyRead.disconnect(self._process_message)
        _ = self.sock.connected.disconnect(self._send_subscribe)
        _ = self.sock.errorOccurred.disconnect(self.emit_error)
        self.sock.close()
