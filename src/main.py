import os
import sys
import socket
import time
import json
import logging
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
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
    QSharedMemory,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QWidget,
    QTableWidgetItem,
    QLineEdit,
    QStyle,
    QMenuBar,
)
from PyQt6.QtGui import QIcon, QPixmap
from ui.GUI import Ui_MainWindow, Ui_IPRConfirmation
from ui.TitleBar import TitleBar

basedir = os.path.dirname(__file__)
icons = os.path.join(basedir, "resources/icons/app")
scalable = os.path.join(basedir, "resources/scalable")

# logger
logger = logging.getLogger(__name__)

app_info = {
    "name": "BitCap IPReporter",
    "version": "1.0.4",
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
        logger.info("ListenerManager : start listening on 0.0.0.0:14235.")
        self.listeners.append(Listener(14235))
        logger.info("ListenerManager : start listening on 0.0.0.0:11503.")
        self.listeners.append(Listener(11503))
        logger.info("ListenerManager : start listening on 0.0.0.0:8888.")
        self.listeners.append(Listener(8888))
        for listener in self.listeners:
            listener.signals.result.connect(self.listen_complete)
            listener.start()

    def stop_listeners(self):
        logger.info("ListenerManager : close listeners.")
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
        logger.info("ListenerManager : listen_complete signal result.")
        self.data = ""
        for listener in self.listeners:
            self.data += listener.d_str
            listener.d_str = ""
        logger.info("ListenerManager : send completed.")
        self.completed.emit()


class IPRConfirmation(QWidget, Ui_IPRConfirmation):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )

        # title bar
        self.title_bar = TitleBar(self, "IP Confirmation", ['min', 'close'])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.window().close)
        title_bar_widget = self.titlebarwidget.layout()
        title_bar_widget.addWidget(self.title_bar)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )
        # title bar
        self.title_bar = TitleBar(self, "BitCap IPReporter", ['min', 'close'])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.quit)
        title_bar_widget = self.titlebarwidget.layout()
        title_bar_widget.addWidget(self.title_bar)

        # menu bar
        self.menu_bar = QMenuBar()
        self.menuHelp = self.menu_bar.addMenu("Help")
        self.menuHelp.setToolTipsVisible(True)
        self.menuOptions = self.menu_bar.addMenu("Options")
        self.menuOptions.setToolTipsVisible(True)
        self.menuTable = self.menu_bar.addMenu("Table")
        self.menuTable.setToolTipsVisible(True)
        self.menuQuit = self.menu_bar.addMenu("Quit")
        self.menuQuit.setToolTipsVisible(True)

        # help
        self.actionAbout = self.menuHelp.addAction("About")
        self.actionAbout.setToolTip("Opens the about dialog")
        self.actionReportIssue = self.menuHelp.addAction("Report Issue")
        self.actionReportIssue.setToolTip("Report a new issue on GitHub")
        self.actionSourceCode = self.menuHelp.addAction("Source Code")
        self.actionSourceCode.setToolTip("Opens the GitHub repo in browser")
        self.actionVersion = self.menuHelp.addAction(f"Version {app_info['version']}")
        self.actionVersion.setEnabled(False)

        # options
        self.actionAlwaysOpenIPInBrowser = self.menuOptions.addAction("Always Open IP in Browser")
        self.actionAlwaysOpenIPInBrowser.setCheckable(True)
        self.actionAlwaysOpenIPInBrowser.setToolTip("Always opens IPs in browser (No IP confirmation)")
        self.actionDisableInactiveTimer = self.menuOptions.addAction("Disable Inactive Timer")
        self.actionDisableInactiveTimer.setCheckable(True)
        self.actionDisableInactiveTimer.setToolTip("Disables inactive timer of 15 minutes (Listens until stopped)")
        self.actionDisableWarningDialog = self.menuOptions.addAction("Disable Warning Dialog")
        self.actionDisableWarningDialog.setCheckable(True)
        self.actionDisableWarningDialog.setToolTip("Disables warning dialog when starting listeners")
        self.actionAutoStartOnLaunch = self.menuOptions.addAction("Auto Start on Launch")
        self.actionAutoStartOnLaunch.setCheckable(True)
        self.actionAutoStartOnLaunch.setToolTip("Automatically start listeners on launch (Takes effect on next launch)")

        # table
        self.actionEnableIDTable = self.menuTable.addAction("Enable ID Table")
        self.actionEnableIDTable.setCheckable(True)
        self.actionEnableIDTable.setToolTip("Stores IP,MAC,SERIAL,TYPE,SUBTYPE in a table on confirmation")
        self.menuTableSettings = self.menuTable.addMenu("Table Settings")
        self.menuTableSettings.setToolTipsVisible(True)
        self.actionSetDefaultAPIPassword = self.menuTableSettings.addAction("Set Default API Password")
        self.actionSetDefaultAPIPassword.setToolTip("Set default API password to config. Used to get data from the miner")
        self.actionCopySelectedElements = self.menuTable.addAction("Copy Selected Elements")
        self.actionCopySelectedElements.setToolTip("Copy selected elements to clipboard. Drag or Ctrl-click to select multiple cols/rows")
        self.actionExport = self.menuTable.addAction("Export")
        self.actionExport.setToolTip("Export current table as .CSV file")

        # quit
        self.actionKillAllConfirmations = self.menuQuit.addAction("Kill All Confirmations")
        self.actionKillAllConfirmations.setToolTip("Kills all IP confirmation windows")
        self.actionQuit = self.menuQuit.addAction("Quit")
        self.actionQuit.setToolTip("Quits app")

        menubarwidget = self.menubarwidget.layout()
        menubarwidget.addWidget(self.menu_bar)

        self.label_2.setPixmap(
            QPixmap(os.path.join(scalable, "BitCapIPRCenterLogo.svg"))
        )
        self.tableWidget.setHorizontalHeaderLabels(
            ["IP", "MAC", "SERIAL", "TYPE", "SUBTYPE"]
        )
        self.children = []

        # MainWindow Signals
        logger.info("MainWindow : set action signals.")
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

        logger.info("MainWindow : read settings from config.")
        self.config_path = Path(Path.home(), ".config", "ipr").resolve()
        self.settings = Path(self.config_path, "instance.json")
        if os.path.exists(self.settings):
            with open(self.settings, "r") as f:
                config = json.load(f)
            self.actionAlwaysOpenIPInBrowser.setChecked(
                config["options"]["alwaysOpenIPInBrowser"]
            )
            self.actionDisableInactiveTimer.setChecked(
                config["options"]["disableInactiveTimer"]
            )
            self.actionDisableWarningDialog.setChecked(
                config["options"]["disableWarningDialog"]
            )
            self.actionAutoStartOnLaunch.setChecked(
                config["options"]["autoStartOnLaunch"]
            )
            self.actionEnableIDTable.setChecked(
                config["table"]["enableIDTable"]
            )

        logger.info("MainWindow : init ListenerManager thread.")
        self.thread = ListenerManager()
        self.thread.completed.connect(self.show_confirm)

        logger.info("MainWindow : init inactive timer for 900000ms.")
        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        self.update_stacked_widget()

        if self.actionAutoStartOnLaunch.isChecked():
            self.start_listen()

    def about(self):
        QMessageBox.information(
            self,
            "BitCapIPR",
            f"{app_info['name']} is a {app_info['desc']}\nVersion {app_info['version']}\n{app_info['author']}\nPowered by {app_info['company']}\n",
        )

    def open_issues(self):
        webbrowser.open(f"{app_info['source']}/issues", new=2)

    def open_source(self):
        webbrowser.open(f"{app_info['source']}", new=2)

    def start_listen(self):
        logger.info("MainWindow : start listeners.")
        self.actionIPRStart.setEnabled(False)
        self.actionIPRStop.setEnabled(True)
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        if (
            not self.actionDisableWarningDialog.isChecked()
            and not self.actionAutoStartOnLaunch.isChecked()
        ):
            QMessageBox.warning(
                self,
                "BitCapIPR",
                "UDP listening on 0.0.0.0[:8888,11503,14235]...\nPress the 'IP Report' button on miner after this dialog.",
            )
        self.thread.start()

    def stop_listen(self, timeout):
        logger.info("MainWindow : stop listeners.")
        if timeout:
            logger.warning("stop_listen : timeout.")
            QMessageBox.warning(
                self,
                "BitCapIPR",
                "Inactive Timeout exceeded! Stopping listeners...",
            )
            self.inactive.stop()
        if self.actionEnableIDTable.isChecked():
            self.tableWidget.setRowCount(0)
        self.thread.stop_listeners()
        self.actionIPRStart.setEnabled(True)
        self.actionIPRStop.setEnabled(False)

    def set_api_passwd(self):
        logger.info("MainWindow : set api password.")
        passwd = self.linePasswdField.text()
        if not passwd:
            # if passwd is blank, exit
            confirm = QMessageBox.question(
                self,
                "BitCapIPR",
                "No supplied password. Do you want to leave the config?",
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes,
                defaultButton=QMessageBox.StandardButton.Yes,
            )
            if confirm == QMessageBox.StandardButton.Yes:
                self.update_stacked_widget()
            return

        logger.info("set_api_passwd : write api password to config.")
        config = {"defaultAPIPasswd": passwd}
        config_json = json.dumps(config, indent=4)
        with open(Path(self.config_path, "config.json"), "w") as f:
            f.write(config_json)
        QMessageBox.information(
            self, "BitCapIPR", "Successfully wrote to config."
        )
        self.linePasswdField.clear()
        self.update_stacked_widget()

    def open_dashboard(self, ip):
        webbrowser.open("http://{0}".format(ip), new=2)

    def update_stacked_widget(self):
        if self.actionEnableIDTable.isChecked():
            logger.info("MainWindow : enable table view.")
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)

    def retrieve_iceriver_mac_addr(self, ip):
        with requests.Session() as s:
            host = f"http://{ip}"
            s.head(host)
            res = s.post(
                url=f"{host}/user/ipconfig",
                data={"post": 1},
                headers={"Referer": host},
            )
            r_data = res.json()["data"]
            if "mac" in r_data:
                return r_data["mac"]

    def get_table_data_from_ip(self, type, ip):
        result = {"serial": "N/A", "subtype": "N/A"}
        match type:
            case "antminer":
                uri = None
                endpoints = [
                    f"http://{ip}/api/v1/info",
                    f"http://{ip}/cgi-bin/get_system_info.cgi",
                ]
                with open(Path(self.config_path, "config.json"), "r") as f:
                    config = json.load(f)
                    passwd = config["defaultAPIPasswd"]

                for endp in range(0, (len(endpoints))):
                    r = requests.get(
                        endpoints[endp], auth=HTTPDigestAuth("root", passwd)
                    )
                    # second pass fail; abort
                    if r.status_code == 401:
                        # first pass failed
                        passwd = "root"
                        r = requests.head(
                            endpoints[endp], auth=HTTPDigestAuth("root", passwd)
                        )
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
                        if "serial" in r_json:
                            result["serial"] = r.json()["serial"]
                        if "miner" in r_json:
                            result["subtype"] = r.json()["miner"][9:]
                    case 1:
                        r = requests.get(
                            endpoints[uri], auth=HTTPDigestAuth("root", passwd)
                        )
                        r_json = r.json()
                        if "serinum" in r_json:
                            result["serial"] = r.json()["serinum"]
                        if "minertype" in r_json:
                            result["subtype"] = r.json()["minertype"][9:]
                    case None:
                        # failed to authenticate
                        result["serial"] = "Failed auth"
                        result["subtype"] = "Failed auth"
                return result
            case "iceriver":
                with requests.Session() as s:
                    host = f"http://{ip}"
                    s.head(host)
                    res = s.post(
                        url=f"{host}/user/userpanel",
                        data={"post": 4},
                        headers={"Referer": host},
                    )
                    r_data = res.json()["data"]
                    if "model" in r_data:
                        if r_data["model"] == "none":
                            if "softver1" in r_data:
                                model = "".join(r_data["softver1"].split("_")[-2:])
                                result["subtype"] = model[model.rfind("ks"):model.rfind("miner")].upper()
                        else:
                            result["subtype"] = r_data["model"]
                    return result
            case "whatsminer":
                json_cmd = {"cmd": "devdetails"}
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, 4028))
                    s.send(json.dumps(json_cmd).encode('utf-8'))
                    data = s.recv(4096)

                    try:
                        r_json = json.loads(data.decode())
                        if "Model" in r_json["DEVDETAILS"][0]:
                            result["subtype"] = r_json["DEVDETAILS"][0]["Model"]
                    except Exception:
                        pass
                return result

    def show_confirm(self):
        logger.info("MainWindow : show IPRConfirmation.")
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        ip, mac, type = self.thread.data.split(",")
        if mac == "ice-river":
            logger.info("show_confirm : get iceriver mac addr.")
            mac = self.retrieve_iceriver_mac_addr(ip)
        if self.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip)
            if self.actionEnableIDTable.isChecked():
                self.activateWindow()
        else:
            logger.info("show_confirm : init IPRConfirmation window.")
            confirm = IPRConfirmation()
            # IPRConfirmation Signals
            confirm.actionOpenBrowser.clicked.connect(
                lambda: self.open_dashboard(ip)
            )
            confirm.accept.clicked.connect(lambda: self.hide_confirm(confirm))
            # copy action
            confirm.lineIPField.actionCopy = confirm.lineIPField.addAction(
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon),
                QLineEdit.ActionPosition.TrailingPosition,
            )
            confirm.lineIPField.actionCopy.triggered.connect(
                lambda: self.copy_text(confirm.lineIPField)
            )
            confirm.lineMACField.actionCopy = confirm.lineMACField.addAction(
                self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon),
                QLineEdit.ActionPosition.TrailingPosition,
            )
            confirm.lineMACField.actionCopy.triggered.connect(
                lambda: self.copy_text(confirm.lineMACField)
            )
            confirm.lineIPField.setText(ip)
            confirm.lineMACField.setText(mac)
            logger.info("show_confirm : show IPRConfirmation window.")
            confirm.show()
            confirm.activateWindow()
            self.children.append(confirm)
        if self.actionEnableIDTable.isChecked():
            t_data = self.get_table_data_from_ip(type, ip)
            logger.info("show_confirm : write table data.")
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)
            self.tableWidget.setItem(rowPosition, 0, QTableWidgetItem(ip))
            self.tableWidget.setItem(rowPosition, 1, QTableWidgetItem(mac))
            self.tableWidget.setItem(
                rowPosition, 2, QTableWidgetItem(t_data["serial"])
            )
            # ASIC TYPE
            self.tableWidget.setItem(rowPosition, 3, QTableWidgetItem(type))
            # SUBTYPE
            self.tableWidget.setItem(
                rowPosition, 4, QTableWidgetItem(t_data["subtype"])
            )

    def show_api_config(self):
        self.stackedWidget.setCurrentIndex(2)

    def copy_selected(self):
        logger.info("MainWindow : copy selected elements.")
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        out = ""
        for i in range(rows):
            for j in range(cols):
                if self.tableWidget.item(i, j).isSelected():
                    out += self.tableWidget.item(i, j).text()
                    out += ","
            out += "\n"
        logger.info("copy_selected : copy elements to clipboard.")
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(out.strip(), mode=cb.Mode.Clipboard)

    def export_table(self):
        logger.info("MainWindow : export table.")
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        out = "IP, MAC, SERIAL, TYPE, SUBTYPE, \n"
        for i in range(rows):
            for j in range(cols):
                out += self.tableWidget.item(i, j).text()
                out += ","
            out += "\n"

        # .csv
        logger.info("export_table : write table to csv.")
        p = Path(Path.home(), "Documents", "ipr").resolve()
        Path.mkdir(p, exist_ok=True)
        file = QFile(
            os.path.join(
                p,
                f"id_table-{datetime.now().strftime('%Y-%m-%d')}-{time.time().__floor__()}.csv",
            )
        )
        if not file.open(
            QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Truncate
        ):
            return
        outfile = QTextStream(file)
        outfile << out << "\n"
        QMessageBox.information(
            self, "BitCapIPR", f"Successfully wrote csv to {p}."
        )

    def hide_confirm(self, confirm):
        confirm.close()

    def copy_text(self, lineEdit):
        lineEdit.selectAll()
        lineEdit.copy()

    def update_settings(self):
        logger.info("MainWindow : write settings to config.")
        instance = {
            "options": {
                "alwaysOpenIPInBrowser": self.actionAlwaysOpenIPInBrowser.isChecked(),
                "disableInactiveTimer": self.actionDisableInactiveTimer.isChecked(),
                "disableWarningDialog": self.actionDisableWarningDialog.isChecked(),
                "autoStartOnLaunch": self.actionAutoStartOnLaunch.isChecked(),
            },
            "table": {"enableIDTable": self.actionEnableIDTable.isChecked()},
        }
        self.instance_json = json.dumps(instance, indent=4)
        with open(self.settings, "w") as f:
            f.write(self.instance_json)

    def killall(self):
        logger.info("MainWindow : kill all confirms.")
        for c in self.children:
            c.close()

    def quit(self):
        self.thread.stop_listeners()
        self.thread.exit()
        self.killall()
        logger.info("MainWindow : exit app.")
        self.close()
        self = None


def exception_hook(exc_type, exc_value, exc_tb):
    QMessageBox.critical(
        None,
        "BitCap IPR - Critical Error",
        "Application has encounter an error!\nSee output log."
    )
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical("exception_hook : exception caught!")
    logger.critical(f"exception_hook : {tb}")
    QApplication.quit()


def launch_app():
    # paths
    config_path = Path(Path.home(), ".config", "ipr").resolve()
    log_path = Path(config_path, "logs").resolve()
    os.makedirs(log_path, exist_ok=True)

    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S%p', filename=f"{Path(log_path, 'ipr.log')}", level=logging.INFO)
    logger.info("launch_app : start init.")

    app = QApplication(sys.argv)
    with open(os.path.join(basedir, 'ui/theme.qss')) as theme:
        app.setStyleSheet(theme.read())
    # first-time launch
    logger.info("launch_app : check for existing config.")
    if not os.path.exists(Path(config_path, "config.json")):
        # no config so write them on first-time launch
        logger.info("launch_app : first time launch; write default config.")
        default_instance = {
            "options": {
                "alwaysOpenIPInBrowser": False,
                "disableInactiveTimer": False,
                "disableWarningDialog": False,
                "autoStartOnLaunch": False,
            },
            "table": {"enableIDTable": False},
        }
        default_instance_json = json.dumps(default_instance, indent=4)
        with open(Path(config_path, "instance.json"), "w") as f:
            f.write(default_instance_json)

        default_config = {"defaultAPIPasswd": ""}
        default_config_json = json.dumps(default_config, indent=4)
        with open(Path(config_path, "config.json"), "w") as f:
            f.write(default_config_json)

    # Here we are making sure that only one instance is running at a time
    window_key = "BitCapIPR"
    shared_mem_key = "IPRSharedMemory"
    semaphore = QSystemSemaphore(window_key, 1)
    semaphore.acquire()

    if sys.platform != "win32":
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
        QMessageBox.warning(
            None,
            "BitCapIPR - Application already running",
            "One instance of the application is already running.",
        )
        return

    app.setWindowIcon(
        QIcon(
            os.path.join(icons, "BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png")
        )
    )
    app.setStyle("Fusion")

    logger.info("launch_app : finish app init.")
    logger.info("launch_app : start MainWindow() init.")
    w = MainWindow()
    w.show()
    sys.excepthook = exception_hook
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
