import logging
from PyQt6.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
)
from mod.listener import Listener

logger = logging.getLogger(__name__)


class ListenerManager(QObject):
    listen_complete = pyqtSignal()
    listen_error = pyqtSignal()

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self.result = ""
        self.listeners = []

    def start_listeners(self, conf: dict):
        for type, enabled in conf.items():
            match type:
                case "antminer":
                    if enabled:
                        logger.info(" start listening on 0.0.0.0:14235.")
                        self.listeners.append(Listener(self, 14235))
                case "iceriver":
                    if enabled:
                        logger.info(" start listening on 0.0.0.0:11503.")
                        self.listeners.append(Listener(self, 11503))
                case "whatsminer":
                    if enabled:
                        logger.info(" start listening on 0.0.0.0:8888.")
                        self.listeners.append(Listener(self, 8888))
                case "volcminer":
                    if enabled:
                        logger.info(" start listening on 0.0.0.0:14236.")
                        self.listeners.append(Listener(self, 14236))
        for listener in self.listeners:
            listener.result.connect(self.emit_listen_complete)
            listener.error.connect(self.emit_listen_error)

    def stop_listeners(self):
        logger.info(" close listeners.")
        if len(self.listeners):
            for listener in self.listeners:
                listener.close()
        self.listeners = []

    @pyqtSlot()
    def start(self, conf: dict):
        # default action (start listeners)
        self.start_listeners(conf)

    def emit_listen_complete(self):
        logger.info(" listen_complete signal result.")
        self.result = ""
        for listener in self.listeners:
            self.result += listener.msg
            listener.msg = ""
        logger.debug(f" result: {self.result}.")
        self.listen_complete.emit()

    def emit_listen_error(self):
        logger.error(" listen_error signal result!")
        self.listen_error.emit()
