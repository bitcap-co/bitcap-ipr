# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
import time
from collections import OrderedDict

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QButtonGroup

from mod.lm.ipreport import IPReport
from mod.lm.listener import Listener

logger = logging.getLogger(__name__)

RECORD_MIN_AGE = 10.0


class Record(OrderedDict[str, IPReport]):
    """
    Record is a OrderedDict with a set size of record entries in FIFO order.
    """

    def __init__(self, capacity: int) -> None:
        super().__init__()
        self._record_cap = capacity
        self._check_size()

    def __setitem__(self, key: str, value: IPReport, /) -> None:
        super().__setitem__(key, value)
        self._check_size()

    def _check_size(self) -> None:
        while len(self) > self._record_cap:
            self.popitem(last=False)

    @property
    def capacity(self) -> int:
        return self._record_cap

    @property
    def size(self) -> int:
        return len(self)


class ListenerManager(QObject):
    """
    Listener Manager class

    Manages a configurable list of Listeners to facilitate IP Report listening
    for supported ASIC types.

    Args:
        parent (QObject) : parent object.

    Signals:
        listen_complete (IPReport) : emits IPReport result from Listener.result signal.
        listen_error (str): emits error from Listener.error signal.
    """

    # Signals
    listen_complete = Signal(IPReport)
    listen_error = Signal(str)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.record: Record = Record(capacity=10)
        self.listen_for: QButtonGroup
        self._listeners: list[Listener] = []

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}"

    @property
    def enabled(self) -> list[str]:
        """Get all enabled listener names from listener configuration.

        Returns:
            list[str]: list of enabled listener names.
        """
        return [
            btn.text().lower() for btn in self.listen_for.buttons() if btn.isChecked()
        ]

    @property
    def status(self) -> str:
        """Get the current status message of active listeners.

        Returns:
            str: string of active listener names. Empty if no active listeners.
        """
        if len(self._listeners):
            return ", ".join(
                btn.text() for btn in self.listen_for.buttons() if btn.isChecked()
            )
        return ""

    @property
    def count(self) -> int:
        """Get the number of active listeners.

        Returns:
            int: the number of active listeners.
        """
        return len(self._listeners)

    def _append_listener(self, port: int) -> None:
        listener = Listener(port=port, parent=self)
        if listener.bound:
            logger.info(
                f" start listening on {listener.addr.toString()}:{listener.port}"
            )
            return self._listeners.append(listener)
        return logger.warning(
            f" failed to bind on {listener.addr.toString()}[{listener.port}]. Maybe someone is already listening on this port?"
        )

    def _start_listeners(self) -> None:
        for btn in [btn for btn in self.listen_for.buttons() if btn.isChecked]:
            match self.listen_for.id(btn):
                case 1 | 4 | 5:  # antminer | volcminer | hammer
                    self._append_listener(14235)
                case 2:  # iceriver
                    self._append_listener(11503)
                case 3:  # whatsminer
                    self._append_listener(8888)
                case 6:  # goldshell
                    self._append_listener(1314)
                case 7:  # sealminer
                    self._append_listener(18650)
                case 8:  # elphapex
                    self._append_listener(9999)
                case 9:  # auradine
                    self._append_listener(12345)
                case _:
                    continue
        for listener in self._listeners:
            listener.error.connect(self.emit_listen_error)
            listener.result.connect(self.emit_listen_complete)

    def _stop_listeners(self) -> None:
        logger.info(" close listeners")
        if len(self._listeners):
            for listener in self._listeners:
                listener.result.disconnect(self.emit_listen_complete)
                listener.error.disconnect(self.emit_listen_error)
                listener.close()
        self._listeners = []

    @Slot()
    def start(self, listen_for: QButtonGroup) -> None:
        self.listen_for = listen_for
        self._start_listeners()

    def stop(self) -> None:
        self._stop_listeners()
        self.record.clear()

    def _is_duplicate_record(self, result: IPReport) -> bool:
        if not self.record.size:
            return False
        for ent in self.record.items():
            key, data = ent
            if key == result.src_ip:
                if data.src_mac != result.src_mac:
                    return False
                else:
                    # check record age
                    if time.time() - data.updated_at <= RECORD_MIN_AGE:
                        logger.warning(f" [{result.src_ip}] : duplicate packet.")
                        return True
                    return False
        return False

    def emit_listen_complete(self, result: IPReport) -> None:
        logger.debug(f" got listen_complete result: {result}")
        if not self._is_duplicate_record(result):
            logger.info(" listen_complete signal result.")
            result.updated_at = time.time()
            self.record[result.src_ip] = result
            self.listen_complete.emit(result)

    def emit_listen_error(self, error: str) -> None:
        logger.error(" listen_error signal result!")
        self.listen_error.emit(error)
