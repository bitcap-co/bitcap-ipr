from __future__ import annotations

import logging
from typing import Any, Dict, List

from pydantic import BaseModel
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QButtonGroup

from .listener import Listener

logger = logging.getLogger(__name__)


class ListenerResult(BaseModel):
    miner_type: str
    ip: str
    mac: str
    serial: str = ""
    created_at: float
    updated_at: float


class ListenerManager(QObject):
    """
    Listener manager class

    Args:
        parent (QObject): parent object.

    Signals:
        listen_complete (Signal(ListenerResult)): emits ListenerResult result from Listener.result signal.
        listen_error (Signal(str)): emits error from Listener.error signal.
    """

    listen_complete = Signal(ListenerResult)
    listen_error = Signal(str)

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self._listeners: List[Listener] = []
        self._listen_config: QButtonGroup

    @property
    def config(self) -> QButtonGroup:
        """Get listener configuration.

        Returns:
            QButtonGroup: The current listener configuration.
        """
        return self._listen_config

    @property
    def enabled(self) -> List[str]:
        """Get enabled listeners from config.

        Returns:
            List[str]: All enabled listeners names from config.
        """
        return [btn.text() for btn in self._listen_config.buttons() if btn.isChecked()]

    @property
    def listeners(self) -> List[Listener]:
        """Get all active listeners.

        Returns:
            List[Listener]: The list of appended listeners.
        """
        return self._listeners

    @property
    def count(self) -> int:
        """Get count of listeners.

        Returns:
            int: the length of appended listeners.
        """
        return len(self._listeners)

    @property
    def status(self) -> str:
        """Get status message of active listeners.

        Returns:
            str: string of appended listener names.
        """
        if len(self._listeners):
            return ", ".join(
                btn.text() for btn in self._listen_config.buttons() if btn.isChecked()
            )
        return ""

    def _append_listener(self, port: int):
        listener = Listener(port=port, parent=self)
        if listener.bound:
            logger.info(f" start listening on 0.0.0.0:{port}")
            self._listeners.append(listener)

    def _start_listeners(self, conf: QButtonGroup):
        enabled = [x for x in conf.buttons() if x.isChecked()]
        for listenFor in enabled:
            match conf.id(listenFor):
                case 1 | 4:  # antminer | volcminer
                    self._append_listener(14235)
                case 2:  # iceriver
                    self._append_listener(11503)
                case 3:  # whatsminer
                    self._append_listener(8888)
                case 5:  # goldshell
                    self._append_listener(1314)
                case 6:  # sealminer
                    self._append_listener(18650)
                case 7:  # elphapex
                    self._append_listener(9999)
        for listener in self._listeners:
            listener.result.connect(self._emit_listen_complete)
            listener.error.connect(self._emit_listen_error)

    def _stop_listeners(self):
        logger.info(" close listeners.")
        if len(self._listeners):
            for listener in self._listeners:
                listener.close()
        self._listeners = []

    @Slot()
    def start(self, listen_config: QButtonGroup):
        self._listen_config = listen_config
        self._start_listeners(listen_config)

    def stop(self):
        self._stop_listeners()

    def _emit_listen_complete(self, result: Dict[str, Any]):
        logger.info(" listen_complete signal result.")
        logger.debug(f" result: {result}.")
        result_obj = ListenerResult.model_construct(**result)
        self.listen_complete.emit(result_obj)

    def _emit_listen_error(self, error: str):
        logger.error(" listen_error signal result!")
        self.listen_error.emit(error)
