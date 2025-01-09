import os
import time
import json
import logging
import webbrowser
from datetime import datetime
from pathlib import Path
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
    QMenuBar,
    QMenu,
)
from PyQt6.QtGui import QPixmap, QIcon
from ui.widgets.TitleBar import TitleBar
from ui.GUI import Ui_MainWindow
import ui.resources

from ListenerManager import ListenerManager
from IPRConfirmation import IPRConfirmation
from IPRAbout import IPRAbout
from mod.api import (
    retrieve_iceriver_mac_addr,
    retrieve_antminer_data,
    retrieve_iceriver_data,
    retrieve_whatsminer_data,
)
from util import (
    CURR_PLATFORM,
    APP_INFO,
    MAX_LOG_SIZE_LIMIT,
    get_config_path,
    get_config,
)

# logger
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        logger.info(" start MainWindow() init.")
        super().__init__(flags=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)

        # title bar
        if CURR_PLATFORM == "darwin":
            self.title_bar = TitleBar(self, "BitCap IPReporter", ['close', 'min'], style="mac")
        else:
            self.title_bar = TitleBar(self, "BitCap IPReporter", ['min', 'close'])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.close_to_tray_or_exit)
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
        self.menuSettings = self.menu_bar.addMenu("Settings")
        self.menuSettings.setToolTipsVisible(True)
        self.menuQuit = self.menu_bar.addMenu("Quit")
        self.menuQuit.setToolTipsVisible(True)

        # help
        self.actionAbout = self.menuHelp.addAction("About")
        self.actionAbout.setToolTip("Opens the about dialog")
        self.actionReportIssue = self.menuHelp.addAction("Report Issue")
        self.actionReportIssue.setToolTip("Report a new issue on GitHub")
        self.actionSourceCode = self.menuHelp.addAction("Source Code")
        self.actionSourceCode.setToolTip("Opens the GitHub repo in browser")
        self.actionVersion = self.menuHelp.addAction(f"Version {APP_INFO['version']}")
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

        # settings
        self.actionSettings = self.menuSettings.addAction("Settings...")
        self.actionSettings.setToolTip("Change application settings")

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
        self.actionTogglePasswd = self.linePasswdField.addAction(
            QIcon(":theme/icons/rc/view.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.actionTogglePasswd.setToolTip("Show/Hide password")
        self.actionTogglePasswd.triggered.connect(self.toggle_passwd)

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
        self.actionIPRSaveConfig.clicked.connect(self.save_settings)
        # listener signals
        self.actionIPRStart.clicked.connect(self.start_listen)
        self.actionIPRStop.clicked.connect(self.stop_listen)

        logger.info(" read config.")
        self.config_path = get_config_path()
        if os.path.exists(self.config_path):
            self.config = get_config(Path(self.config_path, "config.json"))
            # general
            self.checkEnableSysTray.setChecked(
                self.config["general"]["enableSysTray"]
            )
            self.comboOnWindowClose.setCurrentIndex(
                self.config["general"]["onWindowClose"]
            )
            # api
            self.linePasswdField.setText(self.config["api"]["defaultAPIPasswd"])

            # logs
            self.comboLogLevel.setCurrentText(
                self.config["logs"]["logLevel"]
            )
            self.lineMaxLogSize.setText(self.config["logs"]["maxLogSize"])
            self.comboOnMaxLogSize.setCurrentIndex(
                self.config["logs"]["onMaxLogSize"]
            )
            self.comboFlushInterval.setCurrentIndex(
                self.config["logs"]["flushInterval"]
            )

            # instance
            self.actionAlwaysOpenIPInBrowser.setChecked(
                self.config["instance"]["options"]["alwaysOpenIPInBrowser"]
            )
            self.actionDisableInactiveTimer.setChecked(
                self.config["instance"]["options"]["disableInactiveTimer"]
            )
            self.actionDisableWarningDialog.setChecked(
                self.config["instance"]["options"]["disableWarningDialog"]
            )
            self.actionAutoStartOnLaunch.setChecked(
                self.config["instance"]["options"]["autoStartOnLaunch"]
            )
            self.actionEnableIDTable.setChecked(
                self.config["instance"]["table"]["enableIDTable"]
            )
            self.actionDisableIPConfirmations.setChecked(
                self.config["instance"]["table"]["disableIPConfirmations"]
            )

        if self.actionEnableIDTable.isChecked():
            self.actionDisableIPConfirmations.setEnabled(True)

        logger.info(" init systray.")
        self.sys_tray = None
        self.create_or_destroy_systray()

        logger.info(" init ListenerManager thread.")
        self.thread = ListenerManager()
        self.thread.completed.connect(self.show_confirm)
        # restart listeners on fail
        self.thread.failed.connect(self.restart_listen)

        logger.info(" init inactive timer for 900000ms.")
        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        self.actionDisableInactiveTimer.changed.connect(self.restart_listen)
        self.actionEnableIDTable.changed.connect(self.toggle_table_settings)
        self.checkEnableSysTray.stateChanged.connect(self.create_or_destroy_systray)

        self.update_stacked_widget()

        if self.actionAutoStartOnLaunch.isChecked():
            self.start_listen()

    def create_or_destroy_systray(self):
        if self.checkEnableSysTray.isChecked():
            self.sys_tray = QSystemTrayIcon(QIcon(":rc/img/BitCapIPR_BLK-02_Square.png"), self)
            self.system_tray_menu = QMenu()
            self.system_tray_menu.addAction("Show/Hide", self.toggle_visibility)
            self.actionSysStartListen = self.system_tray_menu.addAction("Start Listen", self.start_listen)
            self.actionSysStopListen = self.system_tray_menu.addAction("Stop Listen", self.stop_listen)
            self.actionSysStopListen.setEnabled(False)
            self.system_tray_menu.addSeparator()
            self.system_tray_menu.addAction("Quit", self.quit)
            self.sys_tray.setContextMenu(self.system_tray_menu)
            if self.comboOnWindowClose.currentIndex() == 0:
                self.sys_tray.show()
        else:
            if self.sys_tray:
                self.sys_tray.hide()
            self.sys_tray = None

    def update_stacked_widget(self):
        logger.info(" update view.")
        if self.actionEnableIDTable.isChecked():
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)

    def about(self):
        self.aboutDialog = IPRAbout(
            self,
            "About",
            f"{APP_INFO['name']} is a {APP_INFO['desc']}\nVersion {APP_INFO['version']}\n{APP_INFO['author']}\nPowered by {APP_INFO['company']}\n"
        )
        self.aboutDialog._acceptButton.clicked.connect(self.aboutDialog.window().close)
        self.aboutDialog.show()

    def open_issues(self):
        webbrowser.open(f"{APP_INFO['source']}/issues", new=2)

    def open_source(self):
        webbrowser.open(f"{APP_INFO['source']}", new=2)

    def open_dashboard(self, ip):
        webbrowser.open("http://{0}".format(ip), new=2)

    def start_listen(self):
        logger.info(" start listeners.")
        self.actionIPRStart.setEnabled(False)
        self.actionIPRStop.setEnabled(True)
        if self.sys_tray:
            self.actionSysStartListen.setEnabled(False)
            self.actionSysStopListen.setEnabled(True)
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
        if not self.isVisible():
            self.sys_tray.showMessage(
                "IPR Listener: Start",
                "Started Listening on 0.0.0.0[:8888,:11503,:14235]...",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.thread.start()

    def stop_listen(self, timeout=False):
        logger.info(" stop listeners.")
        if timeout:
            logger.warning("stop_listen : timeout.")
            if not self.isVisible():
                self.sys_tray.showMessage(
                    "Inactive timeout",
                    "Timeout exceeded. Stopping listeners...",
                    QSystemTrayIcon.MessageIcon.Warning,
                    3000,
                )
            else:
                QMessageBox.warning(
                    self,
                    "Timeout",
                    "Inactive Timeout exceeded! Stopping listeners...",
                )
            self.inactive.stop()
        if self.actionEnableIDTable.isChecked():
            self.tableWidget.setRowCount(0)
        if not self.isVisible():
            self.sys_tray.showMessage(
                "IPR Listener: Stop",
                "Stopping listeners...",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.thread.stop_listeners()
        self.actionIPRStart.setEnabled(True)
        self.actionIPRStop.setEnabled(False)
        if self.sys_tray:
            self.actionSysStartListen.setEnabled(True)
            self.actionSysStopListen.setEnabled(False)

    def restart_listen(self):
        if self.thread.listeners:
            logger.info(" restart listeners.")
            self.stop_listen()
            self.start_listen()

    # confirm
    def show_confirm(self):
        logger.info(" show IP confirmation.")
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        ip, mac, type = self.thread.data.split(",")
        logger.info(f"show_confirm : got {ip},{mac},{type} from listener thread.")
        if mac == "ice-river":
            mac = retrieve_iceriver_mac_addr(ip)
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
            confirm.accept.clicked.connect(confirm.hide)
            # copy action
            confirm.lineIPField.actionCopy = confirm.lineIPField.addAction(
                QIcon(":theme/icons/rc/copy.png"),
                QLineEdit.ActionPosition.TrailingPosition,
            )
            confirm.lineIPField.actionCopy.triggered.connect(
                lambda: self.copy_text(confirm.lineIPField)
            )
            confirm.lineMACField.actionCopy = confirm.lineMACField.addAction(
                QIcon(":theme/icons/rc/copy.png"),
                QLineEdit.ActionPosition.TrailingPosition,
            )
            confirm.lineMACField.actionCopy.triggered.connect(
                lambda: self.copy_text(confirm.lineMACField)
            )
            logger.info("show_confirm : show IPRConfirmation.")
            confirm.lineIPField.setText(ip)
            confirm.lineMACField.setText(mac)
            self.children.append(confirm)
            if not self.isVisible():
                self.sys_tray.messageClicked.connect(lambda: self.show_confirm_from_sys_tray(confirm))
                if CURR_PLATFORM == "linux":
                    self.sys_tray.showMessage(
                        "Received confirmation",
                        "Click to show.",
                        QSystemTrayIcon.MessageIcon.Critical,
                        15000,
                    )
                else:
                    self.sys_tray.showMessage(
                        "Received confirmation",
                        "Click to show.",
                        QSystemTrayIcon.MessageIcon.Information,
                        15000,
                    )
            else:
                confirm.show()
                confirm.activateWindow()
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

    def show_confirm_from_sys_tray(self, confirm):
        confirm.show()
        confirm.activateWindow()
        self.sys_tray.messageClicked.disconnect()

    def copy_text(self, lineEdit):
        lineEdit.selectAll()
        lineEdit.copy()

    # id table view
    def get_table_data_from_ip(self, type, ip):
        result = {"serial": "N/A", "subtype": "N/A"}
        logger.info(f" get table data from ip {ip}.")
        match type:
            case "antminer":
                logger.debug("get_table_data_from_ip : type is antminer; get data from endpoint.")
                endpoints = [
                    f"http://{ip}/api/v1/info",
                    f"http://{ip}/cgi-bin/get_system_info.cgi",
                ]
                passwd = self.linePasswdField.text()
                return retrieve_antminer_data(endpoints, passwd, result)

            case "iceriver":
                logger.debug("get_table_data_from_ip : type is iceriver; start session.")
                return retrieve_iceriver_data(ip, result)
            case "whatsminer":
                logger.debug("get_table_data_from_ip : type is whatsminer; send json command.")
                return retrieve_whatsminer_data(ip, {"cmd": "devdetails"}, result)

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
            self, "Export Table Data", f"Successfully wrote csv to {p}."
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

    def toggle_passwd(self):
        if self.linePasswdField.echoMode() == QLineEdit.EchoMode.Password:
            self.linePasswdField.setEchoMode(QLineEdit.EchoMode.Normal)
            self.actionTogglePasswd.setIcon(QIcon(":theme/icons/rc/hide.png"))
        elif self.linePasswdField.echoMode() == QLineEdit.EchoMode.Normal:
            self.linePasswdField.setEchoMode(QLineEdit.EchoMode.Password)
            self.actionTogglePasswd.setIcon(QIcon(":theme/icons/rc/view.png"))

    def save_settings(self):
        self.update_settings()
        QMessageBox.information(
            self,
            "Configuration",
            "Successfully wrote settings to config."
        )

    def update_settings(self):
        logger.info(" write settings to config.")
        if int(self.lineMaxLogSize.text()) > MAX_LOG_SIZE_LIMIT:
            self.lineMaxLogSize.setText(f"{MAX_LOG_SIZE_LIMIT}")
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
                "onWindowClose": self.comboOnWindowClose.currentIndex()
            },
            "api": {"defaultAPIPasswd": self.linePasswdField.text()},
            "logs": {
                "logLevel": self.comboLogLevel.currentText(),
                "maxLogSize": self.lineMaxLogSize.text(),
                "onMaxLogSize": self.comboOnMaxLogSize.currentIndex(),
                "flushInterval": self.comboFlushInterval.currentIndex()
            },
            "instance": instance,
        }
        self.config_json = json.dumps(config, indent=4)
        with open(Path(self.config_path, "config.json"), "w") as f:
            f.write(self.config_json)
        self.update_stacked_widget()

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def close_to_tray_or_exit(self):
        if self.comboOnWindowClose.currentIndex() == 1:
            self.toggle_visibility()
            self.sys_tray.show()
            self.sys_tray.showMessage(
                "Minimized to tray",
                "BitCapIPR is now running in the background.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        else:
            self.quit()

    def killall(self):
        logger.info(" kill all confirmations.")
        for c in self.children:
            c.close()

    def close_root_logger(self, log):
        for handler in log.root.handlers:
            handler.close()
            log.root.removeHandler(handler)

    def quit(self):
        if not self.isVisible():
            self.toggle_visibility()
        self.thread.stop_listeners()
        self.thread.exit()
        self.killall()
        logger.info(" exit app.")
        # flush log on close if set
        if self.comboOnMaxLogSize.currentIndex() == 0 and self.comboFlushInterval.currentIndex() == 1:
            logger.root.handlers[0].doRollover()
        self.close_root_logger(logger)
        self.close()
        self = None
