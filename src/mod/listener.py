import time
import socket
import logging
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class ListenerSignals(QObject):
    result = pyqtSignal()


class Listener(QThread):
    def __init__(self, port, addr: str = "0.0.0.0"):
        super().__init__()
        self.signals = ListenerSignals()
        self.bufsize = 40
        self.addr = addr
        self.port = port
        self.memory = {}
        self.d_str = ""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.addr, self.port))

    @pyqtSlot()
    def run(self):
        while True:
            try:
                self.d = self.sock.recv(self.bufsize)
            except Exception:
                break
            self.d_str = self.d.decode("ascii")
            logger.info(f"Listener[{self.port}] : received msg.")
            logger.info(f"Listener[{self.port}] : d_str {self.d_str}")
            match self.port:
                case 11503:  # IceRiver
                    type = "iceriver"
                    ip = self.d_str.split(":")[1]
                    mac = "ice-river"
                case 8888:  # Whatsminer
                    type = "whatsminer"
                    ip, mac = self.d_str.split("M")
                    ip = ip[3:]
                    mac = mac[3:]
                case 14235:  # AntMiner
                    type = "antminer"
                    ip, mac = self.d_str.split(",")
            logger.info(f"Listener[{self.port}] : found type {type} from port.")
            if self.memory:
                prev_entry = False
                # sort by timestamp descending
                self.memory = dict(
                    sorted(
                        self.memory.items(),
                        reverse=True,
                        key=lambda item: float(item[1][1]),
                    )
                )
                for entry in self.memory.keys():
                    _data = self.memory.get(entry)
                    if ip == entry and self.d == _data[0]:
                        prev_entry = True
                        if (
                            time.time() - _data[1] <= 10.0
                        ):  # prevent duplicate packet data
                            break
                        else:
                            self.emit_received([ip, mac, type])
                if not prev_entry:
                    self.emit_received([ip, mac, type])
            else:
                # first entry
                self.emit_received([ip, mac, type])

    def emit_received(self, received):
        logger.info(f"Listener[{self.port}] : emit received.")
        self.memory.update({f"{received[0]}": [self.d, time.time()]})
        self.d_str = ",".join(received)
        # signal that we received a buffer
        self.signals.result.emit()

    def close(self):
        logger.info(f"Listener[{self.port}] : close socket.")
        self.memory = None  # clear memory
        self.sock.close()
