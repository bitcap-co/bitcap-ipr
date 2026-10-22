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
        self._backends_suspended: bool = False
        self._manual_endpoint: IPRDEndpoint | None = None
        self._endpoint: IPRDEndpoint | None = None
        self._services: dict[str, IPRDService] = {}
        self._network_snapshot: NetworkSnapshot = NetworkSnapshot()
        self._network_fingerprint: str | None = None
        self._pending_fingerprint: str | None = None
        self._stable_samples: int = 0
        self._recovery_pending: bool = False

        self._discovery_settle_timer: QTimer = QTimer(self)
        self._discovery_settle_timer.setSingleShot(True)
        self._discovery_settle_timer.setInterval(DISCOVERY_SETTLE_MS)
        _ = self._discovery_settle_timer.timeout.connect(
            self._select_discovered_endpoint
        )

        _ = self.network_monitor.snapshot_updated.connect(self._on_network_snapshot)
        _ = self.discovery.service_found.connect(self._on_service_resolved)
        _ = self.discovery.service_updated.connect(self._on_service_resolved)
        _ = self.discovery.service_removed.connect(self._on_service_removed)
        _ = self.listener.subscribed.connect(self._on_subscribed)
        _ = self.listener.result.connect(self.report_received.emit)
        _ = self.listener.error.connect(self._on_listener_error)
        _ = self.listener.reconnecting.connect(self._on_reconnecting)
        _ = self.listener.retry_paused.connect(self._on_retry_paused)

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
        if not self.network_monitor.active:
            self.network_monitor.start()
        else:
            self.network_monitor.refresh()

    @Slot()
    def stop(self) -> None:
        self._listening = False
        self._suspended = False
        self._backends_suspended = False
        self._recovery_pending = False
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._services.clear()
        self._discovery_settle_timer.stop()
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
        self._backends_suspended = True
        self._recovery_pending = True
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._discovery_settle_timer.stop()
        self.discovery.on_suspend()
        self.listener.on_suspend()
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
        self._network_snapshot = snapshot
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

    def _pause_for_network(self) -> None:
        self._pause_backends_for_transition()
        self._recovery_pending = True
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._set_state(IPRDControllerState.WAITING_FOR_NETWORK)

    def _pause_backends_for_transition(self) -> None:
        self._discovery_settle_timer.stop()
        self.discovery.stop()
        self.listener.stop()

    def _apply_network(
        self, snapshot: NetworkSnapshot, *, network_changed: bool
    ) -> None:
        self._network_snapshot = snapshot
        self._network_fingerprint = snapshot.fingerprint
        self._pending_fingerprint = None
        self._stable_samples = 0
        self._recovery_pending = False

        if self._backends_suspended:
            self.discovery.on_resume()
            self.listener.on_resume()
            # Existing backends restore themselves on resume. Stop that recovery
            # after clearing their suspended flags so the controller performs one
            # network-authorized activation below.
            self.discovery.stop()
            self.listener.stop()
            self._backends_suspended = False

        if network_changed and self._mode is IPRDEndpointMode.DISCOVERED:
            self._services.clear()
            self._set_endpoint(None)

        self._activate_mode()

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
        if not self.listener.set_socket_addr(endpoint.host, endpoint.port):
            self.error.emit(f"Invalid IPRD endpoint: {endpoint.host}:{endpoint.port}")
            self.stop()
            return
        self.listener.start()
        self._set_state(IPRDControllerState.CONNECTING)

    @Slot()
    def _on_subscribed(self) -> None:
        if self._listening:
            self._set_state(IPRDControllerState.CONNECTED)

    @Slot(str)
    def _on_listener_error(self, message: str) -> None:
        del message

    @Slot(int, int)
    def _on_reconnecting(self, attempt: int, delay_ms: int) -> None:
        del attempt, delay_ms
        if self._listening and not self._suspended:
            self._set_state(IPRDControllerState.RETRYING)

    @Slot(int)
    def _on_retry_paused(self, delay_ms: int) -> None:
        del delay_ms
        if self._listening and not self._suspended:
            self._set_state(IPRDControllerState.RETRYING)

    def close(self) -> None:
        self.stop()
        self.discovery.close()
        self.listener.close()
        self.network_monitor.close()
