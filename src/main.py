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
    QWidget,
    QLineEdit,
    QStyle
)
from PyQt6.QtGui import QIcon, QPixmap

from ui.GUI import Ui_MainWindow, Ui_IPRConfirmation

basedir = os.path.dirname(__file__)
icons = os.path.join(basedir, 'resources/icons/app')
scalable = os.path.join(basedir, 'resources/scalable')

app_info = {
    "name": "BitCap IPReporter",
    "version": "0.2.3",
    "author": "MatthewWertman",
    "company": "BitCap",
    "desc": "cross-platform IP Reporter\nthat listens for AntMiners, IceRivers, and Whatsminers."
}

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

        self.actionVersion.setText(f"Version {app_info['version']}")
        self.label_2.setPixmap(QPixmap(os.path.join(scalable, 'BitCapIPRCenterLogo.svg')))
        self.children = []

        # MainWindow Signals
        self.actionHelp.triggered.connect(self.help)
        self.actionKillAllConfirmations.triggered.connect(self.killall)
        self.actionQuit.triggered.connect(self.quit)
        self.menuOptions.triggered.connect(self.update_settings)

        self.actionIPRStart.clicked.connect(self.start_listen)
        self.actionIPRStop.clicked.connect(self.stop_listen)

        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
            self.actionAlwaysOpenIPInBrowser.setChecked(config['options']['alwaysOpenIPInBrowser'])
            self.actionDisableInactiveTimer.setChecked(config['options']['disableInactiveTimer'])
            self.actionDisableWarningDialog.setChecked(config['options']['disableWarningDialog'])
            self.actionAutoStartOnLaunch.setChecked(config['options']['autoStartOnLaunch'])

        self.thread = ListenerManager()
        self.thread.completed.connect(self.show_confirm)

        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        if self.actionAutoStartOnLaunch.isChecked():
            self.start_listen()

    def start_listen(self):
        self.actionIPRStart.setEnabled(False)
        self.actionIPRStop.setEnabled(True)
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        if not self.actionDisableWarningDialog.isChecked() and not self.actionAutoStartOnLaunch.isChecked():
            QMessageBox.warning(self, "BitCapIPR", "UDP listening on 0.0.0.0[:8888,11503,14235]...\nPress the 'IP Report' button on miner after this dialog.")
        self.thread.start()

    def stop_listen(self, timeout):
        if timeout:
            QMessageBox.warning(self, "BitCapIPR", "Inactive Timeout exceeded! Stopping listeners...")
            self.inactive.stop()
        self.thread.stop_listeners()
        self.actionIPRStart.setEnabled(True)
        self.actionIPRStop.setEnabled(False)

    def open_dashboard(self, ip):
        webbrowser.open('http://{0}'.format(ip), new=2)

    def show_confirm(self):
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        ip, mac = self.thread.data.split(',')
        if self.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip)
            return
        confirm = IPRConfirmation()
        # IPRConfirmation Signals
        confirm.actionOpenBrowser.clicked.connect(lambda: self.open_dashboard(ip))
        confirm.accept.clicked.connect(lambda: self.hide_confirm(confirm))
        # copy action
        confirm.lineIPField.actionCopy = confirm.lineIPField.addAction(app.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), QLineEdit.ActionPosition.TrailingPosition)
        confirm.lineIPField.actionCopy.triggered.connect(lambda: self.copy_text(confirm.lineIPField))
        confirm.lineMACField.actionCopy = confirm.lineMACField.addAction(app.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), QLineEdit.ActionPosition.TrailingPosition)
        confirm.lineMACField.actionCopy.triggered.connect(lambda: self.copy_text(confirm.lineMACField))
        confirm.lineIPField.setText(ip)
        confirm.lineMACField.setText(mac)
        confirm.show()
        self.children.append(confirm)

    def hide_confirm(self, confirm):
        confirm.close()

    def copy_text(self, lineEdit):
        lineEdit.selectAll()
        lineEdit.copy()

    def update_settings(self):
        instance = {
            "options": {
                "alwaysOpenIPInBrowser": self.actionAlwaysOpenIPInBrowser.isChecked(),
                "disableInactiveTimer": self.actionDisableInactiveTimer.isChecked(),
                "disableWarningDialog": self.actionDisableWarningDialog.isChecked(),
                "autoStartOnLaunch": self.actionAutoStartOnLaunch.isChecked()
            }
        }
        self.instance_json = json.dumps(instance, indent=4)
        with open('config.json', 'w') as f:
            f.write(self.instance_json)

    def help(self):
        QMessageBox.information(self, "BitCapIPR", f"{app_info['name']} is a {app_info['desc']}\nVersion {app_info['version']}\n{app_info['author']}\nPowered by {app_info['company']}\n")

    def killall(self):
        for c in self.children:
            c.close()

    def quit(self):
        self.thread.stop_listeners()
        self.thread.terminate()
        for c in self.children:
            c.close()
        self.close()
        self = None


app = QApplication(sys.argv)
app.setWindowIcon(QIcon(os.path.join(icons, 'BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png')))
app.setStyle('Fusion')

w = MainWindow()
w.show()
app.exec()
