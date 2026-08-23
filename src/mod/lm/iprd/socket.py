# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import datetime
import logging
import time
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, ValidationError
from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QTcpSocket
from typing_extensions import override

logger = logging.getLogger(__name__)

IPRD_CMD_SUBSCRIBE = "iprd_subscribe"
IPRD_CMD_STATUS = "iprd_status"


class IPRDCommand(BaseModel):
    command: str
    request_id: Annotated[str | None, Field(serialization_alias="requestID")] = None


class PacketCounters(BaseModel):
    processed: int
    reports: int
    invalid: int
    duplicates: int
    unknown_filtered: int = Field(validation_alias="unknownFiltered")


class ListenerStatus(BaseModel):
    interface: str
    state: str
    activation_failures: int = Field(validation_alias="activationFailures")
    capture_errors: int = Field(validation_alias="captureErrors")
    reconnects: int = Field(validation_alias="reconnects")
    last_error: str | None = Field(None, validation_alias="lastError")
    last_error_at: datetime.datetime | None = Field(
        None, validation_alias="lastErrorAt"
    )


class IPRDStatus(BaseModel):
    state: str
    listeners_configured: int = Field(validation_alias="listenersConfigured")
    listeners_active: int = Field(validation_alias="listenersActive")
    activation_failures: int = Field(validation_alias="activationFailures")
    reconnects: int
    capture_errors: int = Field(validation_alias="captureErrors")
    capture_write_errors: int = Field(validation_alias="captureWriteErrors")
    packets: PacketCounters
    listeners: list[ListenerStatus]
    last_packet_at: datetime.datetime | None = Field(
        None, validation_alias="lastPacketAt"
    )
    last_report_at: datetime.datetime | None = Field(
        None, validation_alias="lastReportAt"
    )
    last_error: str | None = Field(None, validation_alias="lastError")
    last_error_at: datetime.datetime | None = Field(
        None, validation_alias="lastErrorAt"
    )


class IPRDResponse(BaseModel):
    type: str
    request_id: str | None = Field(None, validation_alias="requestID")
    timestamp: int
    status: IPRDStatus | None = None
    error: str | None = None


class IPRDSocket(QObject):
    """
    TCP socket handler for IPR Daemon.

    Facilitates sending commands to a running IPR Daemon instance over TCP.
    """

    # signals
    error: Signal = Signal(str)

    _timeout_ms: ClassVar[int] = 5000

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self.ip: QHostAddress = QHostAddress("127.0.0.1")
        self.port: int = 7788

        self.sock: QTcpSocket = QTcpSocket(self)
        _ = self.sock.errorOccurred.connect(self.emit_error)

    @override
    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}[{self.ip.toString()}:{self.port}]"

    def send_command(self, command: IPRDCommand) -> IPRDResponse | None:
        return self._send_command(command)

    def status(self) -> IPRDStatus | None:
        response = self.send_command(IPRDCommand(command=IPRD_CMD_STATUS))
        if response is None:
            return None
        if response.error:
            self._emit_command_error(response.error)
            return None
        if response.type != IPRD_CMD_STATUS or response.status is None:
            self._emit_command_error("Invalid status response.")
            return None
        return response.status

    def _send_command(self, command: IPRDCommand) -> IPRDResponse | None:
        self.close()
        started_at = time.monotonic()
        self.sock.connectToHost(self.ip, self.port)
        if not self.sock.waitForConnected(self._timeout_ms):
            self.close()
            return None

        try:
            payload = command.model_dump_json(by_alias=True, exclude_none=True) + "\n"
            if self.sock.write(payload.encode()) == -1:
                self._emit_command_error("Failed to write command.")
                return None

            remaining = self._remaining_timeout(started_at)
            if remaining <= 0 or not self.sock.waitForBytesWritten(remaining):
                self._emit_command_error("Timed out writing command.")
                return None

            while not self.sock.canReadLine():
                remaining = self._remaining_timeout(started_at)
                if remaining <= 0 or not self.sock.waitForReadyRead(remaining):
                    self._emit_command_error("Timed out reading command response.")
                    return None

            try:
                response_data = self.sock.readLine().toStdString()
                return IPRDResponse.model_validate_json(response_data)
            except (ValidationError, ValueError, UnicodeDecodeError) as exc:
                self._emit_command_error(f"Invalid command response: {exc}")
                return None
        finally:
            self.close()

    def _remaining_timeout(self, started_at: float) -> int:
        elapsed_ms = int((time.monotonic() - started_at) * 1000)
        return max(0, self._timeout_ms - elapsed_ms)

    def _emit_command_error(self, message: str) -> None:
        logger.error(f"{self.__repr__()} : {message}")
        self.error.emit(message)

    def set_socket_addr(self, ip: str = "127.0.0.1", port: int = 7788) -> bool:
        host_addr = QHostAddress(ip)
        if host_addr.isNull():
            logger.error(
                f"{self.__repr__()} : failed to set socket address! IP address ({ip}) is invalid."
            )
            return False
        if port < 1 or port > 65535:
            logger.error(
                f"{self.__repr__()} : failed to set socket address! Port ({port}) is invalid."
            )
            return False
        self.ip = host_addr
        self.port = port
        return True

    def emit_error(self, error: QAbstractSocket.SocketError) -> None:
        if error == QAbstractSocket.SocketError.RemoteHostClosedError:
            return
        logger.error(f"{self.__repr__()} : emit error! {self.sock.errorString()}")
        self.error.emit(error.name)

    def close(self) -> None:
        self.sock.abort()
