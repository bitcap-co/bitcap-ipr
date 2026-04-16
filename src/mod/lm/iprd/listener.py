# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import json
import logging

from pydantic import BaseModel, Field, ValidationError
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QTcpSocket

from mod.lm import IPReport
from mod.lm.ipreport import MinerTypeHint

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
    TCP Listener for the IP Report daemon (iprd) backend.

    iprd is an alternative listening backend for receiving IP Report packets from a LAN
    and forwards the data over a TCP stream on port 7788 by default.

    Arguments:
        parent (QObject | None): Optional parent object.

    Signals:
        subscribed: emits when socket successfully connected and is subscribed to the stream.
        stopped: emits when socket successfully disconnects from the stream.
        result (IPReport): emits IPReport on received data from the stream.
        error (str): emits socket error string if one occurred.
    """

    subscribed = Signal()
    stopped = Signal()
    result = Signal(IPReport)
    error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.addr: QHostAddress = QHostAddress()
        self.port: int = 7788  # default port to 7788
        # active flag for socket when socket is actively reading from stream.
        self.active: bool = False
        self.sock: QTcpSocket = QTcpSocket()

        # init signals for socket
        self.sock.errorOccurred.connect(self.emit_error)
        self.sock.connected.connect(self._send_subscribe)
        self.sock.readyRead.connect(self._process_message)

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}[{self.port}]"

    def _send_subscribe(self) -> None:
        # once we are connected to host, send subscribe command.
        logger.info(
            f"{self.__repr__()} : connected to {self.addr.toString()}:{self.port}."
        )
        cmd = IPRDCommand(command="iprd_subscribe")
        sub_msg = cmd.model_dump_json() + "\n"
        wrote = self.sock.write(sub_msg.encode())
        logger.debug(f"{self.__repr__()} : write subscribe ({wrote}).")
        # if we failed to write, emit error
        if wrote == -1:
            self.active = False
            logger.error(f"{self.__repr__()} : failed to write subscribe!")
            return self.error.emit("Failed to write.")
        # otherwise, we mark the socket as "active" and emit subscribed.
        self.active = True
        self.subscribed.emit()

    @Slot()
    def _process_message(self) -> None:
        logger.info(f"{self.__repr__()} : received packet.")
        buf = self.sock.readAll()
        logger.debug(f"{self.__repr__()} : read {buf.toStdString()} ({buf.length()})")
        data = buf.toStdString().rstrip("\n")
        try:
            obj = json.loads(data)
            packet = IPRDPacketData.model_validate(obj=obj, by_alias=True)
        except (ValidationError, json.JSONDecodeError) as ex:
            logger.error(f"{self.__repr__()} : invalid IP Report packet data. {ex}")
            return
        else:
            self.emit_result(packet)

    def set_socket_addr(self, addr: str, port: int) -> None:
        self.port = port
        if QHostAddress(addr).toIPv4Address() == 0:
            logger.error(
                f"{self.__repr__()} : failed to initialize socket address! Invalid IPv4 address."
            )
            return self.error.emit("Invalid IPv4 address.")
        self.addr.setAddress(addr)

    def start(self) -> None:
        if self.addr.isNull():
            logger.error(
                f"{self.__repr__()} : failed to start IPRD listener! socket address cannot be null."
            )
            return self.error.emit("Address is null.")
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
            updated_at=0,
            port_type=port_type,
            src_addr=addr,
            src_ip=result.src_ip,
            src_mac=result.src_mac,
            miner_type=miner_type,
            miner_sn="",
        )
        self.result.emit(ip_report)

    def emit_error(self, error: QAbstractSocket.SocketError) -> None:
        logger.error(f"{self.__repr__()} : emit error! {error.name}")
        self.error.emit(self.sock.errorString())

    def close(self) -> None:
        self.stop()
        logger.info(f"{self.__repr__()} : close socket.")
        self.sock.readyRead.disconnect(self._process_message)
        self.sock.connected.disconnect(self._send_subscribe)
        self.sock.errorOccurred.disconnect(self.emit_error)
        self.sock.close()
