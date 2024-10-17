import time
import socket
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


class ListenerSignals(QObject):
    result = pyqtSignal()


class Listener(QThread):
    def __init__(self, port):
        super().__init__()
        self.signals = (ListenerSignals())
        self.bufsize = 40
        self.port = port
        self.memory = {}
        self.d_str = ''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))

    @pyqtSlot()
    def run(self):
        while True:
            try:
                self.d = self.sock.recv(self.bufsize)
            except Exception:
                break
            self.d_str = self.d.decode('ascii')
            match self.port:
                    case 11503:  # IceRiver
                        type = "iceriver"
                        ip = self.d_str.split(":")[1]
                        mac = 'ice-river'
                    case 8888:  # Whatsminer
                        type = "whatsminer"
                        ip, mac = self.d_str.split("M")
                        ip = ip[3:]
                        mac = mac[3:]
                    case 14235:  # AntMiner
                        type = "antminer"
                        ip, mac = self.d_str.split(",")
            if self.memory:
                prev_entry = False
                # sort by timestamp descending
                self.memory = dict(sorted(self.memory.items(), reverse=True, key=lambda item: float(item[1][1])))
                for entry in self.memory.keys():
                    _data = self.memory.get(entry)
                    if ip == entry and self.d == _data[0]:
                        prev_entry = True
                        if time.time() - _data[1] <= 10.0: # prevent duplicate packet data
                            break
                        else:
                            self.emit_received([ip, mac, type])
                if not prev_entry:
                    self.emit_received([ip, mac, type])
            else:
                # first entry
                self.emit_received([ip, mac, type])

    def emit_received(self, received):
        self.memory.update({f"{received[0]}": [self.d, time.time()]})
        self.d_str = ','.join(received)
        # signal that we received a buffer
        self.signals.result.emit()

    def close(self):
        self.memory = None # clear memory
        self.sock.close()
