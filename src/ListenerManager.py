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

    def __init__(self, addrs : list = ["0.0.0.0"], ports : list = [14235, 11503, 8888]):
        super().__init__()
        self.data = None
        self.addrs = addrs
        self.ports = ports
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

    def start_custom_listeners(self):
        for port in self.ports:
            for addr in self.addrs:
                logger.info(f" start listening on {addr}:{port}.")
                self.listeners.append(Listener(port, addr))

        for listener in self.listeners:
            listener.signals.result.connect(self.listen_complete)
            logger.info(" start custom listener")
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
        if self.addrs or self.ports:
            logger.info(" start custom listeners.")
            self.start_custom_listeners()
        else:
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
