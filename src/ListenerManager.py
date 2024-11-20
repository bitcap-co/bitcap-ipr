import logging
from PyQt6.QtCore import (
    QThread,
    pyqtSignal,
    pyqtSlot,
)
from mod.listener import Listener

logger = logging.getLogger(__name__)

class ListenerManager(QThread):
    completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.data = None
        self.listeners = []

    def start_listeners(self):
        logger.info(" start listening on 0.0.0.0:14235.")
        self.listeners.append(Listener(14235))
        logger.info(" start listening on 0.0.0.0:11503.")
        self.listeners.append(Listener(11503))
        logger.info(" start listening on 0.0.0.0:8888.")
        self.listeners.append(Listener(8888))
        for listener in self.listeners:
            listener.signals.result.connect(self.listen_complete)
            listener.start()

    def stop_listeners(self):
        logger.info(" close listeners.")
        if len(self.listeners):
            for listener in self.listeners:
                listener.close()
                listener.exit()
        self.listeners = []

    @pyqtSlot()
    def run(self):
        # default action (start listeners)
        self.start_listeners()

    def listen_complete(self):
        logger.info(" listen_complete signal result.")
        self.data = ""
        for listener in self.listeners:
            self.data += listener.d_str
            listener.d_str = ""
        logger.info(" send completed.")
        self.completed.emit()
