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

    def __init__(self):
        super().__init__()
        self.data = None
        self.listeners = []

    def start_listeners(self):
        self.listeners.append(Listener(14235))
        self.listeners.append(Listener(11503))
        self.listeners.append(Listener(8888))
        for listener in self.listeners:
            listener.signals.result.connect(self.listen_complete)
            listener.start()

    def stop_listeners(self):
        if len(self.listeners):
            for listener in self.listeners:
                listener.close()
                listener.terminate()
        self.listeners = []

    @pyqtSlot()
    def run(self):
        # default action (start listeners)
        self.start_listeners()

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
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
            self.actionAutoOpenIPInBrowser.setChecked(config['options']['autoOpenIPInBrowser'])
            self.actionDisableInactiveTimer.setChecked(config['options']['disableInactiveTimer'])

        self.label_2.setPixmap(QPixmap(os.path.join(scalable, 'BitCapIPRCenterLogo.svg')))
        self.show()

        self.thread = ListenerManager()
        self.thread.completed.connect(self.show_confirm)

        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(self.stop_listen)

        self.confirm = IPRConfirmation()
        self.confirm.actionOpenBrowser.clicked.connect(self.open_dashboard)
        self.confirm.accept.clicked.connect(self.hide_confirm)

        self.actionIPRStart.clicked.connect(self.start_listen)
        self.actionIPRStop.clicked.connect(self.stop_listen)
        self.actionQuit.triggered.connect(self.quit)

    def start_listen(self):
        self.actionIPRStart.setEnabled(False)
        self.actionIPRStop.setEnabled(True)
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        instance = {
            "options": {
                "autoOpenIPInBrowser": self.actionAutoOpenIPInBrowser.isChecked(),
                "disableInactiveTimer": self.actionDisableInactiveTimer.isChecked()
            }
        }
        self.instance_json = json.dumps(instance, indent=4)
        with open('config.json', 'w') as f:
            f.write(self.instance_json)
        QMessageBox.warning(self, "BitCapIPR.exe", "UDP listening on 0.0.0.0[:8888,11503,14235]...\nPress the 'IP Report' button on miner after this dialog.")
        self.thread.start()

    def stop_listen(self):
        # if inactive timer is enabled
        if not self.actionDisableInactiveTimer.isChecked():
            QMessageBox.warning(self, "BitCapIPR.exe", "Stopped or Idle Timeout exceeded! Stopping listeners...")
            self.inactive.stop()
        self.thread.stop_listeners()
        self.actionIPRStart.setEnabled(True)
        self.actionIPRStop.setEnabled(False)

    def open_dashboard(self, ip):
        self.hide_confirm()
        if not ip:
            ip = self.confirm.lineIPField.text()
        webbrowser.open('http://{0}'.format(ip), new=2)

    def show_confirm(self):
        self.inactive.start()
        ip, mac = self.thread.data.split(',')
        if (self.actionAutoOpenIPInBrowser.isChecked()):
            self.open_dashboard(ip)
            return
        self.confirm.lineIPField.setText(ip)
        self.confirm.lineMACField.setText(mac)
        self.confirm.show()

    def hide_confirm(self):
        self.confirm.hide()

    def quit(self):
        self.thread.stop_listeners()
        self.thread.terminate()
        self.close()
        self = None


app = QApplication(sys.argv)
app.setWindowIcon(QIcon(os.path.join(icons, 'BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png')))
app.setStyle('Fusion')

w = MainWindow()
app.exec()
