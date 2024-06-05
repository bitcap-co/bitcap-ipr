import socket
import asyncio
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


class ListenerSignals(QObject):
    result = pyqtSignal()


class DgramProtocol(asyncio.DatagramProtocol):
    def __init__(self, port, signals):
        super().__init__()
        self.transport = None
        self.prev = b''
        self.d_str = ''
        self.port = port
        self.signals = signals

    def connection_made(self, transport) -> "Used by asyncio":
        self.transport = transport

    def datagram_received(self, data, addr) -> "Main entrypoint for processing message":
        # Here is where you would push message to whatever methods/classes you want.
        if not (self.prev.decode('ascii') == data.decode('ascii')):
            self.d_str = data.decode('ascii')
            match self.port:
                case 11503:  # IceRiver
                    ip = self.d_str.split(":")[1]
                    mac = 'ice-river'
                case 8888:  #Whatsminer
                    ip, mac = self.d_str.split("M")
                    ip = ip[3:]
                    mac = mac[3:]
                case 14235:  #AntMiner
                    ip, mac = self.d_str.split(",")

            self.d_str = ','.join([ip, mac])
            self.prev = data
            # signal that we received a buffer
            self.signals.result.emit()


class Listener(QThread):
    def __init__(self, port):
        super().__init__()
        self.signals = (ListenerSignals())
        self.port = port
        self.loop = asyncio.new_event_loop()
        # self.bufsize = 40
        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.bind(('0.0.0.0', self.port))

    @pyqtSlot()
    def run(self):
        asyncio.set_event_loop(self.loop)

        listener = self.loop.create_datagram_endpoint(
            lambda: DgramProtocol(self.port, self.signals),
            local_addr=('0.0.0.0', self.port)
        )
        self.loop.run_until_complete(listener)
        self.loop.run_forever()

    def close(self):
        pass
        #self.transport.close()
