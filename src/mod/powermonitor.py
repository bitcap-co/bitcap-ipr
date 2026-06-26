# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


import logging

from PySide6.QtCore import QObject, Signal, Slot

from utils import CURR_PLATFORM

logger = logging.getLogger(__name__)


class PowerMonitor(QObject):
    """
    Cross-platform OS power/sleep notifier.

    Emits signals when the host is about to suspend and when it resumes so
    consumers (e.g. the IPRD listener) can pause network activity like
    auto-reconnect rather than fighting the OS as it tries to sleep.

    Backends, all dependency-free (PySide6 + ctypes only):
        - Linux : org.freedesktop.login1 ``PrepareForSleep`` signal via QtDBus.
        - win32 : ``WM_POWERBROADCAST`` via a native event filter.
        - other : no-op (macOS has no pyobjc-free hook; consumers fall back to
                  the monotonic-gap heuristic in the listener).

    Arguments:
        parent (QObject | None): Optional parent object.

    Signals:
        aboutToSuspend: emits when the OS is entering sleep/suspend.
        resumed: emits when the OS has resumed from sleep/suspend.
    """

    # Signals
    aboutToSuspend = Signal()
    resumed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._backend = None
        if CURR_PLATFORM.startswith("linux"):
            self._init_linux()
        elif CURR_PLATFORM == "win32":
            self._init_win32()
        else:
            logger.info(
                f"PowerMonitor : no power backend for '{CURR_PLATFORM}'; "
                "relying on listener fallback."
            )

    # -- Linux (systemd-logind over D-Bus) ---------------------------------
    def _init_linux(self) -> None:
        try:
            from PySide6.QtCore import SLOT
            from PySide6.QtDBus import QDBusConnection
        except ImportError as e:
            logger.warning(f"PowerMonitor : QtDBus unavailable: {e}")
            return
        bus = QDBusConnection.systemBus()
        if not bus.isConnected():
            logger.warning("PowerMonitor : system D-Bus not connected.")
            return
        ok = bus.connect(
            "org.freedesktop.login1",
            "/org/freedesktop/login1",
            "org.freedesktop.login1.Manager",
            "PrepareForSleep",
            self,
            SLOT("_on_prepare_for_sleep(bool)"),
        )
        if ok:
            self._backend = "logind"
            logger.info("PowerMonitor : subscribed to logind PrepareForSleep.")
        else:
            logger.warning("PowerMonitor : failed to subscribe to PrepareForSleep.")

    @Slot(bool)
    def _on_prepare_for_sleep(self, before: bool) -> None:
        # before == True  -> system is about to suspend
        # before == False -> system has resumed
        if before:
            logger.info("PowerMonitor : PrepareForSleep(suspend).")
            self.aboutToSuspend.emit()
        else:
            logger.info("PowerMonitor : PrepareForSleep(resume).")
            self.resumed.emit()

    # -- Windows (WM_POWERBROADCAST) ---------------------------------------
    def _init_win32(self) -> None:
        try:
            from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication

            import ctypes
            from ctypes import wintypes
        except ImportError as e:
            logger.warning(f"PowerMonitor : win32 backend unavailable: {e}")
            return

        WM_POWERBROADCAST = 0x0218
        PBT_APMSUSPEND = 0x0004
        PBT_APMRESUMESUSPEND = 0x0007
        PBT_APMRESUMEAUTOMATIC = 0x0012

        class _MSG(ctypes.Structure):
            # truncated; we only read up to wParam.
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
            ]

        monitor = self

        class _PowerEventFilter(QAbstractNativeEventFilter):
            def nativeEventFilter(self, event_type, message):
                if event_type == b"windows_generic_MSG":
                    try:
                        msg = _MSG.from_address(int(message))
                    except (TypeError, ValueError):
                        return False, 0
                    if msg.message == WM_POWERBROADCAST:
                        if msg.wParam == PBT_APMSUSPEND:
                            logger.info("PowerMonitor : WM_POWERBROADCAST suspend.")
                            monitor.aboutToSuspend.emit()
                        elif msg.wParam in (
                            PBT_APMRESUMESUSPEND,
                            PBT_APMRESUMEAUTOMATIC,
                        ):
                            logger.info("PowerMonitor : WM_POWERBROADCAST resume.")
                            monitor.resumed.emit()
                # never consume the event; let Qt keep processing it.
                return False, 0

        app = QCoreApplication.instance()
        if app is None:
            logger.warning("PowerMonitor : no QCoreApplication; cannot install filter.")
            return
        # keep a reference so the filter isn't garbage collected.
        self._event_filter = _PowerEventFilter()
        app.installNativeEventFilter(self._event_filter)
        self._backend = "win32"
        logger.info("PowerMonitor : installed WM_POWERBROADCAST event filter.")
