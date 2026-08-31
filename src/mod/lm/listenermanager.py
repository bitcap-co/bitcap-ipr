# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
import time
from collections import OrderedDict
from typing import override

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QButtonGroup

from mod.lm.ipreport import IPReport, MinerTypeHint
from mod.lm.listener import Listener, ListenerError

logger = logging.getLogger(__name__)

RECORD_MIN_AGE = 10.0


class Record(OrderedDict[str, IPReport]):
    """
    Record is a OrderedDict with a set size of IPReport entries. Entries are removed in FIFO order.
    Serves as a cache of recently seen IPReports to avoid re-emitting duplicate IP reports.

    Args:
        capacity (int): The maximum number of stored entries in the record.

    Raises:
        ValueError: If capacity is not a positive integer.
    """

    def __init__(self, capacity: int) -> None:
        super().__init__()
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self._capacity: int = capacity

    @property
    def capacity(self) -> int:
        """Returns the maximum capacity of the record."""
        return self._capacity

    @property
    def size(self) -> int:
        """Returns the current number of stored IP reports in the record."""
        return len(self)

    def _truncate(self) -> None:
        while len(self) > self._capacity:
            _ = self.popitem(last=False)

    @override
    def __setitem__(self, key: str, value: IPReport, /) -> None:
        super().__setitem__(key, value)
        self.move_to_end(key)
        self._truncate()

    def is_duplicate(self, value: IPReport) -> bool:
        """Returns True if the given IPReport is a duplicate of an existing entry.
        Existing entries can be re-emitted if they are older than RECORD_MIN_AGE.
        """
        previous = self.get(value.ip)
        if previous is None:
            return False
        if previous.mac != value.mac:  # MAC mismatch; update existing entry
            return False
        if time.time() - previous.updated_at <= RECORD_MIN_AGE:
            logger.warning(f" [{value.ip}] : duplicate packet.")
            return True
        return False

    def add(self, value: IPReport) -> bool:
        """Adds the given IPReport to the record. Returns False if IPReport is a duplicate."""
        if ok := not self.is_duplicate(value):
            self.__setitem__(value.ip, value)
        return ok


class ListenerManager(QObject):
    """
    ListenerManager is a UDP listener manager.
    It manages a configurable set of Listeners for supported ASIC cryptominers
    and forwards validated IP reports.

    Args:
        parent (QObject) : The parent object.

    Signals:
        report_received (IPReport) : emits IPReport when a Listener receives a IP report result.
        error_received (ListenerError) : emits a ListenerError when a socket error occurred on a Listener.
        bind_failed (ListenerError) : emits a ListenerError when a Listener fails to bind.
    """

    # Signals
    report_received: Signal = Signal(IPReport)
    error_received: Signal = Signal(ListenerError)
    bind_failed: Signal = Signal(ListenerError)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self._listeners: list[Listener] = []
        self._listen_for: QButtonGroup
        self.record: Record = Record(capacity=10)

    @override
    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}"

    @property
    def count(self) -> int:
        """Returns the number of currently active listeners."""
        return len(self._listeners)

    @property
    def status(self) -> str:
        """Returns the concatenated string of active listener names. Empty if no listeners are active."""
        status = ""
        if len(self._listeners):
            enabled_listeners = [
                l.port_name
                for l in self._listeners
                if l.port != int(MinerTypeHint.COMMON)
            ]
            enabled_common = []
            if self._get_common_listener():
                enabled_common = [
                    b.text()
                    for b in self._listen_for.buttons()
                    if self._listen_for.id(b) in [1, 4, 5] and b.isChecked()
                ]
                status = ", ".join(enabled_common)
            if status and len(enabled_listeners):
                status += ", "
            status += ", ".join(enabled_listeners)
        return status

    @property
    def enabled(self) -> list[str]:
        """Returns the list of enabled button names from listen_for configuration."""
        return [
            btn.text().lower() for btn in self._listen_for.buttons() if btn.isChecked()
        ]

    def _get_common_listener(self) -> Listener | None:
        return next(
            (l for l in self._listeners if l.port == int(MinerTypeHint.COMMON)), None
        )

    def _append_listener(self, port: int) -> None:
        # guard: don't try and bind to the common port if it's already bound
        if int(port) == int(MinerTypeHint.COMMON) and self._get_common_listener():
            return
        listener = Listener(port=port, parent=self)
        if listener.bound:
            logger.info(f" start listening on {listener}")
            self._listeners.append(listener)
            return

        error = listener.listen_error
        if error is None:
            error = listener.set_listen_error("Failed to bind")
        logger.warning(f" failed to bind on {listener}: {error}")
        listener.close()
        listener.deleteLater()
        self.bind_failed.emit(error)

    def _start_listeners(self) -> None:
        for btn in [btn for btn in self._listen_for.buttons() if btn.isChecked()]:
            match self._listen_for.id(btn):
                case 1 | 4 | 5:  # antminer | volcminer | hammer
                    self._append_listener(MinerTypeHint.COMMON)
                case 2:  # iceriver
                    self._append_listener(MinerTypeHint.ICERIVER)
                case 3:  # whatsminer
                    self._append_listener(MinerTypeHint.WHATSMINER)
                case 6:  # goldshell
                    self._append_listener(MinerTypeHint.GOLDSHELL)
                case 7:  # sealminer
                    self._append_listener(MinerTypeHint.SEALMINER)
                case 8:  # elphapex
                    self._append_listener(MinerTypeHint.ELPHAPEX)
                case 9:  # auradine
                    self._append_listener(MinerTypeHint.AURADINE)
                case 10:  # ipollo
                    self._append_listener(MinerTypeHint.IPOLLO)
                case _:
                    continue
        for listener in self._listeners:
            listener.error.connect(self.emit_error_received)
            listener.result.connect(self.emit_report_received)

    def _stop_listeners(self) -> None:
        logger.info(" close listeners")
        if len(self._listeners):
            for listener in self._listeners:
                listener.result.disconnect(self.emit_report_received)
                listener.error.disconnect(self.emit_error_received)
                listener.close()
        self._listeners.clear()

    @Slot()
    def start(self, listen_for: QButtonGroup) -> bool:
        """Starts listeners for all selected buttons in listen_for configuration.
        Returns False if no listeners were started."""
        self._listen_for = listen_for
        self._start_listeners()
        return bool(self._listeners)

    def stop(self) -> None:
        """Stops all active listeners and clears IP report record."""
        self._stop_listeners()
        self.record.clear()

    def emit_report_received(self, result: IPReport) -> None:
        logger.debug(f" got listener result: {result}")
        result.updated_at = time.time()
        if self.record.add(result):
            logger.info(" received IP Report result.")
            self.report_received.emit(result)

    def emit_error_received(self, error: ListenerError) -> None:
        listener = self.sender()
        if isinstance(listener, Listener) and listener in self._listeners:
            listener.result.disconnect(self.emit_report_received)
            listener.error.disconnect(self.emit_error_received)
            self._listeners.remove(listener)

        logger.error(f" emit listen error! {error}")
        self.error_received.emit(error)
