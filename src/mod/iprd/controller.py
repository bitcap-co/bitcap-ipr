# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import ipaddress
import logging
from enum import Enum, auto
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from mod.networkmonitor import NetworkMonitor, NetworkSnapshot

from .listener import IPRDListener
from .service import IPRDService, IPRDServiceListener

logger = logging.getLogger(__name__)

DISCOVERY_SETTLE_MS = 250
NETWORK_STABLE_SAMPLES = 2
RECONNECT_BASE_DELAY_MS = 1000
RECONNECT_MAX_DELAY_MS = 30000


class IPRDEndpointMode(Enum):
    DISCOVERED = auto()
    MANUAL = auto()


class IPRDControllerState(Enum):
    STOPPED = auto()
    WAITING_FOR_NETWORK = auto()
    DISCOVERING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RETRYING = auto()
    SUSPENDED = auto()


class IPRDEndpoint(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    host: str
    port: int = Field(ge=1, le=65535)
    mode: IPRDEndpointMode
    service_name: str | None = None
    network_fingerprint: str | None = None


def _address_score(address: str, snapshot: NetworkSnapshot) -> int:
    try:
        candidate = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError:
        return 0
    if candidate.is_unspecified or candidate.is_multicast:
        return 0

    for local in snapshot.addresses:
        local_ip = local.ip
        if local_ip.version != candidate.version:
            continue
        network = ipaddress.ip_network(
            f"{local_ip}/{local.prefix_length}", strict=False
        )
        if candidate in network:
            return 6

    if candidate.is_loopback:
        return 1
    if candidate.is_link_local:
        return 2
    if candidate.version == 4 and candidate.is_private:
        return 5
    if candidate.version == 4:
        return 4
    return 3


def _source_identity(
    endpoint_host: str, snapshot: NetworkSnapshot
) -> dict[str, tuple[str, ...]]:
    """Return LAN addresses that could source a connection to an endpoint."""
    try:
        endpoint = ipaddress.ip_address(endpoint_host.split("%", 1)[0])
    except ValueError:
        return {}

    compatible = [
        address
        for address in snapshot.addresses
        if address.usable and address.ip.version == endpoint.version
    ]
    direct = [
        address
        for address in compatible
        if endpoint
        in ipaddress.ip_network(f"{address.ip}/{address.prefix_length}", strict=False)
    ]
    candidates = direct or compatible
    identities: dict[str, list[str]] = {}
    for address in candidates:
        identities.setdefault(address.interface, []).append(address.fingerprint_key)
    return {
        interface: tuple(sorted(addresses))
        for interface, addresses in identities.items()
    }


def _source_address_changed(
    endpoint_host: str,
    previous: NetworkSnapshot,
    current: NetworkSnapshot,
) -> bool:
    previous_identity = _source_identity(endpoint_host, previous)
    current_identity = _source_identity(endpoint_host, current)
    return (
        bool(previous_identity)
        and previous_identity.keys() == current_identity.keys()
        and previous_identity != current_identity
    )


def select_best_discovered_endpoint(
    services: tuple[IPRDService, ...],
    snapshot: NetworkSnapshot,
    current: IPRDEndpoint | None = None,
) -> IPRDEndpoint | None:
    """Select the most directly reachable endpoint with deterministic ties."""
    candidates: list[tuple[int, str, str, int]] = []
    for service in services:
        for address in service.addresses:
            score = _address_score(address, snapshot)
            if score:
                candidates.append((score, service.name, address, service.port))
    if not candidates:
        return None

    best_score = max(candidate[0] for candidate in candidates)
    best = [candidate for candidate in candidates if candidate[0] == best_score]
    if current is not None and current.mode is IPRDEndpointMode.DISCOVERED:
        for _score, name, address, port in best:
            if (
                name == current.service_name
                and address == current.host
                and port == current.port
            ):
                return current.model_copy(
                    update={"network_fingerprint": snapshot.fingerprint}
                )

    _score, name, address, port = min(
        best, key=lambda candidate: (candidate[1], candidate[2], candidate[3])
    )
    return IPRDEndpoint(
        host=address,
        port=port,
        mode=IPRDEndpointMode.DISCOVERED,
        service_name=name,
        network_fingerprint=snapshot.fingerprint,
    )


class IPRDController(QObject):
    """Coordinate IPRD endpoint policy above discovery and socket backends."""

    state_changed: Signal = Signal(IPRDControllerState)
    endpoint_changed: Signal = Signal(object)
    report_received: Signal = Signal(object)
    error: Signal = Signal(str)
    connection_error: Signal = Signal(str)
    reconnecting: Signal = Signal(int)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        listener: IPRDListener | None = None,
        discovery: IPRDServiceListener | None = None,
        network_monitor: NetworkMonitor | None = None,
    ) -> None:
        super().__init__(parent)
        self.listener: IPRDListener = listener or IPRDListener(self)
        self.discovery: IPRDServiceListener = discovery or IPRDServiceListener(self)
        self.network_monitor: NetworkMonitor = network_monitor or NetworkMonitor(self)

        self._state: IPRDControllerState = IPRDControllerState.STOPPED
        self._mode: IPRDEndpointMode | None = None
        self._listening: bool = False
        self._suspended: bool = False
        self._manual_endpoint: IPRDEndpoint | None = None
        self._endpoint: IPRDEndpoint | None = None
        self._services: dict[str, IPRDService] = {}
        self._network_snapshot: NetworkSnapshot = NetworkSnapshot()
        self._network_fingerprint: str | None = None
        self._pending_fingerprint: str | None = None
        self._stable_samples: int = 0
        self._recovery_pending: bool = False

        self._reconnect_delay_ms: int = RECONNECT_BASE_DELAY_MS
        self._connection_error_notified: bool = False

        self._discovery_settle_timer: QTimer = QTimer(self)
        self._discovery_settle_timer.setSingleShot(True)
        self._discovery_settle_timer.setInterval(DISCOVERY_SETTLE_MS)
        _ = self._discovery_settle_timer.timeout.connect(
            self._select_discovered_endpoint
        )
        self._reconnect_timer: QTimer = QTimer(self)
        self._reconnect_timer.setSingleShot(True)
        _ = self._reconnect_timer.timeout.connect(self._attempt_reconnect)

        _ = self.network_monitor.snapshot_updated.connect(self._on_network_snapshot)
        _ = self.discovery.service_found.connect(self._on_service_resolved)
        _ = self.discovery.service_updated.connect(self._on_service_resolved)
        _ = self.discovery.service_removed.connect(self._on_service_removed)
        _ = self.listener.subscribed.connect(self._on_subscribed)
        _ = self.listener.result.connect(self.report_received.emit)
        _ = self.listener.error.connect(self._on_listener_error)

    @property
    def state(self) -> IPRDControllerState:
        return self._state

    @property
    def mode(self) -> IPRDEndpointMode | None:
        return self._mode

    @property
    def listening(self) -> bool:
        return self._listening

    @property
    def endpoint(self) -> IPRDEndpoint | None:
        return self._endpoint

    @property
    def network_snapshot(self) -> NetworkSnapshot:
        return self._network_snapshot

    def _set_state(self, state: IPRDControllerState) -> None:
        if state is self._state:
            return
        self._state = state
        self.state_changed.emit(state)

    def _set_endpoint(self, endpoint: IPRDEndpoint | None) -> None:
        if endpoint == self._endpoint:
            return
        self._endpoint = endpoint
        self.endpoint_changed.emit(endpoint)

    def start_discovery(self) -> None:
        self._mode = IPRDEndpointMode.DISCOVERED
        self._manual_endpoint = None
        self._set_endpoint(None)
        self._start()

    def start_manual(self, host: str, port: int) -> None:
        endpoint = IPRDEndpoint(
            host=host.strip().strip("[]"),
            port=port,
            mode=IPRDEndpointMode.MANUAL,
        )
        self._mode = IPRDEndpointMode.MANUAL
        self._manual_endpoint = endpoint
        self._set_endpoint(endpoint)
        self._start()

    def _start(self) -> None:
        if self._listening:
            self._pause_backends_for_transition()
        self._listening = True
        self._suspended = False
        self._network_fingerprint = None
        self._recovery_pending = False
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._cancel_reconnect(reset_notification=True)
        if not self.network_monitor.active:
            self.network_monitor.start()
        else:
            self.network_monitor.refresh()

    @Slot()
    def stop(self) -> None:
        self._listening = False
        self._suspended = False
        self._recovery_pending = False
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._services.clear()
        self._discovery_settle_timer.stop()
        self._cancel_reconnect(reset_notification=True)
        self.discovery.stop()
        self.listener.stop()
        self.network_monitor.stop()
        if self._mode is IPRDEndpointMode.DISCOVERED:
            self._set_endpoint(None)
        self._set_state(IPRDControllerState.STOPPED)

    @Slot()
    def on_suspend(self) -> None:
        if not self._listening or self._suspended:
            return
        self._suspended = True
        self._recovery_pending = True
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._discovery_settle_timer.stop()
        self._cancel_reconnect(reset_notification=True)
        self.discovery.stop()
        self.listener.stop()
        self._set_state(IPRDControllerState.SUSPENDED)

    @Slot()
    def on_resume(self) -> None:
        if not self._listening or not self._suspended:
            return
        self._suspended = False
        self._recovery_pending = True
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._set_state(IPRDControllerState.WAITING_FOR_NETWORK)
        if not self.network_monitor.active:
            self.network_monitor.start()
        else:
            self.network_monitor.refresh()

    @Slot(NetworkSnapshot, bool)
    def _on_network_snapshot(self, snapshot: NetworkSnapshot, changed: bool) -> None:
        del changed
        if not self._listening or self._suspended:
            return
        if not snapshot.usable:
            self._pause_for_network()
            return

        if self._network_fingerprint is None and not self._recovery_pending:
            self._apply_network(snapshot, network_changed=False)
            return

        fingerprint_changed = snapshot.fingerprint != self._network_fingerprint
        if not self._recovery_pending and not fingerprint_changed:
            return
        if (
            not self._recovery_pending
            and fingerprint_changed
            and self._retain_active_endpoint(snapshot)
        ):
            return
        if not self._recovery_pending:
            self._pause_backends_for_transition()
            self._recovery_pending = True

        if snapshot.fingerprint != self._pending_fingerprint:
            self._pending_fingerprint = snapshot.fingerprint
            self._stable_samples = 1
        else:
            self._stable_samples += 1
        self._set_state(IPRDControllerState.WAITING_FOR_NETWORK)
        if self._stable_samples >= NETWORK_STABLE_SAMPLES:
            self._apply_network(snapshot, network_changed=fingerprint_changed)

    def _retain_active_endpoint(self, snapshot: NetworkSnapshot) -> bool:
        endpoint = self._endpoint
        if endpoint is None or not self.listener.active:
            return False

        previous_score = _address_score(endpoint.host, self._network_snapshot)
        current_score = _address_score(endpoint.host, snapshot)
        if current_score == 0 or current_score < previous_score:
            logger.info(
                "IPRD active endpoint rank decreased after network change: endpoint=%s:%s, previous_score=%s, current_score=%s.",
                endpoint.host,
                endpoint.port,
                previous_score,
                current_score,
            )
            return False
        if _source_address_changed(endpoint.host, self._network_snapshot, snapshot):
            logger.info(
                "IPRD local source address changed; reconnecting endpoint after network stabilization: endpoint=%s:%s.",
                endpoint.host,
                endpoint.port,
            )
            return False

        if endpoint.mode is IPRDEndpointMode.DISCOVERED:
            best = select_best_discovered_endpoint(
                tuple(self._services.values()), snapshot, endpoint
            )
            if best is not None:
                best_score = _address_score(best.host, snapshot)
                if best_score > current_score:
                    logger.info(
                        "IPRD discovered candidate outranks active endpoint after network change: active=%s:%s (%s), candidate=%s:%s (%s).",
                        endpoint.host,
                        endpoint.port,
                        current_score,
                        best.host,
                        best.port,
                        best_score,
                    )
                    return False
            self._set_endpoint(
                endpoint.model_copy(
                    update={"network_fingerprint": snapshot.fingerprint}
                )
            )

        self._network_snapshot = snapshot
        self._network_fingerprint = snapshot.fingerprint
        self._pending_fingerprint = None
        self._stable_samples = 0
        logger.info(
            "IPRD active endpoint remains preferred after network change: endpoint=%s:%s, score=%s.",
            endpoint.host,
            endpoint.port,
            current_score,
        )
        return True

    def _pause_for_network(self) -> None:
        self._pause_backends_for_transition()
        self._recovery_pending = True
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._set_state(IPRDControllerState.WAITING_FOR_NETWORK)

    def _pause_backends_for_transition(self) -> None:
        self._discovery_settle_timer.stop()
        self._cancel_reconnect(reset_notification=True)
        self.discovery.stop()
        self.listener.stop()

    def _apply_network(
        self, snapshot: NetworkSnapshot, *, network_changed: bool
    ) -> None:
        reuse_discovered_endpoint = self._can_reuse_discovered_endpoint(snapshot)
        self._network_snapshot = snapshot
        self._network_fingerprint = snapshot.fingerprint
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._recovery_pending = False

        if (
            network_changed
            and self._mode is IPRDEndpointMode.DISCOVERED
            and not reuse_discovered_endpoint
        ):
            self._services.clear()
            self._set_endpoint(None)

        self._activate_mode()

    def _can_reuse_discovered_endpoint(self, snapshot: NetworkSnapshot) -> bool:
        endpoint = self._endpoint
        if (
            self._mode is not IPRDEndpointMode.DISCOVERED
            or endpoint is None
            or _address_score(endpoint.host, self._network_snapshot) != 6
            or _address_score(endpoint.host, snapshot) != 6
            or not _source_address_changed(
                endpoint.host, self._network_snapshot, snapshot
            )
        ):
            return False
        best = select_best_discovered_endpoint(
            tuple(self._services.values()), snapshot, endpoint
        )
        if best is None or (
            best.host,
            best.port,
            best.service_name,
        ) != (
            endpoint.host,
            endpoint.port,
            endpoint.service_name,
        ):
            return False
        self._set_endpoint(
            endpoint.model_copy(update={"network_fingerprint": snapshot.fingerprint})
        )
        logger.info(
            "IPRD discovered endpoint remains preferred after local address change; reconnecting %s:%s.",
            endpoint.host,
            endpoint.port,
        )
        return True

    def _activate_mode(self) -> None:
        if not self._listening:
            return
        if self._mode is IPRDEndpointMode.MANUAL:
            if self._manual_endpoint is None:
                self.error.emit("Manual IPRD endpoint is not configured.")
                self.stop()
                return
            self.discovery.stop()
            self._connect(self._manual_endpoint)
            return

        if self._endpoint is not None:
            self._connect(self._endpoint)
            return
        self._services.clear()
        self.discovery.start()
        self._set_state(IPRDControllerState.DISCOVERING)

    @Slot(IPRDService)
    def _on_service_resolved(self, service: IPRDService) -> None:
        if (
            not self._listening
            or self._suspended
            or self._mode is not IPRDEndpointMode.DISCOVERED
        ):
            return
        self._services[service.name] = service
        self._discovery_settle_timer.start()

    @Slot(str)
    def _on_service_removed(self, name: str) -> None:
        _ = self._services.pop(name, None)
        if self._endpoint is not None and self._endpoint.service_name == name:
            self._set_endpoint(None)
            if self._listening and not self._suspended:
                self.listener.stop()
                self.discovery.start()
                self._set_state(IPRDControllerState.DISCOVERING)

    @Slot()
    def _select_discovered_endpoint(self) -> None:
        endpoint = select_best_discovered_endpoint(
            tuple(self._services.values()),
            self._network_snapshot,
            self._endpoint,
        )
        if endpoint is None:
            return
        self._set_endpoint(endpoint)
        self.discovery.stop()
        self._connect(endpoint)

    def _connect(self, endpoint: IPRDEndpoint) -> None:
        self._cancel_reconnect(reset_notification=True)
        if not self.listener.set_socket_addr(endpoint.host, endpoint.port):
            self.error.emit(f"Invalid IPRD endpoint: {endpoint.host}:{endpoint.port}")
            self.stop()
            return
        self.listener.start()
        self._set_state(IPRDControllerState.CONNECTING)

    @Slot()
    def _on_subscribed(self) -> None:
        if not self._listening:
            return
        self._cancel_reconnect(reset_notification=True)
        self._set_state(IPRDControllerState.CONNECTED)

    @Slot(str)
    def _on_listener_error(self, message: str) -> None:
        if not self._listening or self._suspended or not self._network_snapshot.usable:
            return
        if not self._connection_error_notified:
            self._connection_error_notified = True
            self.connection_error.emit(message)
        self._schedule_reconnect()

    def _schedule_reconnect(self) -> None:
        if (
            not self._listening
            or self._suspended
            or not self._network_snapshot.usable
            or self._endpoint is None
        ):
            return
        if self._reconnect_timer.isActive():
            return

        delay_ms = self._reconnect_delay_ms
        logger.info("IPRD reconnecting in %s ms.", delay_ms)
        self.reconnecting.emit(delay_ms)
        self._reconnect_timer.start(delay_ms)
        self._reconnect_delay_ms = min(delay_ms * 2, RECONNECT_MAX_DELAY_MS)
        self._set_state(IPRDControllerState.RETRYING)

    @Slot()
    def _attempt_reconnect(self) -> None:
        if (
            not self._listening
            or self._suspended
            or not self._network_snapshot.usable
            or self._endpoint is None
        ):
            return
        logger.info(
            "IPRD attempting reconnect to %s:%s.",
            self._endpoint.host,
            self._endpoint.port,
        )
        self.listener.stop()
        self.listener.start()

    def _reset_reconnect_state(self, *, reset_notification: bool) -> None:
        self._reconnect_delay_ms = RECONNECT_BASE_DELAY_MS
        if reset_notification:
            self._connection_error_notified = False

    def _cancel_reconnect(self, *, reset_notification: bool = False) -> None:
        self._reconnect_timer.stop()
        self._reset_reconnect_state(reset_notification=reset_notification)

    def close(self) -> None:
        self.stop()
        self.discovery.close()
        self.listener.close()
        self.network_monitor.close()
