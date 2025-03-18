import os
import time
import json
import logging
import webbrowser
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import (
    Qt,
    QTimer,
    QFile,
    QIODevice,
    QTextStream,
    QUrl,
    QMetaMethod,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSystemTrayIcon,
    QMessageBox,
    QTableWidgetItem,
    QLabel,
    QLineEdit,
    QMenuBar,
    QMenu,
)
from PySide6.QtGui import (
    QPixmap,
    QIcon,
    QCursor,
    QDesktopServices,
)
import ui.resources  # noqa F401
from ui.MainWindow import Ui_MainWindow
from ui.widgets.titlebar import TitleBar
from iprconfirmation import IPRConfirmation
from iprabout import IPRAbout

from mod.listenermanager import ListenerManager
from mod.api.client import APIClient
from utils import (
    CURR_PLATFORM,
    APP_INFO,
    get_log_path,
    get_config_path,
    get_config,
)

# logger
logger = logging.getLogger(__name__)


class IPR(QMainWindow, Ui_MainWindow):
    def __init__(self):
        logger.info(" start IPR() init.")
        super().__init__(flags=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)

        # title bar
        if CURR_PLATFORM == "darwin":
            self.title_bar = TitleBar(
                self, "BitCap IPReporter", ["close", "min"], style="mac"
            )
        else:
            self.title_bar = TitleBar(self, "BitCap IPReporter", ["min", "close"])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.close_to_tray_or_exit)
        title_bar_widget = self.titlebar.layout()
        title_bar_widget.addWidget(self.title_bar)

        # menu bar
        self.menu_bar = QMenuBar()
        self.menuHelp = self.menu_bar.addMenu("Help")
        self.menuHelp.setToolTipsVisible(True)
        self.menuOptions = self.menu_bar.addMenu("Options")
        self.menuOptions.setToolTipsVisible(True)
        self.menuTable = self.menu_bar.addMenu("ID Table")
        self.menuTable.setToolTipsVisible(True)
        self.menuSettings = self.menu_bar.addMenu("Settings")
        self.menuSettings.setToolTipsVisible(True)
        self.menuQuit = self.menu_bar.addMenu("Quit")
        self.menuQuit.setToolTipsVisible(True)

        # help
        self.actionAbout = self.menuHelp.addAction("About")
        self.actionAbout.setToolTip("Opens the about dialog")
        self.actionOpenLog = self.menuHelp.addAction("Open Log")
        self.actionOpenLog.setToolTip("Opens log file")
        self.actionReportIssue = self.menuHelp.addAction("Report Issue")
        self.actionReportIssue.setToolTip("Report a new issue on GitHub")
        self.actionSourceCode = self.menuHelp.addAction("Source Code")
        self.actionSourceCode.setToolTip("Opens the GitHub repo in browser")
        self.actionVersion = self.menuHelp.addAction(
            f"Version {APP_INFO['appversion']}"
        )
        self.actionVersion.setEnabled(False)

        # options
        self.actionAlwaysOpenIPInBrowser = self.menuOptions.addAction(
            "Always Open IP in Browser"
        )
        self.actionAlwaysOpenIPInBrowser.setCheckable(True)
        self.actionAlwaysOpenIPInBrowser.setToolTip(
            "Always opens IPs in browser (No IP confirmation)"
        )
        self.actionDisableInactiveTimer = self.menuOptions.addAction(
            "Disable Inactive Timer"
        )
        self.actionDisableInactiveTimer.setCheckable(True)
        self.actionDisableInactiveTimer.setToolTip(
            "Disables inactive timer of 15 minutes (Listens until stopped)"
        )
        self.actionAutoStartOnLaunch = self.menuOptions.addAction(
            "Auto Start on Launch"
        )
        self.actionAutoStartOnLaunch.setCheckable(True)
        self.actionAutoStartOnLaunch.setToolTip(
            "Automatically start listeners on launch (Takes effect on next launch)"
        )

        # table
        self.actionEnableIDTable = self.menuTable.addAction("Enable ID Table")
        self.actionEnableIDTable.setCheckable(True)
        self.actionEnableIDTable.setToolTip(
            "Stores identifying information in a table on confirmation"
        )
        self.actionOpenSelectedIPs = self.menuTable.addAction("Open Selected IPs")
        self.actionOpenSelectedIPs.setEnabled(False)
        self.actionOpenSelectedIPs.setToolTip("Open selected IPs in browser")
        self.actionCopySelectedElements = self.menuTable.addAction(
            "Copy Selected Elements"
        )
        self.actionCopySelectedElements.setEnabled(False)
        self.actionCopySelectedElements.setToolTip(
            "Copy selected elements to clipboard. Drag or Ctrl-click to select multiple cols/rows"
        )
        self.actionExport = self.menuTable.addAction("Export")
        self.actionExport.setEnabled(False)
        self.actionExport.setToolTip("Export current table as .CSV file")

        # settings
        self.actionSettings = self.menuSettings.addAction("Settings...")
        self.actionSettings.setToolTip("Change application settings")

        # quit
        self.actionKillAllConfirmations = self.menuQuit.addAction(
            "Kill All Confirmations"
        )
        self.actionKillAllConfirmations.setToolTip("Kills all IP confirmation windows")
        self.actionQuit = self.menuQuit.addAction("Quit")
        self.actionQuit.setToolTip("Quits app")

        menubarwidget = self.menubar.layout()
        menubarwidget.addWidget(self.menu_bar)

        self.labelLogo.setPixmap(QPixmap(":rc/img/scalable/BitCapIPRCenterLogo.svg"))

        self.idTable.setHorizontalHeaderLabels(
            [
                "",
                "IP",
                "MAC",
                "SERIAL",
                "TYPE",
                "SUBTYPE",
                "ALGORITHM",
                "FIRMWARE",
                "PLATFORM",
            ]
        )
        self.idTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.idTable.customContextMenuRequested.connect(self.show_table_context)
        self.idTable.setColumnWidth(0, 15)
        self.idTable.doubleClicked.connect(self.double_click_item)
        self.idTable.cellClicked.connect(self.locate_miner)

        self.actionToggleBitmainPasswd = self.lineBitmainPasswd.addAction(
            QIcon(":theme/icons/rc/view.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.actionToggleBitmainPasswd.setToolTip("Show/Hide password")
        self.actionToggleBitmainPasswd.triggered.connect(
            lambda: self.toggle_show_passwd(
                self.lineBitmainPasswd, self.actionToggleBitmainPasswd
            )
        )

        self.actionToggleWhatsminerPasswd = self.lineWhatsminerPasswd.addAction(
            QIcon(":theme/icons/rc/view.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.actionToggleWhatsminerPasswd.setToolTip("Show/Hide password")
        self.actionToggleWhatsminerPasswd.triggered.connect(
            lambda: self.toggle_show_passwd(
                self.lineWhatsminerPasswd, self.actionToggleWhatsminerPasswd
            )
        )

        self.actionToggleVolcminerPasswd = self.lineVolcminerPasswd.addAction(
            QIcon(":theme/icons/rc/view.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.actionToggleVolcminerPasswd.setToolTip("Show/Hide password")
        self.actionToggleVolcminerPasswd.triggered.connect(
            lambda: self.toggle_show_passwd(
                self.lineVolcminerPasswd, self.actionToggleVolcminerPasswd
            )
        )

        self.actionTogglePbfarmerKey = self.linePbfarmerKey.addAction(
            QIcon(":theme/icons/rc/view.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        self.actionTogglePbfarmerKey.setToolTip("Show/Hide password")
        self.actionTogglePbfarmerKey.triggered.connect(
            lambda: self.toggle_show_passwd(
                self.linePbfarmerKey, self.actionTogglePbfarmerKey
            )
        )

        self.confirms = []

        # menu_bar signals
        self.actionAbout.triggered.connect(self.about)
        self.actionOpenLog.triggered.connect(self.open_log)
        self.actionReportIssue.triggered.connect(self.open_issues)
        self.actionSourceCode.triggered.connect(self.open_source)
        self.actionKillAllConfirmations.triggered.connect(self.killall)
        self.actionQuit.triggered.connect(self.quit)
        self.menuOptions.triggered.connect(self.update_settings)
        self.menuTable.triggered.connect(self.update_settings)
        self.actionEnableIDTable.triggered.connect(self.update_stacked_widget)
        self.actionOpenSelectedIPs.triggered.connect(self.open_selected_ips)
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
            self.checkEnableSysTray.setChecked(self.config["general"]["enableSysTray"])
            self.comboOnWindowClose.setCurrentIndex(
                self.config["general"]["onWindowClose"]
            )
            # listeners
            self.checkListenAntminer.setChecked(
                self.config["general"]["listenFor"]["antminer"]
            )
            self.checkListenWhatsminer.setChecked(
                self.config["general"]["listenFor"]["whatsminer"]
            )
            self.checkListenIceRiver.setChecked(
                self.config["general"]["listenFor"]["iceriver"]
            )
            #additional listeners
            self.checkListenVolcminer.setChecked(
                self.config["general"]["listenFor"]["additional"]["volcminer"]
            )

            # api
            self.lineBitmainPasswd.setText(self.config["api"]["bitmainAltPasswd"])
            self.lineWhatsminerPasswd.setText(self.config["api"]["whatsminerAltPasswd"])
            self.lineVolcminerPasswd.setText(self.config["api"]["volcminerAltPasswd"])
            self.linePbfarmerKey.setText(self.config["api"]["pbfarmerKey"])

            # logs
            self.comboLogLevel.setCurrentText(self.config["logs"]["logLevel"])
            self.spinMaxLogSize.setValue(self.config["logs"]["maxLogSize"])
            self.comboOnMaxLogSize.setCurrentIndex(self.config["logs"]["onMaxLogSize"])
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
            self.actionAutoStartOnLaunch.setChecked(
                self.config["instance"]["options"]["autoStartOnLaunch"]
            )
            self.actionEnableIDTable.setChecked(
                self.config["instance"]["table"]["enableIDTable"]
            )

        if self.actionEnableIDTable.isChecked():
            self.toggle_table_settings(True)

        logger.info(" init ListenerManager().")
        self.lm = ListenerManager(self)
        self.lm.listen_complete.connect(self.show_confirm)
        # restart listeners on fail
        self.lm.listen_error.connect(self.restart_listen)

        logger.info(" init inactive timer for 900000ms.")
        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        logger.info(" init APIClient().")
        self.api_client = APIClient(self)

        logger.info(" init systray.")
        self.sys_tray = None
        self.create_or_destroy_systray()

        self.actionDisableInactiveTimer.changed.connect(self.restart_listen)
        self.actionEnableIDTable.changed.connect(
            lambda: self.toggle_table_settings(self.actionEnableIDTable.isChecked())
        )
        self.checkEnableSysTray.stateChanged.connect(self.create_or_destroy_systray)
        self.comboLogLevel.currentIndexChanged.connect(self.set_logger_level)

        # status bar
        self.iprStatus.messageChanged.connect(self.update_status_msg)
        self.update_status_msg()

        self.update_stacked_widget()

        if self.actionAutoStartOnLaunch.isChecked():
            self.start_listen()

    def create_or_destroy_systray(self):
        if self.checkEnableSysTray.isChecked():
            self.sys_tray = QSystemTrayIcon(
                QIcon(":rc/img/BitCapIPR_BLK-02_Square.png"), self
            )
            self.system_tray_menu = QMenu()
            self.system_tray_menu.addAction("Show/Hide", self.toggle_visibility)
            self.actionSysStartListen = self.system_tray_menu.addAction(
                "Start Listen", self.start_listen
            )
            self.actionSysStopListen = self.system_tray_menu.addAction(
                "Stop Listen", self.stop_listen
            )
            self.actionSysStopListen.setEnabled(False)
            self.system_tray_menu.addSeparator()
            self.system_tray_menu.addAction("Quit", self.quit)
            if self.lm.listeners:
                self.actionSysStartListen.setEnabled(False)
                self.actionSysStopListen.setEnabled(True)
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

    def update_status_msg(self):
        if self.lm.listeners and not self.iprStatus.currentMessage():
            self.iprStatus.showMessage(
                f"Status :: UDP listening on 0.0.0.0[:{self.active_ports}]..."
            )
        if not self.iprStatus.currentMessage():
            self.iprStatus.showMessage("Status :: Ready.")

    def about(self):
        self.aboutDialog = IPRAbout(
            self,
            "About",
            f"{APP_INFO['name']} is a {APP_INFO['desc']}\nVersion {APP_INFO['appversion']}\nQt Version {APP_INFO['qt']}\nPython Version {APP_INFO['python']}\n{APP_INFO['author']}\nPowered by {APP_INFO['company']}\n",
        )
        self.aboutDialog._acceptButton.clicked.connect(self.aboutDialog.window().close)
        self.aboutDialog.show()

    def open_log(self):
        QDesktopServices.openUrl(
            QUrl(f"file:///{get_log_path()}/ipr.log", QUrl.ParsingMode.TolerantMode)
        )

    def open_issues(self):
        webbrowser.open(f"{APP_INFO['source']}/issues", new=2)

    def open_source(self):
        webbrowser.open(f"{APP_INFO['source']}", new=2)

    def open_dashboard(self, ip):
        webbrowser.open("http://{0}".format(ip), new=2)

    def start_listen(self):
        logger.info(" start listeners.")
        listener_config = {
            "antminer": self.checkListenAntminer.isChecked(),
            "whatsminer": self.checkListenWhatsminer.isChecked(),
            "iceriver": self.checkListenIceRiver.isChecked(),
        }
        if not any(enabled for _, enabled in listener_config.items()):
            logger.error(
                "start_listen: no listeners configured. at least one needs to be checked."
            )
            self.iprStatus.showMessage(
                "Status :: Failed to start listeners. No listeners configured", 5000
            )
            return
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        if self.sys_tray:
            self.actionSysStartListen.setEnabled(False)
            self.actionSysStopListen.setEnabled(True)
        self.actionIPRStart.setEnabled(False)
        self.actionIPRStop.setEnabled(True)
        self.lm.start(listener_config)
        self.active_ports = ",".join(
            [str(listener.port) for listener in self.lm.listeners]
        )
        if self.sys_tray and not self.isVisible():
            self.sys_tray.showMessage(
                "IPR Listener: Start",
                f"Started Listening on 0.0.0.0[:{self.active_ports}]...",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.iprStatus.showMessage(
            f"Status :: UDP listening on 0.0.0.0[:{self.active_ports}]..."
        )

    def stop_listen(self, timeout=False):
        logger.info(" stop listeners.")
        self.inactive.stop()
        if timeout:
            logger.warning("stop_listen : timeout.")
            if self.sys_tray and not self.isVisible():
                self.sys_tray.showMessage(
                    "IPR Listener: Inactive timeout!",
                    "Timeout exceeded. Stopping listeners...",
                    QSystemTrayIcon.MessageIcon.Warning,
                    3000,
                )
            else:
                QMessageBox.warning(
                    self,
                    "Timeout",
                    "Inactive timeout exceeded! Stopping listeners...",
                )
        if self.sys_tray:
            self.actionSysStartListen.setEnabled(True)
            self.actionSysStopListen.setEnabled(False)
        if self.actionEnableIDTable.isChecked():
            self.idTable.setRowCount(0)
        self.actionIPRStart.setEnabled(True)
        self.actionIPRStop.setEnabled(False)
        self.lm.stop_listeners()
        if self.sys_tray and not self.isVisible():
            self.sys_tray.showMessage(
                "IPR Listener: Stop",
                "Stopped UDP listening.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.iprStatus.clearMessage()

    def restart_listen(self):
        if self.lm.listeners:
            logger.info(" restart listeners.")
            self.stop_listen()
            self.start_listen()

    # confirm
    def show_confirm(self):
        logger.info(" show IP confirmation.")
        if not self.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        ip, mac, type = self.lm.result.split(",")
        if type == "antminer" and self.checkListenVolcminer.isChecked():
            self.api_client.create_volcminer_client(ip, self.lineVolcminerPasswd.text())
            if self.api_client.is_volcminer():
                type = "volcminer"
            self.api_client.close_client()
        logger.info(f"show_confirm : got {ip},{mac},{type} from listener.")
        if type == "iceriver":
            self.api_client.create_iceriver_client(ip, self.linePbfarmerKey.text())
            mac = self.api_client.get_iceriver_mac_addr()
            self.api_client.close_client()
            logger.info(f"show_confirm : got iceriver mac addr : {mac}")
        self.iprStatus.showMessage(f"Status :: Got {type}: IP:{ip} MAC:{mac}", 3000)
        if self.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip)
        if self.actionEnableIDTable.isChecked():
            self.populate_table_row(ip, mac, type)
            self.activateWindow()
        else:
            confirm = IPRConfirmation()
            # IPRConfirmation Signals
            confirm.actionOpenBrowser.clicked.connect(lambda: self.open_dashboard(ip))
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
            self.confirms.append(confirm)
            if self.sys_tray and not self.isVisible():
                if self.sys_tray.isSignalConnected(
                    QMetaMethod().fromSignal(self.sys_tray.messageClicked)
                ):
                    self.confirms[-2].show()
                    self.sys_tray.messageClicked.disconnect()
                self.sys_tray.messageClicked.connect(
                    lambda: self.show_confirm_from_sys_tray(confirm)
                )
                # workaround for clickable notification on linux
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

    def show_confirm_from_sys_tray(self, confirm):
        confirm.show()
        confirm.activateWindow()
        self.sys_tray.messageClicked.disconnect()

    def copy_text(self, lineEdit):
        lineEdit.selectAll()
        lineEdit.copy()

    # id table view
    def populate_table_row(self, ip: str, mac: str, type: str):
        client_auth = None
        match type:
            case "antminer":
                client_auth = self.lineBitmainPasswd.text()
            case "volcminer":
                client_auth = self.lineVolcminerPasswd.text()
            case "iceriver":
                client_auth = self.linePbfarmerKey.text()
        self.api_client.create_client_from_type(type, ip, client_auth)
        if not self.api_client.client:
            self.iprStatus.showMessage(
                "Status :: Failed to connect or authenticate client.", 5000
            )
        logger.info(f"populate_table : get target data from ip {ip}.")
        t_data = self.api_client.get_target_data_from_type(type)
        self.api_client.close_client()
        logger.info("populate_table : write table data.")
        rowPosition = self.idTable.rowCount()
        self.idTable.insertRow(rowPosition)
        actionLocateMiner = QLabel()
        actionLocateMiner.setPixmap(QPixmap(":theme/icons/rc/flash.png"))
        actionLocateMiner.setToolTip("Locate Miner")
        self.idTable.setCellWidget(rowPosition, 0, actionLocateMiner)
        self.idTable.setItem(rowPosition, 1, QTableWidgetItem(ip))
        self.idTable.setItem(rowPosition, 2, QTableWidgetItem(mac))
        self.idTable.setItem(rowPosition, 3, QTableWidgetItem(t_data["serial"]))
        # ASIC TYPE
        self.idTable.setItem(rowPosition, 4, QTableWidgetItem(type))
        # SUBTYPE
        self.idTable.setItem(rowPosition, 5, QTableWidgetItem(t_data["subtype"]))
        # ALGO
        self.idTable.setItem(rowPosition, 6, QTableWidgetItem(t_data["algorithm"]))
        # FIRMWARE
        self.idTable.setItem(rowPosition, 7, QTableWidgetItem(t_data["firmware"]))
        # PLATFORM
        self.idTable.setItem(rowPosition, 8, QTableWidgetItem(t_data["platform"]))

    def show_table_context(self):
        self.table_context = QMenu()
        self.actionContextOpenSelectedIPs = self.table_context.addAction(
            "Open Selected IPs"
        )
        self.actionContextOpenSelectedIPs.triggered.connect(self.open_selected_ips)
        self.actionContextCopySelectedElements = self.table_context.addAction(
            "Copy Selected Elements"
        )
        self.actionContextCopySelectedElements.triggered.connect(self.copy_selected)
        self.actionContextExport = self.table_context.addAction("Export")
        self.actionContextExport.triggered.connect(self.export_table)
        self.table_context.exec(QCursor.pos())

    def toggle_table_settings(self, enabled: bool):
        self.actionOpenSelectedIPs.setEnabled(enabled)
        self.actionCopySelectedElements.setEnabled(enabled)
        self.actionExport.setEnabled(enabled)

    def locate_miner(self, row: int, col: int):
        if col == 0:
            miner_type = self.idTable.item(row, 4).text()
            ip_addr = self.idTable.item(row, 1).text()
            logger.info(f" locate miner {ip_addr}.")
            client_auth = None
            match miner_type:
                case "antminer":
                    client_auth = self.lineBitmainPasswd.text()
                case "volcminer":
                    #client_auth = self.lineVolcminerPasswd.text()
                    return self.iprStatus.showMessage(
                        "Status :: Failed to locate miner: VolcMiner is currently not supported.", 5000
                    )
                case "iceriver":
                    client_auth = self.linePbfarmerKey.text()
                case "whatsminer":
                    client_auth = self.lineWhatsminerPasswd.text()
            self.api_client.create_client_from_type(miner_type, ip_addr, client_auth)
            client = self.api_client.get_client()
            if not client:
                return self.iprStatus.showMessage(
                    "Status :: Failed to connect or authenticate client.", 5000
                )
            self.api_client.locate_miner(miner_type)
            if client.err:
                return self.iprStatus.showMessage(
                    f"Status :: Failed to locate miner: {client.err}", 5000
                )
            self.iprStatus.showMessage(f"Status :: Locating miner: {ip_addr}...", 10000)

    def double_click_item(self, model_index):
        row = model_index.row()
        col = model_index.column()
        # ip
        if col == 1:
            self.open_dashboard(self.idTable.item(row, col).text())
        # serial
        if col == 3:
            self.idTable.editItem(self.idTable.item(row, col))

    def open_selected_ips(self):
        rows = self.idTable.rowCount()
        if not rows:
            return
        for r in range(rows):
            if self.idTable.item(r, 1).isSelected():
                self.open_dashboard(self.idTable.item(r, 1).text())

    def copy_selected(self):
        logger.info(" copy selected elements.")
        rows = self.idTable.rowCount()
        cols = self.idTable.columnCount()
        if not rows:
            return
        out = ""
        if len(self.idTable.selectedItems()) == 1:
            out += self.idTable.selectedItems()[0].text()
            out += "\n"
        else:
            for i in range(rows):
                for j in range(1, cols):
                    if self.idTable.item(i, j).isSelected():
                        out += self.idTable.item(i, j).text()
                        out += ","
                out += "\n"
        logger.info("copy_selected : copy elements to clipboard.")
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(out.strip(), mode=cb.Mode.Clipboard)
        self.iprStatus.showMessage("Status :: Copied elements to clipboard.", 3000)

    def export_table(self):
        logger.info("export table.")
        rows = self.idTable.rowCount()
        cols = self.idTable.columnCount()
        if not rows:
            return
        out = "IP, MAC, SERIAL, TYPE, SUBTYPE, ALGORITHM, FIRMWARE, PLATFORM \n"
        for i in range(rows):
            for j in range(1, cols):
                out += self.idTable.item(i, j).text()
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
        self.iprStatus.showMessage(f"Status :: Wrote table as .CSV to {p}.", 3000)

    # app config view
    def show_app_config(self):
        self.stackedWidget.setCurrentIndex(2)

    def toggle_app_config(self):
        if self.checkEnableSysTray.isChecked():
            self.comboOnWindowClose.setEnabled(True)
        else:
            self.comboOnWindowClose.setCurrentIndex(0)
            self.comboOnWindowClose.setEnabled(False)

    def toggle_show_passwd(self, line: QLineEdit, action):
        if line.echoMode() == QLineEdit.EchoMode.Password:
            line.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(QIcon(":theme/icons/rc/hide.png"))
        elif line.echoMode() == QLineEdit.EchoMode.Normal:
            line.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(QIcon(":theme/icons/rc/view.png"))

    def save_settings(self):
        self.update_settings()
        self.iprStatus.showMessage("Status :: Wrote settings to config.", 3000)

    def set_logger_level(self):
        logger.manager.root.setLevel(self.comboLogLevel.currentText())
        logger.log(
            logger.manager.root.level,
            f" change logger to level {self.comboLogLevel.currentText()}.",
        )

    def update_settings(self):
        logger.info(" write settings to config.")
        instance = {
            "options": {
                "alwaysOpenIPInBrowser": self.actionAlwaysOpenIPInBrowser.isChecked(),
                "disableInactiveTimer": self.actionDisableInactiveTimer.isChecked(),
                "autoStartOnLaunch": self.actionAutoStartOnLaunch.isChecked(),
            },
            "table": {"enableIDTable": self.actionEnableIDTable.isChecked()},
        }
        config = {
            "general": {
                "enableSysTray": self.checkEnableSysTray.isChecked(),
                "onWindowClose": self.comboOnWindowClose.currentIndex(),
                "listenFor": {
                    "antminer": self.checkListenAntminer.isChecked(),
                    "whatsminer": self.checkListenWhatsminer.isChecked(),
                    "iceriver": self.checkListenIceRiver.isChecked(),
                    "additional": {
                        "volcminer": self.checkListenVolcminer.isChecked(),
                    }
                },
            },
            "api": {
                "bitmainAltPasswd": self.lineBitmainPasswd.text(),
                "whatsminerAltPasswd": self.lineWhatsminerPasswd.text(),
                "volcminerAltPasswd": self.lineVolcminerPasswd.text(),
                "pbfarmerKey": self.linePbfarmerKey.text(),
            },
            "logs": {
                "logLevel": self.comboLogLevel.currentText(),
                "maxLogSize": self.spinMaxLogSize.value(),
                "onMaxLogSize": self.comboOnMaxLogSize.currentIndex(),
                "flushInterval": self.comboFlushInterval.currentIndex(),
            },
            "instance": instance,
        }
        self.config_json = json.dumps(config, indent=4)
        with open(Path(self.config_path, "config.json"), "w") as f:
            f.write(self.config_json)
        self.update_stacked_widget()
        self.iprStatus.showMessage("Status :: Updated settings to config.", 1000)

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def close_to_tray_or_exit(self):
        if self.sys_tray and self.comboOnWindowClose.currentIndex() == 1:
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
        for c in self.confirms:
            c.close()
        self.iprStatus.showMessage("Status :: Killed all confirmations.", 3000)

    def close_root_logger(self, log):
        for handler in log.root.handlers:
            handler.close()
            log.root.removeHandler(handler)

    def quit(self):
        if self.sys_tray and not self.isVisible():
            self.toggle_visibility()
        self.lm.stop_listeners()
        self.killall()
        logger.info(" exit app.")
        # flush log on close if set
        if (
            self.comboOnMaxLogSize.currentIndex() == 0
            and self.comboFlushInterval.currentIndex() == 1
        ):
            logger.root.handlers[0].doRollover()
        self.close_root_logger(logger)
        self.close()
        self = None
