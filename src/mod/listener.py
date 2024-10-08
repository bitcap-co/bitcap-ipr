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
        self.prev = b''
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
            if not (self.prev.decode('ascii') == self.d.decode('ascii')):
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

                self.d_str = ','.join([ip, mac, type])
                self.prev = self.d
                # signal that we received a buffer
                self.signals.result.emit()

    def close(self):
        self.sock.close()
