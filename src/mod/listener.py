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
        self.sock.bind(('0.0.0.0', self.port))


    @pyqtSlot()
    def run(self):
        while True:
            self.d = self.sock.recv(self.bufsize)
            if not (self.prev.decode('ascii') == self.d.decode('ascii')):
                self.d_str = self.d.decode('ascii')
                ip, mac = self.d_str.split(",")
                if (self.port == 11503):
                    ip = self.d_str.split(":")[1]
                    mac = 'ice-river'
                if (self.port == 8888):
                    ip, mac = self.d_str.split("M")
                    ip = ip[3:]
                    mac = mac[3:]
                self.d_str = ','.join([ip, mac])
                self.prev = self.d
                # signal that we received a buffer
                self.signals.result.emit()


    def close(self):
        self.sock.close()
