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

    Backends:
        - Linux : org.freedesktop.login1 ``PrepareForSleep`` signal via QtDBus.
        - win32 : ``WM_POWERBROADCAST`` via a native event filter.
        - darwin: ``NSWorkspace`` sleep/wake notifications via pyobjc.
        - other : no-op (consumers fall back to the monotonic-gap heuristic in
                  the listener).

    Linux and win32 backends are dependency-free (PySide6 + ctypes); the macOS
    backend needs pyobjc-framework-Cocoa and degrades to a no-op if absent.

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
        # Track suspend state so duplicate OS notifications collapse to a single
        # signal. WM_POWERBROADCAST in particular is delivered to every
        # top-level window, so one real event fires the filter several times.
        self._suspended = False
        # log an unattended (automatic) wake at most once per suspend period.
        self._auto_wake_logged = False
        if CURR_PLATFORM.startswith("linux"):
            self._init_linux()
        elif CURR_PLATFORM == "win32":
            self._init_win32()
        elif CURR_PLATFORM == "darwin":
            self._init_macos()
        else:
            logger.info(
                f"PowerMonitor : no power backend for '{CURR_PLATFORM}'; "
                "relying on listener fallback."
            )

    def _emit_suspend(self) -> None:
        if self._suspended:
            return
        self._suspended = True
        self._auto_wake_logged = False
        logger.info("PowerMonitor : suspend.")
        self.aboutToSuspend.emit()

    def _note_automatic_wake(self) -> None:
        # Only meaningful while still suspended; if a user-present resume already
        # arrived (broadcasts from multiple windows interleave) there's nothing
        # to note. Log at most once per suspend period.
        if not self._suspended or self._auto_wake_logged:
            return
        self._auto_wake_logged = True
        logger.info("PowerMonitor : automatic wake; staying suspended.")

    def _emit_resume(self) -> None:
        if not self._suspended:
            return
        self._suspended = False
        logger.info("PowerMonitor : resume.")
        self.resumed.emit()

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
            self._emit_suspend()
        else:
            self._emit_resume()

    # -- Windows (WM_POWERBROADCAST) ---------------------------------------
    def _init_win32(self) -> None:
        try:
            import ctypes
            from ctypes import wintypes

            from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication
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
                            monitor._emit_suspend()
                        elif msg.wParam == PBT_APMRESUMESUSPEND:
                            # user-present resume (sent only on user activity):
                            # this is when we actually want to reconnect.
                            monitor._emit_resume()
                        elif msg.wParam == PBT_APMRESUMEAUTOMATIC:
                            # unattended wake: the system woke for a background
                            # task and intends to sleep again. Stay quiet so we
                            # don't re-open the socket and hold the host awake.
                            monitor._note_automatic_wake()
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

    # -- macOS (NSWorkspace sleep/wake notifications) ----------------------
    def _init_macos(self) -> None:
        try:
            from AppKit import (
                NSWorkspace,
                NSWorkspaceDidWakeNotification,
                NSWorkspaceWillSleepNotification,
            )
            from Foundation import NSObject
        except ImportError as e:
            logger.warning(
                f"PowerMonitor : pyobjc unavailable ({e}); macOS backend disabled."
            )
            return

        monitor = self

        class _SleepObserver(NSObject):
            def willSleep_(self, notification):
                monitor._emit_suspend()

            def didWake_(self, notification):
                monitor._emit_resume()

        # NSWorkspace notifications are posted to its own notification center,
        # NOT the default one. Qt's macOS event loop drives the CFRunLoop, so
        # these are delivered while the app is running.
        nc = NSWorkspace.sharedWorkspace().notificationCenter()
        # keep a reference so the observer isn't garbage collected.
        self._observer = _SleepObserver.alloc().init()
        nc.addObserver_selector_name_object_(
            self._observer, b"willSleep:", NSWorkspaceWillSleepNotification, None
        )
        nc.addObserver_selector_name_object_(
            self._observer, b"didWake:", NSWorkspaceDidWakeNotification, None
        )
        self._backend = "nsworkspace"
        logger.info("PowerMonitor : subscribed to NSWorkspace sleep/wake.")
