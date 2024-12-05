import os
import socket
import time
import json
import logging
import webbrowser
from datetime import datetime
from pathlib import Path
import requests
from requests.auth import HTTPDigestAuth
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QFile,
    QIODevice,
    QTextStream,
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSystemTrayIcon,
    QMessageBox,
    QTableWidgetItem,
    QLineEdit,
    QStyle,
    QMenuBar,
    QMenu,
)
from PyQt6.QtGui import QPixmap
from ui.widgets.TitleBar import TitleBar
from ui.GUI import Ui_MainWindow
import ui.resources

from ListenerManager import ListenerManager
from IPRConfirmation import IPRConfirmation
from util import curr_platform, app_info

# logger
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, sys_tray : QSystemTrayIcon | None):
        self.sys_tray = sys_tray
        if self.sys_tray:
            self.system_tray_menu = QMenu()
            self.system_tray_menu.addAction("Show/Hide", self.toggle_visibility)
            self.sys_tray.setContextMenu(self.system_tray_menu)

        logger.info(" start MainWindow() init.")
        super().__init__(flags=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)

        # title bar
        if curr_platform == "darwin":
            self.title_bar = TitleBar(self, "BitCap IPReporter", ['close', 'min'], style="mac")
        else:
            self.title_bar = TitleBar(self, "BitCap IPReporter", ['min', 'close'])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.close_to_tray)
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
        self.actionSettings = self.menu_bar.addAction("Settings...")
        self.actionSettings.setToolTip("Change app settings")
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
        self.actionDisableIPConfirmations = self.menuTableSettings.addAction("Disable IP Confirmations")
        self.actionDisableIPConfirmations.setEnabled(False)
        self.actionDisableIPConfirmations.setCheckable(True)
        self.actionDisableIPConfirmations.setToolTip("Disables IP Confirmation windows when in table view.")
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
            QPixmap(":rc/img/scalable/BitCapIPRCenterLogo.svg")
        )
        self.tableWidget.setHorizontalHeaderLabels(
            ["IP", "MAC", "SERIAL", "TYPE", "SUBTYPE"]
        )
        self.children = []

        # menu_bar signals
        self.actionAbout.triggered.connect(self.about)
        self.actionReportIssue.triggered.connect(self.open_issues)
        self.actionSourceCode.triggered.connect(self.open_source)
        self.actionKillAllConfirmations.triggered.connect(self.killall)
        self.actionQuit.triggered.connect(self.quit)
        self.menuOptions.triggered.connect(self.update_settings)
        self.menuTable.triggered.connect(self.update_settings)
        self.actionEnableIDTable.triggered.connect(self.update_stacked_widget)
        self.actionCopySelectedElements.triggered.connect(self.copy_selected)
        self.actionExport.triggered.connect(self.export_table)
        self.actionSettings.triggered.connect(self.show_app_config)
        # app config signals
        self.checkEnableSysTray.toggled.connect(self.toggle_app_config)
        self.actionIPRCancelConfig.clicked.connect(self.update_stacked_widget)
        self.actionIPRSaveConfig.clicked.connect(self.update_settings)
        # listener signals
        self.actionIPRStart.clicked.connect(self.start_listen)
        self.actionIPRStop.clicked.connect(self.stop_listen)

        logger.info(" read config.")
        self.config_path = Path(Path.home(), ".config", "ipr").resolve()
        self.config = Path(self.config_path, "config.json")
        if os.path.exists(self.config):
            with open(self.config, "r") as f:
                config = json.load(f)
            self.checkEnableSysTray.setChecked(
                config["general"]["enableSysTray"]
            )
            self.onWindowCloseIndex = {
                "close": 0,
                "minimizeToTray": 1
            }
            self.comboOnWindowClose.setCurrentIndex(self.onWindowCloseIndex[config["general"]["onWindowClose"]])
            self.linePasswdField.setText(config["api"]["defaultAPIPasswd"])

            self.actionAlwaysOpenIPInBrowser.setChecked(
                config["instance"]["options"]["alwaysOpenIPInBrowser"]
            )
            self.actionDisableInactiveTimer.setChecked(
                config["instance"]["options"]["disableInactiveTimer"]
            )
            self.actionDisableWarningDialog.setChecked(
                config["instance"]["options"]["disableWarningDialog"]
            )
            self.actionAutoStartOnLaunch.setChecked(
                config["instance"]["options"]["autoStartOnLaunch"]
            )
            self.actionEnableIDTable.setChecked(
                config["instance"]["table"]["enableIDTable"]
            )
            self.actionDisableIPConfirmations.setChecked(
                config["instance"]["table"]["disableIPConfirmations"]
            )

        logger.info(" init ListenerManager thread.")
        self.thread = ListenerManager()
        self.thread.completed.connect(self.show_confirm)

        logger.info(" init inactive timer for 900000ms.")
        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        self.actionDisableInactiveTimer.changed.connect(self.restart_listen)
        self.actionEnableIDTable.changed.connect(self.toggle_table_settings)

        self.update_stacked_widget()

        if self.actionAutoStartOnLaunch.isChecked():
            self.start_listen()

    def update_stacked_widget(self):
        if self.actionEnableIDTable.isChecked():
            logger.info(" show table view.")
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)

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

    def open_dashboard(self, ip):
        webbrowser.open("http://{0}".format(ip), new=2)

    def start_listen(self):
        logger.info(" start listeners.")
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

    def stop_listen(self, timeout=False):
        logger.info(" stop listeners.")
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

    def restart_listen(self):
        if self.thread.listeners:
            logger.info(" restart listeners.")
            self.stop_listen()
            self.start_listen()

    # confirm
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

    def show_confirm(self):
        logger.info(" show IP confirmation.")
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        ip, mac, type = self.thread.data.split(",")
        logger.info(f"show_confirm : got {ip},{mac},{type} from listener thread.")
        if mac == "ice-river":
            mac = self.retrieve_iceriver_mac_addr(ip)
            logger.info(f"show_confirm : got iceriver mac addr : {mac}")
        if self.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip)
            if self.actionEnableIDTable.isChecked():
                self.activateWindow()
        elif self.actionDisableIPConfirmations.isChecked():
            self.activateWindow()
        else:
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
            logger.info("show_confirm : show IPRConfirmation.")
            confirm.lineIPField.setText(ip)
            confirm.lineMACField.setText(mac)
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

    def hide_confirm(self, confirm):
        confirm.close()

    def copy_text(self, lineEdit):
        lineEdit.selectAll()
        lineEdit.copy()

    # id table view
    def get_table_data_from_ip(self, type, ip):
        result = {"serial": "N/A", "subtype": "N/A"}
        logger.info(f" get table data from ip {ip}.")
        match type:
            case "antminer":
                logger.info("get_table_data_from_ip : get api from endpoint.")
                uri = None
                endpoints = [
                    f"http://{ip}/api/v1/info",
                    f"http://{ip}/cgi-bin/get_system_info.cgi",
                ]
                with open(Path(self.config_path, "config.json"), "r") as f:
                    config = json.load(f)
                    passwd = config["defaultAPIPasswd"]

                for endp in range(0, (len(endpoints))):
                    logger.info(f"get_table_data_from_ip : authenticate endp {endp}.")
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
                            logger.warning("get_table_data_from_ip : authentication fail. abort!")
                            endp = None
                            break
                    if r.status_code == 200:
                        logger.info("get_table_data_from_ip : authentication success.")
                        uri = endp
                        break
                logger.info("get_table_data_from_ip : parse json data.")
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
                logger.info("get_table_data_from_ip : type is iceriver; start session.")
                with requests.Session() as s:
                    host = f"http://{ip}"
                    s.head(host)
                    res = s.post(
                        url=f"{host}/user/userpanel",
                        data={"post": 4},
                        headers={"Referer": host},
                    )
                    logger.info("get_table_data_from_ip : parse json data.")
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
                logger.info(f"get_table_data_from_ip : type is whatsminer; send json command.")
                json_cmd = {"cmd": "devdetails"}
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, 4028))
                    s.send(json.dumps(json_cmd).encode("utf-8"))
                    data = s.recv(4096)
                    logger.info("get_table_data_from_ip : parse json data.")
                    try:
                        r_json = json.loads(data.decode())
                        if "Model" in r_json["DEVDETAILS"][0]:
                            result["subtype"] = r_json["DEVDETAILS"][0]["Model"]
                    except Exception:
                        pass
                return result

    def toggle_table_settings(self):
        if self.actionEnableIDTable.isChecked():
            self.actionDisableIPConfirmations.setEnabled(True)
        else:
            self.actionDisableIPConfirmations.setChecked(False)
            self.update_settings()
            self.actionDisableIPConfirmations.setEnabled(False)

    def copy_selected(self):
        logger.info(" copy selected elements.")
        rows = self.tableWidget.rowCount()
        cols = self.tableWidget.columnCount()
        out = ""
        if len(self.tableWidget.selectedItems()) == 1:
            out += self.tableWidget.selectedItems()[0].text()
            out += "\n"
        else:
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
        logger.info("export table.")
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

    # app config view
    def show_app_config(self):
        self.stackedWidget.setCurrentIndex(2)

    def toggle_app_config(self):
        if self.checkEnableSysTray.isChecked():
            self.comboOnWindowClose.setEnabled(True)
        else:
            self.comboOnWindowClose.setCurrentIndex(0)
            self.comboOnWindowClose.setEnabled(False)

    def update_config(self):
        config = {
            "config": {
                "enableSysTray": self.checkEnableSysTray.isChecked(),
                "onWindowClose": [x for x,y in self.onWindowCloseIndex.items() if y == self.comboOnWindowClose.currentIndex()][0],
                "api": {
                    "defaultAPIPasswd": ""
                }
            }
        }
        self.config_json = json.dumps(config, indent=4)
        with open(self.config, "w") as f:
            f.write(self.config_json)

    def update_settings(self):
        logger.info(" write settings to config.")
        instance = {
            "options": {
                "alwaysOpenIPInBrowser": self.actionAlwaysOpenIPInBrowser.isChecked(),
                "disableInactiveTimer": self.actionDisableInactiveTimer.isChecked(),
                "disableWarningDialog": self.actionDisableWarningDialog.isChecked(),
                "autoStartOnLaunch": self.actionAutoStartOnLaunch.isChecked(),
            },
            "table": {
                "enableIDTable": self.actionEnableIDTable.isChecked(),
                "disableIPConfirmations": self.actionDisableIPConfirmations.isChecked(),
            },
        }
        config = {
            "general": {
                "enableSysTray": self.checkEnableSysTray.isChecked(),
                "onWindowClose": [x for x,y in self.onWindowCloseIndex.items() if y == self.comboOnWindowClose.currentIndex()][0]
            },
            "api": {
                "defaultAPIPasswd": self.linePasswdField.text()
            },
            "instance": instance
        }
        self.config_json = json.dumps(config, indent=4)
        with open(self.config, "w") as f:
            f.write(self.config_json)
        self.update_stacked_widget()

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def close_to_tray(self):
        self.toggle_visibility()
        self.sys_tray.show()
        self.sys_tray.showMessage("BitCapIPR", "BitCapIPR is now running in the background.", QSystemTrayIcon.MessageIcon.Information, 2000)

    def killall(self):
        logger.info(" kill all confirmations.")
        for c in self.children:
            c.close()

    def quit(self):
        self.thread.stop_listeners()
        self.thread.exit()
        self.killall()
        logger.info(" exit app.")
        self.close()
        self = None
