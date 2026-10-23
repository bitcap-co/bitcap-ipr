# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import hashlib
import ipaddress
import logging
from collections.abc import Callable, Iterable
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, field_validator
from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtNetwork import QAbstractSocket, QNetworkInterface

logger = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL_MS = 3000


class NetworkAddress(BaseModel):
    """Address identity used to detect material changes to the local network."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    interface: str
    address: str
    prefix_length: int
    lan: bool = True

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        _ = ipaddress.ip_address(value.split("%", 1)[0])
        return value

    @property
    def ip(self) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        return ipaddress.ip_address(self.address.split("%", 1)[0])

    @property
    def usable(self) -> bool:
        address = self.ip
        return not (
            address.is_loopback
            or address.is_unspecified
            or address.is_link_local
            or address.is_multicast
        )

    @property
    def fingerprint_key(self) -> str:
        address = self.ip.compressed
        scope = self.address.partition("%")[2]
        if scope:
            address = f"{address}%{scope}"
        return f"{self.interface}|{address}/{self.prefix_length}"


class NetworkSnapshot(BaseModel):
    """Deterministic snapshot of active local network addresses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    addresses: tuple[NetworkAddress, ...] = ()
    available: bool = False
    usable: bool = False
    fingerprint: str = ""


def build_network_snapshot(addresses: Iterable[NetworkAddress]) -> NetworkSnapshot:
    """Build a fingerprint from Wi-Fi/Ethernet addresses only.

    Non-LAN interfaces still make the host generally available, but VPN, PPP,
    tunnel, and cellular-style transports do not authorize local IPRD recovery.
    """
    valid = tuple(
        address
        for address in addresses
        if not address.ip.is_loopback
        and not address.ip.is_unspecified
        and not address.ip.is_multicast
        and 0 <= address.prefix_length <= address.ip.max_prefixlen
    )
    if not valid:
        return NetworkSnapshot()

    unique_lan = {address.fingerprint_key: address for address in valid if address.lan}
    normalized = tuple(unique_lan[key] for key in sorted(unique_lan))
    if not normalized:
        return NetworkSnapshot(available=True)

    identity = "\n".join(address.fingerprint_key for address in normalized)
    fingerprint = hashlib.sha256(identity.encode()).hexdigest()
    return NetworkSnapshot(
        addresses=normalized,
        available=True,
        usable=any(address.usable for address in normalized),
        fingerprint=fingerprint,
    )


def capture_network_snapshot() -> NetworkSnapshot:
    """Capture active, non-loopback addresses from Qt's interface inventory."""
    addresses: list[NetworkAddress] = []
    for interface in QNetworkInterface.allInterfaces():
        flags = interface.flags()
        if (
            not flags & QNetworkInterface.InterfaceFlag.IsUp
            or not flags & QNetworkInterface.InterfaceFlag.IsRunning
            or flags & QNetworkInterface.InterfaceFlag.IsLoopBack
        ):
            continue

        is_lan = interface.type() in (
            QNetworkInterface.InterfaceType.Ethernet,
            QNetworkInterface.InterfaceType.Wifi,
        )
        for entry in interface.addressEntries():
            host = entry.ip()
            if host.protocol() not in (
                QAbstractSocket.NetworkLayerProtocol.IPv4Protocol,
                QAbstractSocket.NetworkLayerProtocol.IPv6Protocol,
            ):
                continue
            prefix_length = entry.prefixLength()
            if prefix_length < 0:
                continue
            address = host.toString()
            try:
                addresses.append(
                    NetworkAddress(
                        interface=interface.name(),
                        address=address,
                        prefix_length=prefix_length,
                        lan=is_lan,
                    )
                )
            except ValueError:
                logger.debug(
                    "NetworkMonitor : ignoring invalid address %r on interface %s.",
                    address,
                    interface.name(),
                )

    return build_network_snapshot(addresses)


class NetworkMonitor(QObject):
    """Poll local interfaces and report deterministic network snapshots."""

    active_changed: Signal = Signal(bool)
    snapshot_updated: Signal = Signal(NetworkSnapshot, bool)
    network_changed: Signal = Signal(NetworkSnapshot)
    error: Signal = Signal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        poll_interval_ms: int = DEFAULT_POLL_INTERVAL_MS,
        snapshot_provider: Callable[[], NetworkSnapshot] = capture_network_snapshot,
    ) -> None:
        super().__init__(parent)
        if poll_interval_ms <= 0:
            raise ValueError("poll_interval_ms must be positive")

        self._snapshot_provider: Callable[[], NetworkSnapshot] = snapshot_provider
        self._snapshot: NetworkSnapshot = NetworkSnapshot()
        self._initialized: bool = False
        self._active: bool = False
        self._generation: int = 0
        self._poll_timer: QTimer = QTimer(self)
        self._poll_timer.setInterval(poll_interval_ms)
        _ = self._poll_timer.timeout.connect(self.refresh)

    @property
    def active(self) -> bool:
        return self._active

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def snapshot(self) -> NetworkSnapshot:
        return self._snapshot

    @property
    def generation(self) -> int:
        return self._generation

    @Slot()
    def start(self) -> None:
        if self._active:
            return
        self._active = True
        self.active_changed.emit(True)
        self.refresh()
        self._poll_timer.start()

    @Slot()
    def stop(self) -> None:
        if not self._active:
            return
        self._poll_timer.stop()
        self._active = False
        self._initialized = False
        self.active_changed.emit(False)

    @Slot()
    def refresh(self) -> None:
        if not self._active:
            return
        try:
            snapshot = self._snapshot_provider()
        except Exception as exc:
            message = f"Failed to inspect local network interfaces: {exc}"
            logger.error(f"NetworkMonitor : {message}")
            self.error.emit(message)
            return

        changed = not self._initialized or snapshot != self._snapshot
        self._snapshot = snapshot
        self._initialized = True
        if changed:
            self._generation += 1
            self.network_changed.emit(snapshot)
        self.snapshot_updated.emit(snapshot, changed)

    def close(self) -> None:
        self.stop()
