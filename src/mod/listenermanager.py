import logging
from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)
from PySide6.QtWidgets import QButtonGroup
from mod.listener import Listener

logger = logging.getLogger(__name__)


class ListenerManager(QObject):
    listen_complete = Signal()
    listen_error = Signal()

    def __init__(self, parent: QObject):
        super().__init__(parent)
        self.result = ""
        self.listeners = []

    def start_listeners(self, conf: QButtonGroup):
        for listenFor in conf.buttons():
            match conf.id(listenFor):
                case 1:  # antminer
                    if listenFor.isChecked():
                        logger.info(" start listening on 0.0.0.0:14235.")
                        self.listeners.append(Listener(self, 14235))
                case 2:  # iceriver
                    if listenFor.isChecked():
                        logger.info(" start listening on 0.0.0.0:11503.")
                        self.listeners.append(Listener(self, 11503))
                case 3:  # whatsminer
                    if listenFor.isChecked():
                        logger.info(" start listening on 0.0.0.0:8888.")
                        self.listeners.append(Listener(self, 8888))
                case 5:  # goldshell
                    if listenFor.isChecked():
                        logger.info(" start listening on 0.0.0.0:1314.")
                        self.listeners.append(Listener(self, 1314))
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
