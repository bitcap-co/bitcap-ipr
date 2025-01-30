import time
import socket
import logging
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class Memory:
    def __init__(self, size: int):
        self.size = size
        self.dict = {}

    def __setitem__(self, key, value):
        if len(self.dict) >= self.size:
            self.dict.popitem()
        self.dict[key] = value

    def __getitem__(self, key):
        return self.dict[key]


class ListenerSignals(QObject):
    result = pyqtSignal()
    error = pyqtSignal()


class Listener(QThread):
    def __init__(self, port: int):
        super().__init__()
        self.signals = ListenerSignals()
        self.bufsize = 40
        self.port = port
        self.memory = Memory(size=10)
        self.d_str = ""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", self.port))

    @pyqtSlot()
    def run(self):
        while True:
            try:
                self.d = self.sock.recv(self.bufsize)
            except Exception:
                break
            self.d_str = self.d.decode("ascii")
            if self.d_str:
                logger.info(f"Listener[{self.port}] : received msg.")
                logger.debug(f"Listener[{self.port}] : d_str {self.d_str}")
                match self.port:
                    case 11503:  # IceRiver
                        type = "iceriver"
                        try:
                            ip = self.d_str.split(":")[1]
                        except IndexError:
                            logger.warning(f"Listener[{self.port}] : Failed to unpack msg! Ignoring...")
                            continue
                        mac = "ice-river"
                    case 8888:  # Whatsminer
                        type = "whatsminer"
                        try:
                            ip, mac = self.d_str.split("M")
                        except ValueError:
                            logger.warning(f"Listener[{self.port}] : Failed to unpack msg! Ignoring...")
                            continue
                        ip = ip[3:]
                        mac = mac[3:]
                    case 14235:  # AntMiner
                        type = "antminer"
                        try:
                            ip, mac = self.d_str.split(",")
                        except ValueError:
                            logger.warning(f"Listener[{self.port}] : Failed to unpack msg! Ignoring...")
                            continue
                logger.debug(f"Listener[{self.port}] : found type {type} from port.")
                if self.memory.dict:
                    prev_entry = False
                    # sort by timestamp descending
                    self.memory.dict = dict(
                        sorted(
                            self.memory.dict.items(),
                            reverse=True,
                            key=lambda item: float(item[1][1]),
                        )
                    )
                    for entry in self.memory.dict.keys():
                        _data = self.memory.dict.get(entry)
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
            else:
                logger.warning(f"Listener[{self.port}] : d_str empty! Ignoring.")

    def emit_received(self, received):
        logger.info(f"Listener[{self.port}] : emit received.")
        self.memory[received[0]] = [self.d, time.time()]
        self.d_str = ",".join(received)
        # signal that we received a buffer
        self.signals.result.emit()

    def emit_error(self, err):
        logger.error(f"Listener[{self.port}] : emit error! got {err}")
        self.signals.error.emit()

    def close(self):
        logger.info(f"Listener[{self.port}] : close socket.")
        self.memory.dict = {}  # clear memory
        self.sock.close()
        self.sock = None
