import os
import sys
import json
import webbrowser
from mod.listener import Listener

from PyQt6.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QWidget
)
from PyQt6.QtGui import QIcon, QPixmap

from ui.GUI import Ui_MainWindow, Ui_IPRConfirmation

basedir = os.path.dirname(__file__)
icons = os.path.join(basedir, 'resources/icons/app')
scalable = os.path.join(basedir, 'resources/scalable')

# windows taskbar
try:
    from ctypes import windll

    myappid = "bitcap.ipr.ipreporter"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class ListenerManager(QThread):

    completed = pyqtSignal()

    @pyqtSlot()
    def run(self):
        self.data = None
        self.listeners.append(Listener(14235))
        self.listeners.append(Listener(11503))
        self.listeners.append(Listener(8888))
        for listener in self.listeners:
            listener.signals.result.connect(self.listen_complete)
            listener.start()

    def listen_complete(self):
        self.data = ''
        for listener in self.listeners:
            self.data += listener.d_str
            listener.d_str = ''
        self.completed.emit()


class IPRConfirmation(QWidget, Ui_IPRConfirmation):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.label_2.setPixmap(QPixmap(os.path.join(scalable, 'BitCapIPRCenterLogo.svg')))
        self.show()

        self.thread = ListenerManager()
        self.thread.listeners = []
        self.thread.completed.connect(self.show_confirm)

        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(self.stop_listen)

        self.confirm = IPRConfirmation()
        self.confirm.openChrome.clicked.connect(self.open_dashboard)
        self.confirm.accept.clicked.connect(self.hide_confirm)

        self.IPRButtonStart.clicked.connect(self.start_listen)
        self.IPRButtonStop.clicked.connect(self.stop_listen)
        self.actionQuit.triggered.connect(self.quit)

    def start_listen(self):
        self.inactive.start()
        self.IPRButtonStart.setEnabled(False)
        # self.instance
        QMessageBox.warning(self, "BitCapIPR.exe", "UDP listening on 0.0.0.0[:8888,11503,14235]...\nPress the 'IP Report' button on miner after this dialog.")
        self.thread.start()

    def stop_listen(self):
        # if inactive timer is enabled
        # QMessageBox.warning(self, "BitCapIPR.exe", "Stopped or Idle Timeout exceeded! Stopping listeners...")
        self.inactive.stop()
        self.IPRButtonStart.setEnabled(True)
        for listener in self.thread.listeners:
            listener.close()
            listener.terminate()
        self.thread.listeners = []
        self.thread.terminate()

    def open_dashboard(self, ip):
        self.hide_confirm()
        if not ip:
            ip = self.confirm.ipField.text()
        webbrowser.open('http://{0}'.format(ip), new=2)

    def show_confirm(self):
        self.inactive.start()
        ip, mac = self.thread.data.split(',')
        if (self.actionAutoOpenIP.isChecked()):
            self.open_dashboard(ip)
            return
        self.confirm.ipField.setText(ip)
        self.confirm.macField.setText(mac)
        self.confirm.show()

    def hide_confirm(self):
        self.confirm.hide()

    def quit(self):
        for listener in self.thread.listeners:
            listener.close()
            listener.terminate()
        self.thread.listeners = []
        self.thread.terminate()
        self.close()
        self = None


app = QApplication(sys.argv)
app.setWindowIcon(QIcon(os.path.join(icons, 'BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png')))
app.setStyle('Fusion')

w = MainWindow()
app.exec()
