import logging
from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)
from PySide6.QtWidgets import QButtonGroup
from .listener import Listener

logger = logging.getLogger(__name__)


class ListenerManager(QObject):
    listen_complete = Signal(list)
    listen_error = Signal()

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self.listeners = []

    def append_listener(self, port: int):
        listener = Listener(self, port)
        if listener.bound:
            logger.info(f" start listening on 0.0.0.0:{port}")
            self.listeners.append(listener)

    def start_listeners(self, conf: QButtonGroup):
        for listenFor in conf.buttons():
            match conf.id(listenFor):
                case 1 | 4:  # antminer | volcminer
                    if listenFor.isChecked():
                        self.append_listener(14235)
                case 2:  # iceriver
                    if listenFor.isChecked():
                        self.append_listener(11503)
                case 3:  # whatsminer
                    if listenFor.isChecked():
                        self.append_listener(8888)
                case 5:  # goldshell
                    if listenFor.isChecked():
                        self.append_listener(1314)
                case 6:  # sealminer
                    if listenFor.isChecked():
                        self.append_listener(18650)
        for listener in self.listeners:
            listener.result.connect(self.emit_listen_complete)
            listener.error.connect(self.emit_listen_error)

    def stop_listeners(self):
        logger.info(" close listeners.")
        if len(self.listeners):
            for listener in self.listeners:
                listener.close()
        self.listeners = []

    @Slot()
    def start(self, listenConfig: QButtonGroup):
        # default action (start listeners)
        self.start_listeners(listenConfig)

    def emit_listen_complete(self, result: list):
        logger.info(" listen_complete signal result.")
        logger.debug(f" result: {result}.")
        self.listen_complete.emit(result)

    def emit_listen_error(self):
        logger.error(" listen_error signal result!")
        self.listen_error.emit()
