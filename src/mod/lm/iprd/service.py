# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import ipaddress
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import QObject, Signal, Slot
from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

logger = logging.getLogger(__name__)

IPRD_SERVICE_TYPE = "_iprd._tcp.local."
DEFAULT_RESOLVE_TIMEOUT_MS = 3000


def _create_zeroconf() -> Zeroconf:
    """Create the synchronous client outside any running asyncio event loop."""
    with ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="iprd-zeroconf-init",
    ) as executor:
        return executor.submit(Zeroconf).result()


class IPRDService(BaseModel):
    """Resolved endpoint advertised by an IPR Daemon instance."""

    model_config = ConfigDict(frozen=True)

    name: str
    instance_name: str
    hostname: str
    addresses: tuple[str, ...]
    port: int
    properties: dict[str, str | None]

    @property
    def address(self) -> str:
        """Return the preferred connection address, favoring IPv4."""
        for address in self.addresses:
            try:
                if ipaddress.ip_address(address.split("%", 1)[0]).version == 4:
                    return address
            except ValueError:
                continue
        return self.addresses[0] if self.addresses else ""

    @property
    def version(self) -> str:
        return self.properties.get("version") or ""

    @property
    def subscribe_command(self) -> str:
        return self.properties.get("subscribe") or "iprd_subscribe"


class IPRDServiceListener(QObject, ServiceListener):
    """Discover IPR Daemon TCP endpoints using mDNS/DNS-SD.

    ``zeroconf`` invokes service callbacks from its browser thread. Qt signal
    emission is thread-safe, allowing receivers in the GUI thread to consume
    resolved services through queued signal delivery.

    Signals:
        service_found (IPRDService): emitted when a daemon is resolved.
        service_updated (IPRDService): emitted when a resolved daemon changes.
        service_removed (str): emitted with the full DNS-SD service name.
        started: emitted after browsing starts.
        stopped: emitted after browsing stops and resources are closed.
        error (str): emitted when startup or service resolution fails.
    """

    service_found = Signal(IPRDService)
    service_updated = Signal(IPRDService)
    service_removed = Signal(str)
    started = Signal()
    stopped = Signal()
    error = Signal(str)

    _resolved = Signal(object, int, int, bool)
    _removed = Signal(str, int, int)
    _resolution_failed = Signal(str, str, int, int)

    def __init__(
        self,
        parent: QObject | None = None,
        resolve_timeout_ms: int = DEFAULT_RESOLVE_TIMEOUT_MS,
    ) -> None:
        super().__init__(parent)
        if resolve_timeout_ms <= 0:
            raise ValueError("resolve_timeout_ms must be positive")

        self.resolve_timeout_ms = resolve_timeout_ms
        self._zeroconf: Zeroconf | None = None
        self._browser: ServiceBrowser | None = None
        self._services: dict[str, IPRDService] = {}
        self._revisions: dict[str, int] = {}
        self._session = 0
        self._lock = threading.RLock()
        self._active = False
        self._power_suspended = False
        self._resume_after_suspend = False

        self._resolved.connect(self._publish_resolved)
        self._removed.connect(self._publish_removed)
        self._resolution_failed.connect(self._publish_resolution_error)

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}[{IPRD_SERVICE_TYPE}]"

    @property
    def active(self) -> bool:
        with self._lock:
            return self._active

    @property
    def services(self) -> tuple[IPRDService, ...]:
        """Return a thread-safe snapshot of currently discovered services."""
        with self._lock:
            return tuple(self._services.values())

    def get_service(self, name: str) -> IPRDService | None:
        with self._lock:
            return self._services.get(name)

    @Slot()
    def start(self) -> None:
        """Start browsing. Calling this while active has no effect."""
        zeroconf: Zeroconf | None = None
        try:
            with self._lock:
                if self._active:
                    return
                if self._power_suspended:
                    self._resume_after_suspend = True
                    return
                zeroconf = _create_zeroconf()
                self._session += 1
                self._revisions.clear()
                self._services.clear()
                self._zeroconf = zeroconf
                self._active = True
                self._browser = ServiceBrowser(
                    zeroconf,
                    IPRD_SERVICE_TYPE,
                    listener=self,
                )
        except Exception as exc:
            with self._lock:
                if self._zeroconf is zeroconf:
                    self._active = False
                    self._browser = None
                    self._zeroconf = None
                    self._session += 1
                    self._revisions.clear()
                    self._services.clear()
            if zeroconf is not None:
                zeroconf.close()
            self._emit_error(f"Failed to start IPRD service discovery: {exc}")
            return

        logger.info(f"{self.__repr__()} : started service discovery.")
        self.started.emit()

    @Slot()
    def stop(self) -> None:
        """Stop browsing and release all zeroconf sockets and threads."""
        self._stop()

    def _stop(self, *, preserve_resume: bool = False) -> None:
        with self._lock:
            if not preserve_resume:
                self._resume_after_suspend = False
            if not self._active and self._browser is None and self._zeroconf is None:
                return
            self._active = False
            self._session += 1
            browser = self._browser
            zeroconf = self._zeroconf
            self._browser = None
            self._zeroconf = None
            self._services.clear()
            self._revisions.clear()

        errors: list[str] = []
        if browser is not None:
            try:
                browser.cancel()
            except Exception as exc:
                errors.append(f"cancel browser: {exc}")
        if zeroconf is not None:
            try:
                zeroconf.close()
            except Exception as exc:
                errors.append(f"close zeroconf: {exc}")

        if errors:
            self._emit_error(
                "Failed to stop IPRD service discovery: " + "; ".join(errors)
            )
        logger.info(f"{self.__repr__()} : stopped service discovery.")
        self.stopped.emit()

    @Slot()
    def on_suspend(self) -> None:
        """Pause discovery and remember whether it should resume after wake."""
        with self._lock:
            if self._power_suspended:
                return
            self._power_suspended = True
            pause = self._active
            self._resume_after_suspend = pause
        if pause:
            logger.info(f"{self.__repr__()} : host suspending; pausing discovery.")
            self._stop(preserve_resume=True)

    @Slot()
    def on_resume(self) -> None:
        """Recreate zeroconf after wake if discovery was active before sleep."""
        with self._lock:
            if not self._power_suspended:
                return
            self._power_suspended = False
            restart = self._resume_after_suspend
            self._resume_after_suspend = False
        if restart:
            logger.info(f"{self.__repr__()} : host resumed; restarting discovery.")
            self.start()

    def close(self) -> None:
        self.stop()

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._queue_resolution(zc, type_, name, is_update=False)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self._queue_resolution(zc, type_, name, is_update=True)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        del type_
        with self._lock:
            if not self._active or zc is not self._zeroconf:
                return
            revision = self._revisions.get(name, 0) + 1
            self._revisions[name] = revision
            session = self._session
        self._removed.emit(name, session, revision)

    def _queue_resolution(
        self,
        zc: Zeroconf,
        type_: str,
        name: str,
        is_update: bool,
    ) -> None:
        with self._lock:
            if not self._active or zc is not self._zeroconf:
                return
            revision = self._revisions.get(name, 0) + 1
            self._revisions[name] = revision
            session = self._session
        threading.Thread(
            target=self._resolve_service,
            args=(zc, type_, name, is_update, session, revision),
            name="iprd-service-resolver",
            daemon=True,
        ).start()

    def _resolve_service(
        self,
        zc: Zeroconf,
        type_: str,
        name: str,
        is_update: bool,
        session: int,
        revision: int,
    ) -> None:
        try:
            info = zc.get_service_info(type_, name, timeout=self.resolve_timeout_ms)
            if info is None:
                self._resolution_failed.emit(
                    f"Failed to resolve IPRD service: {name}",
                    name,
                    session,
                    revision,
                )
                return
            service = self._service_from_info(info)
        except Exception as exc:
            self._resolution_failed.emit(
                f"Failed to resolve IPRD service {name}: {exc}",
                name,
                session,
                revision,
            )
            return
        self._resolved.emit(service, session, revision, is_update)

    @Slot(object, int, int, bool)
    def _publish_resolved(
        self,
        service: IPRDService,
        session: int,
        revision: int,
        is_update: bool,
    ) -> None:
        with self._lock:
            if (
                not self._active
                or session != self._session
                or revision != self._revisions.get(service.name)
            ):
                return
            previous = self._services.get(service.name)
            if previous == service:
                return
            self._services[service.name] = service

        if previous is None or not is_update:
            logger.info(
                f"{self.__repr__()} : discovered {service.address}:{service.port}."
            )
            self.service_found.emit(service)
            return

        logger.info(f"{self.__repr__()} : updated {service.address}:{service.port}.")
        self.service_updated.emit(service)

    @Slot(str, int, int)
    def _publish_removed(self, name: str, session: int, revision: int) -> None:
        with self._lock:
            if (
                not self._active
                or session != self._session
                or revision != self._revisions.get(name)
            ):
                return
            service = self._services.pop(name, None)
        if service is None:
            return
        logger.info(f"{self.__repr__()} : removed {name}.")
        self.service_removed.emit(name)

    @Slot(str, str, int, int)
    def _publish_resolution_error(
        self, message: str, name: str, session: int, revision: int
    ) -> None:
        with self._lock:
            if (
                not self._active
                or session != self._session
                or revision != self._revisions.get(name)
            ):
                return
        self._emit_error(message)

    @staticmethod
    def _service_from_info(info: ServiceInfo) -> IPRDService:
        addresses = tuple(dict.fromkeys(info.parsed_scoped_addresses()))
        if not addresses:
            raise ValueError("service did not advertise a reachable address")
        if info.port is None or not 1 <= info.port <= 65535:
            raise ValueError(f"service advertised invalid port: {info.port}")

        properties: dict[str, str | None]
        decoded = getattr(info, "decoded_properties", None)
        if decoded is not None:
            properties = dict(decoded)
        else:
            properties = {
                key.decode("ascii", "replace"): (
                    None if value is None else value.decode("utf-8", "replace")
                )
                for key, value in info.properties.items()
            }

        return IPRDService(
            name=info.name,
            instance_name=info.get_name(),
            hostname=(info.server or "").rstrip("."),
            addresses=addresses,
            port=info.port,
            properties=properties,
        )

    def _emit_error(self, message: str) -> None:
        logger.error(f"{self.__repr__()} : {message}")
        self.error.emit(message)
