# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import json
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


class IPRDPacketData(BaseModel):
    timestamp: int
    packet_id: str = Field(validation_alias="packetID")
    dst_port: int = Field(validation_alias="dstPort")
    src_ip: str = Field(validation_alias="srcIP")
    src_mac: str = Field(validation_alias="srcMAC")
    miner_hint: str = Field(validation_alias="minerHint")


class IPRDListener(QObject):
    """
    TCP listener for IPR Daemon (iprd).

    IPR Daemon is an external listening backend for receiving IP report packets directly from a LAN
    and forwards the data over a subscribable TCP stream.

    NOTE: This is a standalone listener and not managed by ListenerManager.

    Arguements:
        parent (QObject | None): Optional parent object.

    Signals:
        subscribed: emits when socket succussfully connects and is subscribed to TCP stream.
        stopped: emits when socket succussfully disconnects from stream.
        result (IPReport): emits IPReport on received data from the stream.
        error (str): emits every unintentional socket failure for policy handling.
    """

    # Signals
    subscribed: Signal = Signal()
    stopped: Signal = Signal()
    result: Signal = Signal(IPReport)
    error: Signal = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.addr: QHostAddress = QHostAddress()
        self.port: int = 7788  # default port set to 7788
        # active flag for socket when socket is actively reading from stream.
        self.active: bool = False
        self.sock: QTcpSocket = QTcpSocket()

        self._intentional_stop: bool = False

        self.sock.errorOccurred.connect(self.emit_error)
        self.sock.connected.connect(self._send_subscribe)
        self.sock.readyRead.connect(self._process_message)

    @override
    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}[{self.addr.toString()}:{self.port}]"

    def _enable_keepalive(self) -> None:
        fd = self.sock.socketDescriptor()
        if fd == -1:
            logger.warning(
                f"{self.__repr__()} : no socket descriptor; skipping keepalive"
            )
            return
        try:
            # Wrap Qt's native handle. We must NOT let this Python object close it,
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
            logger.debug(f"{self.__repr__()} : keepalive enabled.")
        except OSError as e:
            logger.error(f"{self.__repr__()} : failed to set keepalive: {e}")

    def _send_subscribe(self) -> None:
        if self._intentional_stop:
            self.sock.abort()
            self.active = False
            return
        logger.info(
            f"{self.__repr__()} : connected to {self.addr.toString()}:{self.port}."
        )
        self._enable_keepalive()
        cmd = IPRDCommand(command=IPRD_CMD_SUBSCRIBE)
        sub_msg = cmd.model_dump_json() + "\n"
        wrote = self.sock.write(sub_msg.encode())
        logger.debug(f"{self.__repr__()} : write subscribe ({wrote}).")
        # if we failed to write (-1), emit error
        if wrote == -1:
            self.active = False
            logger.error(f"{self.__repr__()} : failed to write subscribe!")
            return self.error.emit("Failed to write command.")
        self.active = True
        self.subscribed.emit()

    @Slot()
    def _process_message(self) -> None:
        # Leave partial frames in QTcpSocket's buffer and process every complete
        # newline-delimited report already available from the TCP stream.
        while self.sock.canReadLine():
            pkt_data = self.sock.readLine().toStdString().strip()
            if not pkt_data:
                continue
            logger.info(f"{self.__repr__()} : received packet.")
            logger.debug(f"{self.__repr__()} : read {pkt_data} ({len(pkt_data)})")
            try:
                obj = json.loads(pkt_data)
                packet = IPRDPacketData.model_validate(obj=obj, by_alias=True)
            except (ValidationError, json.JSONDecodeError) as e:
                logger.error(f"{self.__repr__()} : invalid IP Report packet data: {e}.")
                continue
            self.emit_result(packet)

    def set_socket_addr(self, addr: str, port: int) -> bool:
        """Sets host IP address and port for iprd TCP stream endpoint.
        Returns False on invalid address/port."""
        host_addr = QHostAddress(addr)
        if host_addr.isNull():
            logger.error(
                f"{self.__repr__()} : failed to set socket address! IP address ({addr}) is invalid."
            )
            return False
        if port < 1 or port > 65535:
            logger.error(
                f"{self.__repr__()} : failed to set socket address! Port ({port}) is invalid."
            )
            return False
        self.port = port
        self.addr = host_addr
        return True

    def start(self) -> None:
        """Connects to iprd TCP stream endpoint and starts reading from the stream."""
        if self.addr.isNull():
            logger.error(
                f"{self.__repr__()} : failed to start IPRD listener! Socket address not set."
            )
            return self.error.emit("Socket address not set.")
        self._intentional_stop = False
        if not self.active:
            self.sock.connectToHost(self.addr, self.port)

    def stop(self) -> None:
        """Closes connection to iprd TCP stream endpoint."""
        self._intentional_stop = True
        was_connected = (
            self.sock.state() != QAbstractSocket.SocketState.UnconnectedState
        )
        if was_connected:
            logger.info(f"{self.__repr__()} : disconnect from host.")
            self.sock.abort()
        self.active = False
        if was_connected:
            self.stopped.emit()

    def emit_result(self, result: IPRDPacketData) -> None:
        logger.info(f"{self.__repr__()} : emit result.")
        hint = MinerTypeHint.UNKNOWN
        try:
            hint = MinerTypeHint.from_port(result.dst_port)
        except ValueError:
            pass
        miner_hint = str(hint)
        addr_result = QHostAddress(result.src_ip).toIPv4Address()
        addr = addr_result[0] if isinstance(addr_result, tuple) else addr_result
        ip_report = IPReport(
            created_at=result.timestamp / 1000.0,
            updated_at=time.time(),
            hint=hint,
            sort_ip=addr,
            ip=result.src_ip,
            mac=result.src_mac,
            miner_hint=miner_hint,
            serial="",
        )
        self.result.emit(ip_report)

    def emit_error(self, error: QAbstractSocket.SocketError) -> None:
        self.active = False
        if self._intentional_stop:
            return
        logger.error(f"{self.__repr__()} : emit error! {self.sock.errorString()}")
        self.error.emit(error.name)

    def close(self) -> None:
        self.stop()
        logger.info(f"{self.__repr__()} : close socket.")
        self.sock.readyRead.disconnect(self._process_message)
        self.sock.connected.disconnect(self._send_subscribe)
        self.sock.errorOccurred.disconnect(self.emit_error)
        self.sock.close()
