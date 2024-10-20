import os
import sys
from pathlib import Path
import time
from datetime import datetime
import json
import webbrowser
import requests
from requests.auth import HTTPDigestAuth
from mod.listener import Listener

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QThread,
    pyqtSignal,
    pyqtSlot,
    QFile,
    QIODevice,
    QTextStream,
    QSystemSemaphore,
    QSharedMemory
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QWidget,
    QTableWidgetItem,
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
    "version": "1.0.3",
    "author": "MatthewWertman",
    "source": "https://github.com/bitcap-co/bitcap-ipr",
    "company": "Bit Capital Group",
    "desc": "cross-platform IP Reporter\nthat listens for AntMiners, IceRivers, and Whatsminers.",
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
                listener.exit()
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

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.actionVersion.setText(f"Version {app_info['version']}")
        self.label_2.setPixmap(QPixmap(os.path.join(scalable, 'BitCapIPRCenterLogo.svg')))
        self.tableWidget.setHorizontalHeaderLabels(["IP", "MAC", "SERIAL", "TYPE"])
        self.children = []

        # MainWindow Signals
        self.actionAbout.triggered.connect(self.about)
        self.actionReportIssue.triggered.connect(self.open_issues)
        self.actionSourceCode.triggered.connect(self.open_source)
        self.actionKillAllConfirmations.triggered.connect(self.killall)
        self.actionQuit.triggered.connect(self.quit)
        self.menuOptions.triggered.connect(self.update_settings)
        self.menuTable.triggered.connect(self.update_settings)
        self.actionEnableIDTable.triggered.connect(self.update_stacked_widget)
        self.actionSetDefaultAPIPassword.triggered.connect(self.show_api_config)
        self.actionCopySelectedElements.triggered.connect(self.copy_selected)
        self.actionExport.triggered.connect(self.export_table)

        self.actionIPRStart.clicked.connect(self.start_listen)
        self.actionIPRStop.clicked.connect(self.stop_listen)
        self.actionIPRSetPasswd.clicked.connect(self.set_api_passwd)

        self.config_path = Path(Path.home(), '.config', 'ipr').resolve()
        self.settings = Path(self.config_path, 'instance.json')
        if os.path.exists(self.settings):
            with open(self.settings, 'r') as f:
                config = json.load(f)
            self.actionAlwaysOpenIPInBrowser.setChecked(config['options']['alwaysOpenIPInBrowser'])
            self.actionDisableInactiveTimer.setChecked(config['options']['disableInactiveTimer'])
            self.actionDisableWarningDialog.setChecked(config['options']['disableWarningDialog'])
            self.actionAutoStartOnLaunch.setChecked(config['options']['autoStartOnLaunch'])
            self.actionEnableIDTable.setChecked(config['table']['enableIDTable'])

        self.thread = ListenerManager()
        self.thread.completed.connect(self.show_confirm)

        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        self.update_stacked_widget()

        if self.actionAutoStartOnLaunch.isChecked():
            self.start_listen()

    def about(self):
        QMessageBox.information(self, "BitCapIPR", f"{app_info['name']} is a {app_info['desc']}\nVersion {app_info['version']}\n{app_info['author']}\nPowered by {app_info['company']}\n")

    def open_issues(self):
        webbrowser.open(f"{app_info['source']}/issues", new=2)

    def open_source(self):
        webbrowser.open(f"{app_info['source']}", new=2)

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
        if self.actionEnableIDTable.isChecked():
            self.tableWidget.setRowCount(0)
        self.thread.stop_listeners()
        self.actionIPRStart.setEnabled(True)
        self.actionIPRStop.setEnabled(False)

    def set_api_passwd(self):
        passwd = self.linePasswdField.text()
        if not passwd:
            # if passwd is blank, exit
            confirm = QMessageBox.question(self, 'BitCapIPR', 'No supplied password. Do you want to leave the config?', QMessageBox.StandardButton.No|QMessageBox.StandardButton.Yes, defaultButton=QMessageBox.StandardButton.Yes)
            if confirm == QMessageBox.StandardButton.Yes:
                self.update_stacked_widget()
            return

        config = {
            "defaultAPIPasswd": passwd
        }
        config_json = json.dumps(config, indent=4)
        with open(Path(self.config_path, 'config.json'), 'w') as f:
            f.write(config_json)
        QMessageBox.information(self, 'BitCapIPR', 'Successfully wrote to config.')
        self.linePasswdField.clear()
        self.update_stacked_widget()

    def open_dashboard(self, ip):
        webbrowser.open('http://{0}'.format(ip), new=2)

    def update_stacked_widget(self):
        if self.actionEnableIDTable.isChecked():
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)

    def show_confirm(self):
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        ip, mac, type = self.thread.data.split(',')
        if self.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip)
            return
        confirm = IPRConfirmation()
        # IPRConfirmation Signals
        confirm.actionOpenBrowser.clicked.connect(lambda: self.open_dashboard(ip))
        confirm.accept.clicked.connect(lambda: self.hide_confirm(confirm))
        # copy action
        confirm.lineIPField.actionCopy = confirm.lineIPField.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), QLineEdit.ActionPosition.TrailingPosition)
        confirm.lineIPField.actionCopy.triggered.connect(lambda: self.copy_text(confirm.lineIPField))
        confirm.lineMACField.actionCopy = confirm.lineMACField.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon), QLineEdit.ActionPosition.TrailingPosition)
        confirm.lineMACField.actionCopy.triggered.connect(lambda: self.copy_text(confirm.lineMACField))
        confirm.lineIPField.setText(ip)
        confirm.lineMACField.setText(mac)
        confirm.show()
        confirm.activateWindow()
        self.children.append(confirm)
        if self.actionEnableIDTable.isChecked():
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)
            self.tableWidget.setItem(rowPosition, 0, QTableWidgetItem(ip))
            self.tableWidget.setItem(rowPosition, 1, QTableWidgetItem(mac))
            # SERIAL
            serial = 'N/A'
            uri = None
            endpoints = [f'http://{ip}/api/v1/info', f'http://{ip}/cgi-bin/get_system_info.cgi']
            with open(Path(self.config_path, 'config.json'), 'r') as f:
                config = json.load(f)
                passwd = config['defaultAPIPasswd']

            for endp in range(0, (len(endpoints))):
                r = requests.get(endpoints[endp], auth=HTTPDigestAuth('root', passwd))
                if r.status_code == 401:
                    # first pass failed
                    passwd = 'root'
                    r = requests.head(endpoints[endp], auth=HTTPDigestAuth('root', passwd))
                    # second pass fail; abort
                    if r.status_code == 401:
                        endp = None
                        break
                if r.status_code == 200:
                    uri = endp
                    break

            match endp:
                case 0:
                    r = requests.get(endpoints[uri])
                    r_json = r.json()
                    if 'serial' in r_json:
                        serial = r.json()['serial']
                case 1:
                    r = requests.get(endpoints[uri], auth= HTTPDigestAuth('root', passwd))
                    r_json = r.json()
                    if 'serinum' in r_json:
                        serial = r.json()['serinum']
                case None:
                    # failed to authenticate
                    serial = "Failed auth"

            self.tableWidget.setItem(rowPosition, 2, QTableWidgetItem(serial))
            # ASIC TYPE
            self.tableWidget.setItem(rowPosition, 3, QTableWidgetItem(type))

    def show_api_config(self):
        self.stackedWidget.setCurrentIndex(2)

    def copy_selected(self):
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        out = ""
        for i in range(rows):
            for j in range(cols):
                if self.tableWidget.item(i, j).isSelected():
                    out += self.tableWidget.item(i, j).text()
                    out += ';'
            out += '\n'
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(out.strip(), mode=cb.Mode.Clipboard)

    def export_table(self):
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        out = "IP, MAC, SERIAL, TYPE, \n"
        for i in range(rows):
            for j in range(cols):
                out += self.tableWidget.item(i, j).text()
                out += ','
            out += "\n"

        # .csv
        p = Path(Path.home(), 'Documents', 'ipr').resolve()
        Path.mkdir(p, exist_ok=True)
        file = QFile(os.path.join(p, f"id_table-{datetime.now().strftime('%Y-%m-%d')}-{time.time().__floor__()}.csv"))
        if not file.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Truncate):
            return
        outfile = QTextStream(file)
        outfile << out << "\n"
        QMessageBox.information(self, "BitCapIPR", f"Successfully wrote csv to {p}.")

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
                "autoStartOnLaunch": self.actionAutoStartOnLaunch.isChecked(),
            },
            "table": {
                "enableIDTable": self.actionEnableIDTable.isChecked()
            }
        }
        self.instance_json = json.dumps(instance, indent=4)
        with open(self.settings, 'w') as f:
            f.write(self.instance_json)

    def killall(self):
        for c in self.children:
            c.close()

    def quit(self):
        self.thread.stop_listeners()
        self.thread.exit()
        self.killall()
        self.close()
        self = None

    # hook MainWindow close event
    def closeEvent(self, event):
        self.quit()

def launch_app():
    app = QApplication(sys.argv)
    # first-time launch
    config_path = Path(Path.home(), '.config', 'ipr').resolve()
    os.makedirs(config_path, exist_ok=True)
    if not os.path.exists(Path(config_path, 'config.json')):
        # no config so write them on first-time launch
        default_instance = {
            "options": {
                "alwaysOpenIPInBrowser": False,
                "disableInactiveTimer": False,
                "disableWarningDialog": False,
                "autoStartOnLaunch": False,
            },
            "table": {
                "enableIDTable": False
            }
        }
        default_instance_json = json.dumps(default_instance, indent=4)
        with open(Path(config_path, 'instance.json'), 'w') as f:
            f.write(default_instance_json)

        default_config = {
            "defaultAPIPasswd": ""
        }
        default_config_json = json.dumps(default_config, indent=4)
        with open(Path(config_path, 'config.json'), 'w') as f:
            f.write(default_config_json)

    # Here we are making sure that only one instance is running at a time
    window_key = 'BitCapIPR'
    shared_mem_key = 'IPRSharedMemory'
    semaphore = QSystemSemaphore(window_key, 1)
    semaphore.acquire()

    if sys.platform != 'win32':
        # manually destroy shared memory if on unix
        unix_fix_shared_mem = QSharedMemory(shared_mem_key)
        if unix_fix_shared_mem.attach():
            unix_fix_shared_mem.detach()

    shared_mem = QSharedMemory(shared_mem_key)

    if shared_mem.attach():
        is_running = True
    else:
        shared_mem.create(1)
        is_running = False

    semaphore.release()

    if is_running:
        # if already running, send warning dialog and close app
        QMessageBox.warning(None, "BitCapIPR - Application already running", "One instance of the application is already running.")
        return

    app.setWindowIcon(QIcon(os.path.join(icons, 'BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png')))
    app.setStyle('Fusion')

    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    launch_app()
