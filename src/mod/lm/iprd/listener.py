# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import json
import logging
import socket
import time

from pydantic import BaseModel, Field, ValidationError
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QTcpSocket

from mod.lm.ipreport import IPReport, MinerTypeHint
from utils import CURR_PLATFORM

logger = logging.getLogger(__name__)


class IPRDCommand(BaseModel):
    command: str


class IPRDPacketData(BaseModel):
    timestamp: int
    packet_id: str = Field(validation_alias="packetID")
    dst_port: int = Field(validation_alias="dstPort")
    src_ip: str = Field(validation_alias="srcIP")
    src_mac: str = Field(validation_alias="srcMAC")
    miner_hint: str = Field(validation_alias="minerHint")


class IPRDListener(QObject):
    """
    TCP Listener class for the IPR Daemon (iprd) backend.

    IPR Daemon is an alternative listening backend for receiving IP Report packets from a LAN
    and forwards the data over a TCP stream on port 7788 by default.

    This is a standalone listener that is NOT managed by ListenerManager.

    Arguements:
        parent (QObject | None): Optional parent object.

    Signals:
        subscribed: emits when socket succussfully connects and is subscribed to TCP stream.
        stopped: emits when socket succussfully disconnects from stream.
        result (IPReport): emits IPReport on received data from the stream.
        error (str): emits socket error string if one occurred.
    """

    # Signals
    subscribed = Signal()
    stopped = Signal()
    result = Signal(IPReport)
    error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.addr = QHostAddress()
        self.port = 7788  # default port set to 7788
        # active flag for socket when socket is actively reading from stream.
        self.active = False
        self.sock = QTcpSocket()

        self.sock.errorOccurred.connect(self.emit_error)
        self.sock.connected.connect(self._send_subscribe)
        self.sock.readyRead.connect(self._process_message)

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}[{self.port}]"

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
                s.detach()
            logger.debug(f"{self.__repr__()} : keepalive enabled.")
        except OSError as e:
            logger.error(f"{self.__repr__()} : failed to set keepalive: {e}")

    def _send_subscribe(self) -> None:
        logger.info(
            f"{self.__repr__()} : connected to {self.addr.toString()}:{self.port}."
        )
        self._enable_keepalive()
        cmd = IPRDCommand(command="iprd_subscribe")
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
        logger.info(f"{self.__repr__()} : received packet.")
        stream = self.sock.readAll()
        pkt_data = stream.toStdString().splitlines()[0]
        logger.debug(f"{self.__repr__()} : read {pkt_data} ({len(pkt_data)})")
        try:
            obj = json.loads(pkt_data)
            packet = IPRDPacketData.model_validate(obj=obj, by_alias=True)
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"{self.__repr__()} : invalid IP Report packet data: {e}.")
            return
        self.emit_result(packet)

    def set_socket_addr(self, addr: str, port: int) -> None:
        self.port = port
        if QHostAddress(addr).toIPv4Address() == 0:
            logger.error(
                f"{self.__repr__()} : failed to initialize socket address! Invalid IPv4 address"
            )
            return self.error.emit("Invalid IPv4 address.")
        self.addr.setAddress(addr)

    def start(self) -> None:
        if self.addr.isNull():
            logger.error(
                f"{self.__repr__()} : failed to start IPRD listener! Socket address cannot be null."
            )
            return self.error.emit("Null address.")
        if not self.active:
            self.sock.connectToHost(self.addr, self.port)

    def stop(self) -> None:
        if self.active:
            logger.info(f"{self.__repr__()} : disconnect from host.")
            self.active = False
            self.sock.abort()
            self.stopped.emit()

    def emit_result(self, result: IPRDPacketData) -> None:
        logger.info(f"{self.__repr__()} : emit result.")
        port_type = MinerTypeHint.UNKNOWN
        try:
            port_type = MinerTypeHint.from_port(result.dst_port)
        except ValueError:
            pass
        miner_type = port_type.name.lower()
        addr: int = QHostAddress(result.src_ip).toIPv4Address()
        ip_report = IPReport(
            created_at=float(result.timestamp),
            updated_at=time.time(),
            port_type=port_type,
            src_addr=addr,
            src_ip=result.src_ip,
            src_mac=result.src_mac,
            miner_type=miner_type,
            miner_sn="",
        )
        self.result.emit(ip_report)

    def emit_error(self, error: QAbstractSocket.SocketError) -> None:
        logger.error(f"{self.__repr__()} : emit error! {self.sock.errorString()}")
        self.error.emit(error.name)

    def close(self) -> None:
        self.stop()
        logger.info(f"{self.__repr__()} : close socket.")
        self.sock.readyRead.disconnect(self._process_message)
        self.sock.connected.disconnect(self._send_subscribe)
        self.sock.errorOccurred.disconnect(self.emit_error)
        self.sock.close()
