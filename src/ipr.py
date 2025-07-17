import logging
import os
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    QFile,
    QIODevice,
    QMetaMethod,
    Qt,
    QTextStream,
    QTimer,
    QUrl,
)
from PySide6.QtGui import (
    QCursor,
    QDesktopServices,
    QIcon,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QTableWidgetItem,
)

import ui.resources  # noqa F401
from iprabout import IPRAbout
from iprconfirmation import IPRConfirmation

from ui.MainWindow import Ui_MainWindow
from ui.widgets.ipr.menubar import IPR_Menubar
from ui.widgets.titlebar import TitleBar

from mod.api import settings as api_settings
from mod.api.client import APIClient
from mod.lm.listenermanager import ListenerManager

from utils import (
    APP_INFO,
    CURR_PLATFORM,
    get_config_file_path,
    get_default_config,
    get_log_dir,
    read_config,
    write_config,
)

# logger
logger = logging.getLogger(__name__)


class IPR(QMainWindow, Ui_MainWindow):
    def __init__(self):
        logger.info(" start IPR() init.")
        super().__init__(flags=Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)
        self.confirms = []
        self.sys_tray = None

        logger.info(" init inactive timer for 900000ms.")
        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        logger.info(" init mod lm.")
        self.lm = ListenerManager(self)
        self.lm.listen_complete.connect(self.show_confirm)
        # restart listeners on fail
        self.lm.listen_error.connect(self.restart_listen)

        logger.info(" init mod api.")
        self.api_client = APIClient(self)

        # title bar
        if CURR_PLATFORM == "darwin":
            self.title_bar = TitleBar(
                self, "BitCap IPReporter", ["close", "min"], style="mac"
            )
        else:
            self.title_bar = TitleBar(self, "BitCap IPReporter", ["min", "close"])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.close_to_tray_or_exit)
        titlebarwidget = self.titlebar.layout()
        if titlebarwidget:
            titlebarwidget.addWidget(self.title_bar)

        # menu bar
        self.menu_bar = IPR_Menubar()
        menubarwidget = self.menubar.layout()
        if menubarwidget:
            menubarwidget.addWidget(self.menu_bar)

        # menu_bar signals
        self.menu_bar.actionAbout.triggered.connect(self.about)
        self.menu_bar.actionOpenLog.triggered.connect(self.open_log)
        self.menu_bar.actionReportIssue.triggered.connect(self.open_issues)
        self.menu_bar.actionSourceCode.triggered.connect(self.open_source)
        self.menu_bar.actionKillAllConfirmations.triggered.connect(self.killall)
        self.menu_bar.actionQuit.triggered.connect(self.quit)
        self.menu_bar.menuOptions.triggered.connect(self.update_settings)
        self.menu_bar.menuTable.triggered.connect(self.update_settings)
        self.menu_bar.actionEnableIDTable.triggered.connect(self.update_stacked_widget)
        self.menu_bar.actionEnableIDTable.changed.connect(
            lambda: self.toggle_table_settings(
                self.menu_bar.actionEnableIDTable.isChecked()
            )
        )
        self.menu_bar.actionOpenSelectedIPs.triggered.connect(self.open_selected_ips)
        self.menu_bar.actionCopySelectedElements.triggered.connect(self.copy_selected)
        self.menu_bar.actionImport.triggered.connect(self.import_table)
        self.menu_bar.actionExport.triggered.connect(self.export_table)
        self.menu_bar.actionSettings.triggered.connect(self.show_app_config)
        self.menu_bar.actionDisableInactiveTimer.changed.connect(self.restart_listen)
        # app config signals
        self.checkEnableSysTray.toggled.connect(self.toggle_sys_tray_settings)
        self.checkEnableSysTray.stateChanged.connect(self.create_or_destroy_systray)
        self.comboOnWindowClose.currentIndexChanged.connect(
            self.update_sys_tray_visibility
        )
        self.spinLocateDuration.valueChanged.connect(self.update_miner_locate_duration)
        self.comboLogLevel.currentIndexChanged.connect(self.set_logger_level)
        self.actionIPRCancelConfig.clicked.connect(self.update_stacked_widget)
        self.actionIPRSaveConfig.clicked.connect(self.update_settings)
        self.actionIPRResetConfig.clicked.connect(self.reset_settings)
        # listener signals
        self.actionIPRStart.clicked.connect(self.start_listen)
        self.actionIPRStop.clicked.connect(self.stop_listen)
        # status bar
        self.iprStatus.messageChanged.connect(self.update_status_msg)

        self.labelLogo.setPixmap(QPixmap(":rc/img/scalable/BitCapIPRCenterLogo.svg"))

        self.listenerConfig = QButtonGroup(exclusive=False)
        self.listenerConfig.addButton(self.checkListenAntminer, 1)
        self.listenerConfig.addButton(self.checkListenIceRiver, 2)
        self.listenerConfig.addButton(self.checkListenWhatsminer, 3)
        self.listenerConfig.addButton(self.checkListenVolcminer, 4)
        self.listenerConfig.addButton(self.checkListenGoldshell, 5)
        self.listenerConfig.addButton(self.checkListenSealminer, 6)
        self.listenerConfig.buttonClicked.connect(self.restart_listen)

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
        self.idTable.setColumnWidth(2, 120)
        self.idTable.setColumnWidth(3, 135)
        self.idTable.setColumnWidth(5, 130)
        self.idTable.setColumnWidth(7, 180)
        self.idTable.doubleClicked.connect(self.double_click_item)
        self.idTable.cellClicked.connect(self.locate_miner)

        duration_line = self.spinLocateDuration.lineEdit()
        duration_line.setReadOnly(True)

        self.actionToggleBitmainPasswd = self.create_passwd_toggle_action(
            self.lineBitmainPasswd
        )
        self.actionToggleWhatsminerPasswd = self.create_passwd_toggle_action(
            self.lineWhatsminerPasswd
        )
        self.actionToggleVolcminerPasswd = self.create_passwd_toggle_action(
            self.lineVolcminerPasswd
        )
        self.actionToggleGoldshellPasswd = self.create_passwd_toggle_action(
            self.lineGoldshellPasswd
        )
        self.actionToggleSealminerPasswd = self.create_passwd_toggle_action(
            self.lineSealminerPasswd
        )
        self.actionTogglePbfarmerKey = self.create_passwd_toggle_action(
            self.linePbfarmerKey
        )
        self.actionToggleVnishPasswd = self.create_passwd_toggle_action(
            self.lineVnishPasswd
        )

        self.read_settings()
        # api settings
        self.update_miner_locate_duration()

        if self.menu_bar.actionEnableIDTable.isChecked():
            self.toggle_table_settings(True)

        self.create_or_destroy_systray()
        self.update_status_msg()
        self.update_stacked_widget()

        if self.menu_bar.actionAutoStartOnLaunch.isChecked():
            self.start_listen()

    def create_or_destroy_systray(self):
        if self.checkEnableSysTray.isChecked():
            self.sys_tray = QSystemTrayIcon(
                QIcon(":rc/img/BitCapIPR_BLK-02_Square.png"), self
            )
            self.system_tray_menu = QMenu()
            self.system_tray_menu.addAction("Show/Hide", self.toggle_visibility)
            self.system_tray_menu.addAction("Open Log", self.open_log)
            self.actionSysStartListen = self.system_tray_menu.addAction(
                "Start Listen", self.start_listen
            )
            self.actionSysStopListen = self.system_tray_menu.addAction(
                "Stop Listen", self.stop_listen
            )
            self.actionSysStopListen.setEnabled(False)
            self.system_tray_menu.addSeparator()
            self.system_tray_menu.addAction("Settings", self.show_app_config)
            self.system_tray_menu.addAction("Quit", self.quit)
            if self.lm.listeners:
                self.actionSysStartListen.setEnabled(False)
                self.actionSysStopListen.setEnabled(True)
            self.sys_tray.setContextMenu(self.system_tray_menu)
        else:
            if self.sys_tray:
                self.sys_tray.hide()
            self.sys_tray = None

    def update_sys_tray_visibility(self, current_index):
        if self.sys_tray:
            match current_index:
                case 0:  # minimize to tray
                    if self.sys_tray.isVisible():
                        self.sys_tray.hide()
                case 1:  # close
                    if not self.sys_tray.isVisible():
                        self.sys_tray.show()

    def update_stacked_widget(self):
        logger.info(" update view.")
        if self.menu_bar.actionEnableIDTable.isChecked():
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)

    def update_status_msg(self):
        if self.lm.listeners and not self.iprStatus.currentMessage():
            self.iprStatus.showMessage(
                f"Status :: UDP listening on 0.0.0.0[{self.active_miners}]..."
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
            QUrl(f"file:///{get_log_dir()}/ipr.log", QUrl.ParsingMode.TolerantMode)
        )

    def open_issues(self):
        webbrowser.open(f"{APP_INFO['source']}/issues", new=2)

    def open_source(self):
        webbrowser.open(f"{APP_INFO['source']}", new=2)

    def open_dashboard(self, ip):
        webbrowser.open("http://{0}".format(ip), new=2)

    def start_listen(self):
        logger.info(" start listeners.")
        if not any(
            listenFor.isChecked() for listenFor in self.listenerConfig.buttons()
        ):
            logger.error(
                "start_listen : no listeners configured. at least one listener needs to be checked."
            )
            self.iprStatus.showMessage(
                "Status :: Failed to start listeners. No listeners configured", 5000
            )
            return
        if not self.menu_bar.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        if self.sys_tray:
            self.actionSysStartListen.setEnabled(False)
            self.actionSysStopListen.setEnabled(True)
        self.actionIPRStart.setEnabled(False)
        self.actionIPRStop.setEnabled(True)
        self.lm.start(self.listenerConfig)
        self.active_miners = ", ".join(
            [btn.text() for btn in self.listenerConfig.buttons() if btn.isChecked()]
        )
        if self.sys_tray and not self.isVisible():
            self.sys_tray.showMessage(
                "IPR Listener: Start",
                f"Started Listening on 0.0.0.0[{self.active_miners}]...",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.iprStatus.showMessage(
            f"Status :: UDP listening on 0.0.0.0[{self.active_miners}]..."
        )

    def stop_listen(self, timeout=False):
        logger.info(" stop listeners.")
        self.inactive.stop()
        if self.sys_tray:
            self.actionSysStartListen.setEnabled(True)
            self.actionSysStopListen.setEnabled(False)
        if self.menu_bar.actionEnableIDTable.isChecked():
            self.idTable.setRowCount(0)
        self.actionIPRStart.setEnabled(True)
        self.actionIPRStop.setEnabled(False)
        self.lm.stop_listeners()
        if timeout:
            logger.warning("stop_listen : timeout.")
            self.iprStatus.showMessage(
                "Status :: Inactive timeout. Stopped listeners", 5000
            )
            if self.sys_tray and not self.isVisible():
                self.sys_tray.showMessage(
                    "IPR Listener: Inactive timeout!",
                    "Timeout exceeded. Stopped listeners...",
                    QSystemTrayIcon.MessageIcon.Warning,
                    3000,
                )
            else:
                QMessageBox.warning(
                    self,
                    "Timeout",
                    "Inactive timeout exceeded! Stopped listeners...",
                )
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
    def show_confirm(self, result: str):
        logger.info(" show IP confirmation.")
        if not self.menu_bar.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        ip, mac, type, sn = result.split(",")
        if type == "antminer" and self.checkListenVolcminer.isChecked():
            self.api_client.create_volcminer_client(ip, self.lineVolcminerPasswd.text())
            if self.api_client.is_volcminer():
                type = "volcminer"
            self.api_client.close_client()
        logger.info(f"show_confirm : got {ip},{mac},{sn},{type} from listener.")
        if type == "iceriver":
            self.api_client.create_iceriver_client(
                ip, None, self.linePbfarmerKey.text()
            )
            mac = self.api_client.get_iceriver_mac_addr()
            self.api_client.close_client()
            logger.info(f"show_confirm : got iceriver mac addr : {mac}")
        self.iprStatus.showMessage(f"Status :: Got {type}: IP:{ip}, MAC:{mac}", 3000)
        if self.menu_bar.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip)
        if self.menu_bar.actionEnableIDTable.isChecked() and self.isVisible():
            target_data = self.get_data_from_type(type, ip)
            data = {"ip": ip, "mac": mac, "type": type}
            data.update(target_data)
            if sn:
                data["serial"] = sn
            self.populate_table_row(**data)
            self.activateWindow()
        else:
            confirm = IPRConfirmation()
            # IPRConfirmation Signals
            confirm.actionOpenBrowser.clicked.connect(lambda: self.open_dashboard(ip))
            confirm.accept.clicked.connect(confirm.hide)
            # copy action
            confirm.lineIPField.actionCopy = self.create_copy_text_action(
                confirm.lineIPField
            )
            confirm.lineMACField.actionCopy = self.create_copy_text_action(
                confirm.lineMACField
            )
            logger.info("show_confirm : show IPRConfirmation.")
            confirm.lineIPField.setText(ip)
            confirm.lineMACField.setText(mac.upper())
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
                # workaround to get messageClicked signal on Linux/X11
                # https://bugreports.qt.io/browse/QTBUG-87329
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

    def create_copy_text_action(self, line: QLineEdit):
        copy_action = line.addAction(
            QIcon(":theme/icons/rc/copy.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        copy_action.triggered.connect(lambda: self.copy_text(line))
        return copy_action

    def copy_text(self, lineEdit):
        lineEdit.selectAll()
        lineEdit.copy()

    # id table view
    def get_data_from_type(self, type: str, ip: str):
        client_auth = ""
        custom_auth = ""
        match type:
            case "antminer":
                client_auth = self.lineBitmainPasswd.text()
                custom_auth = self.lineVnishPasswd.text()
            case "volcminer":
                client_auth = self.lineVolcminerPasswd.text()
            case "goldshell":
                client_auth = self.lineGoldshellPasswd.text()
            case "iceriver":
                custom_auth = self.linePbfarmerKey.text()
            case "sealminer":
                client_auth = self.lineSealminerPasswd.text()
        self.api_client.create_client_from_type(type, ip, client_auth, custom_auth)
        if not self.api_client.client:
            self.iprStatus.showMessage(
                "Status :: Failed to connect or authenticate client.", 5000
            )
        logger.info(f"populate_table : get target data from ip {ip}.")
        t_data = self.api_client.get_target_data_from_type(type)
        self.api_client.close_client()
        return t_data

    def populate_table_row(self, **data: str) -> None:
        """
        arguments:
            **data: dict[str. str] -- row data with the following key structure:
                'ip', 'mac', 'serial', 'type', 'subtype', 'algoritmn', 'firmware', 'platform'
        """
        logger.info("populate_table : write table data.")
        rowPosition = self.idTable.rowCount()
        self.idTable.insertRow(rowPosition)
        actionLocateMiner = QLabel()
        actionLocateMiner.setPixmap(QPixmap(":theme/icons/rc/flash.png"))
        actionLocateMiner.setToolTip("Locate Miner")
        self.idTable.setCellWidget(rowPosition, 0, actionLocateMiner)
        self.idTable.setItem(rowPosition, 1, QTableWidgetItem(data["ip"]))
        self.idTable.setItem(rowPosition, 2, QTableWidgetItem(data["mac"].upper()))
        self.idTable.setItem(rowPosition, 3, QTableWidgetItem(data["serial"]))
        # ASIC TYPE
        self.idTable.setItem(rowPosition, 4, QTableWidgetItem(data["type"]))
        # SUBTYPE
        self.idTable.setItem(rowPosition, 5, QTableWidgetItem(data["subtype"]))
        # ALGO
        self.idTable.setItem(rowPosition, 6, QTableWidgetItem(data["algorithm"]))
        # FIRMWARE
        self.idTable.setItem(rowPosition, 7, QTableWidgetItem(data["firmware"]))
        # PLATFORM
        self.idTable.setItem(rowPosition, 8, QTableWidgetItem(data["platform"]))
        self.idTable.scrollToBottom()

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
        self.actionContextImport = self.table_context.addAction("Import")
        self.actionContextImport.triggered.connect(self.import_table)
        self.actionContextExport = self.table_context.addAction("Export")
        self.actionContextExport.triggered.connect(self.export_table)
        self.table_context.exec(QCursor.pos())

    def toggle_table_settings(self, enabled: bool):
        self.menu_bar.actionOpenSelectedIPs.setEnabled(enabled)
        self.menu_bar.actionCopySelectedElements.setEnabled(enabled)
        self.menu_bar.actionImport.setEnabled(enabled)
        self.menu_bar.actionExport.setEnabled(enabled)

    def locate_miner(self, row: int, col: int):
        if col == 0:
            miner_type = self.idTable.item(row, 4).text()
            ip_addr = self.idTable.item(row, 1).text()
            if self.api_client.locate and self.api_client.locate.isActive():
                return logger.warning(
                    "locate_miner : already locating a miner. Ignoring..."
                )
            logger.info(f" locate miner {ip_addr}.")
            client_auth = ""
            custom_auth = ""
            match miner_type:
                case "antminer":
                    client_auth = self.lineBitmainPasswd.text()
                    if not self.checkVnishUseAntminerLogin.isChecked():
                        custom_auth = self.lineVnishPasswd.text()
                    else:
                        custom_auth = self.lineBitmainPasswd.text()
                case "volcminer":
                    # client_auth = self.lineVolcminerPasswd.text()
                    return self.iprStatus.showMessage(
                        "Status :: Failed to locate miner: VolcMiner is currently not supported.",
                        5000,
                    )
                case "iceriver":
                    custom_auth = self.linePbfarmerKey.text()
                case "whatsminer":
                    client_auth = self.lineWhatsminerPasswd.text()
                case "goldshell":
                    client_auth = self.lineGoldshellPasswd.text()
                case "sealminer":
                    client_auth = self.lineSealminerPasswd.text()
            self.api_client.create_client_from_type(
                miner_type, ip_addr, client_auth, custom_auth
            )
            client = self.api_client.get_client()
            if not client:
                return self.iprStatus.showMessage(
                    "Status :: Failed to connect or authenticate client.", 5000
                )
            self.api_client.locate_miner(miner_type)
            if client._error:
                return self.iprStatus.showMessage(
                    f"Status :: Failed to locate miner: {client._error}", 5000
                )
            self.iprStatus.showMessage(
                f"Status :: Locating miner: {ip_addr}...",
                self.locateMinerDuration,
            )

    def double_click_item(self, model_index):
        item = self.idTable.itemFromIndex(model_index)
        match item.column():
            case 1:  # ip column
                self.open_dashboard(item.text())
            case 3:  # serial column
                self.idTable.editItem(item)
            case _:
                return

    def open_selected_ips(self):
        rows = self.idTable.rowCount()
        if not rows:
            return
        selected_ips = [x for x in self.idTable.selectedIndexes() if x.column() == 1]
        for index in selected_ips:
            item = self.idTable.itemFromIndex(index)
            self.open_dashboard(item.text())

    def copy_selected(self):
        logger.info(" copy selected elements.")
        rows = self.idTable.rowCount()
        if not rows:
            return
        out = ""
        selected_indexes = self.idTable.selectedIndexes()
        for r in range(rows):
            selected_indexes_in_row = [x for x in selected_indexes if x.row() == r]
            if len(selected_indexes_in_row) == 0:
                continue
            if len(selected_indexes_in_row) == 1:
                # single column
                item = self.idTable.itemFromIndex(selected_indexes_in_row[0])
                if item.column() == 0:
                    continue
                if item.column() == 1:
                    out += f"http://{item.text()}"
                else:
                    out += f"{item.text()}"
                out += "\n"
                continue
            for index in range(len(selected_indexes_in_row)):
                if not self.idTable.itemFromIndex(selected_indexes_in_row[index]):
                    continue
                item = self.idTable.itemFromIndex(selected_indexes_in_row[index])
                if item.column() == 0:
                    continue
                if item.column() == 1:
                    out += f"http://{item.text()},"
                else:
                    out += f"{item.text()},"
            out += "\n"
        logger.info("copy_selected : copy elements to clipboard.")
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(out.strip(), mode=cb.Mode.Clipboard)
        self.iprStatus.showMessage("Status :: Copied elements to clipboard.", 3000)

    def import_table(self):
        logger.info("import table.")
        table_file, _ = QFileDialog.getOpenFileName(
            self,
            "Open .CSV",
            Path(Path.home(), "Documents", "ipr").resolve().__str__(),
            ".CSV Files (*.csv)",
        )
        self.idTable.setRowCount(0)
        table_csv = QFile(table_file)
        if table_csv.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(table_csv)
            header = stream.readLine()
            headers = [x.strip().lower() for x in header.split(",")]
            stream.seek(len(header) + 1)
            while not stream.atEnd():
                line = stream.readLine()
                if line:
                    row = dict(zip(headers, line.split(",")))
                    self.populate_table_row(**row)
        else:
            logger.error(f"import_table : failed to read file {table_file}.")
            self.iprStatus.showMessage("Status :: Failed to import table.", 5000)
            return

    def export_table(self):
        logger.info("export table.")
        rows = self.idTable.rowCount()
        cols = self.idTable.columnCount()
        if not rows:
            return
        out = "IP,MAC,SERIAL,TYPE,SUBTYPE,ALGORITHM,FIRMWARE,PLATFORM\n"
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
        if self.sys_tray and not self.isVisible():
            self.toggle_visibility()
        self.stackedWidget.setCurrentIndex(2)

    def toggle_sys_tray_settings(self):
        if self.checkEnableSysTray.isChecked():
            self.comboOnWindowClose.setEnabled(True)
        else:
            self.comboOnWindowClose.setCurrentIndex(0)
            self.comboOnWindowClose.setEnabled(False)

    def update_miner_locate_duration(self):
        self.locateMinerDuration = self.spinLocateDuration.value() * 1000
        api_settings.update("locate_duration_ms", self.locateMinerDuration)
        logger.info(f" update miner locate duration: {self.locateMinerDuration}ms.")

    def create_passwd_toggle_action(self, line: QLineEdit):
        passwd_action = line.addAction(
            QIcon(":theme/icons/rc/view.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        passwd_action.setToolTip("Show/Hide password")
        passwd_action.triggered.connect(
            lambda: self.toggle_show_passwd(line, passwd_action)
        )
        return passwd_action

    def toggle_show_passwd(self, line: QLineEdit, action):
        if line.echoMode() == QLineEdit.EchoMode.Password:
            line.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(QIcon(":theme/icons/rc/hide.png"))
        elif line.echoMode() == QLineEdit.EchoMode.Normal:
            line.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(QIcon(":theme/icons/rc/view.png"))

    def read_settings(self):
        logger.info(" read config.")
        self.config_path = get_config_file_path()
        if os.path.exists(self.config_path):
            self.config = read_config(self.config_path)
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
            # additional listeners
            self.checkListenVolcminer.setChecked(
                self.config["general"]["listenFor"]["additional"]["volcminer"]
            )
            self.checkListenGoldshell.setChecked(
                self.config["general"]["listenFor"]["additional"]["goldshell"]
            )
            self.checkListenSealminer.setChecked(
                self.config["general"]["listenFor"]["additional"]["sealminer"]
            )

            # api
            self.lineBitmainPasswd.setText(
                self.config["api"]["auth"]["bitmainAltPasswd"]
            )
            self.lineWhatsminerPasswd.setText(
                self.config["api"]["auth"]["whatsminerAltPasswd"]
            )
            self.lineVolcminerPasswd.setText(
                self.config["api"]["auth"]["volcminerAltPasswd"]
            )
            self.lineGoldshellPasswd.setText(
                self.config["api"]["auth"]["goldshellAltPasswd"]
            )
            self.lineVnishPasswd.setText(
                self.config["api"]["auth"]["firmware"]["vnishAltPasswd"]
            )
            self.linePbfarmerKey.setText(
                self.config["api"]["auth"]["firmware"]["pbfarmerKey"]
            )

            # api settings
            self.spinLocateDuration.setValue(
                self.config["api"]["settings"]["locateDurationSecs"]
            )
            self.checkVnishUseAntminerLogin.setChecked(
                self.config["api"]["settings"]["vnishUseAntminerLogin"]
            )

            # logs
            self.comboLogLevel.setCurrentText(self.config["logs"]["logLevel"])
            self.spinMaxLogSize.setValue(self.config["logs"]["maxLogSize"])
            self.comboOnMaxLogSize.setCurrentIndex(self.config["logs"]["onMaxLogSize"])
            self.comboFlushInterval.setCurrentIndex(
                self.config["logs"]["flushInterval"]
            )

            # instance
            window = self.config["instance"]["geometry"]["mainWindow"]
            if window:
                self.setGeometry(*window)

            self.menu_bar.actionAlwaysOpenIPInBrowser.setChecked(
                self.config["instance"]["options"]["alwaysOpenIPInBrowser"]
            )
            self.menu_bar.actionDisableInactiveTimer.setChecked(
                self.config["instance"]["options"]["disableInactiveTimer"]
            )
            self.menu_bar.actionAutoStartOnLaunch.setChecked(
                self.config["instance"]["options"]["autoStartOnLaunch"]
            )
            self.menu_bar.actionEnableIDTable.setChecked(
                self.config["instance"]["table"]["enableIDTable"]
            )

    def update_settings(self):
        logger.info(" update settings to config.")
        instance = {
            "geometry": {
                "mainWindow": [
                    self.geometry().x(),
                    self.geometry().y(),
                    self.geometry().width(),
                    self.geometry().height(),
                ]
            },
            "options": {
                "alwaysOpenIPInBrowser": self.menu_bar.actionAlwaysOpenIPInBrowser.isChecked(),
                "disableInactiveTimer": self.menu_bar.actionDisableInactiveTimer.isChecked(),
                "autoStartOnLaunch": self.menu_bar.actionAutoStartOnLaunch.isChecked(),
            },
            "table": {"enableIDTable": self.menu_bar.actionEnableIDTable.isChecked()},
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
                        "goldshell": self.checkListenGoldshell.isChecked(),
                        "sealminer": self.checkListenSealminer.isChecked(),
                    },
                },
            },
            "api": {
                "auth": {
                    "bitmainAltPasswd": self.lineBitmainPasswd.text(),
                    "whatsminerAltPasswd": self.lineWhatsminerPasswd.text(),
                    "volcminerAltPasswd": self.lineVolcminerPasswd.text(),
                    "goldshellAltPasswd": self.lineGoldshellPasswd.text(),
                    "bitdeerAltPasswd": self.lineSealminerPasswd.text(),
                    "firmware": {
                        "vnishAltPasswd": self.lineVnishPasswd.text(),
                        "pbfarmerKey": self.linePbfarmerKey.text(),
                    },
                },
                "settings": {
                    "locateDurationSecs": self.spinLocateDuration.value(),
                    "vnishUseAntminerLogin": self.checkVnishUseAntminerLogin.isChecked(),
                },
            },
            "logs": {
                "logLevel": self.comboLogLevel.currentText(),
                "maxLogSize": self.spinMaxLogSize.value(),
                "onMaxLogSize": self.comboOnMaxLogSize.currentIndex(),
                "flushInterval": self.comboFlushInterval.currentIndex(),
            },
            "instance": instance,
        }
        self.config = config
        self.update_stacked_widget()
        self.iprStatus.showMessage("Status :: Updated settings to config.", 1000)

    def reset_settings(self):
        ok = QMessageBox.warning(
            self,
            "Confirm Reset Settings",
            "Are you sure you want to reset configuration to default?",
            buttons=QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
        )
        if ok == QMessageBox.StandardButton.Ok:
            logger.info(" reset settings.")
            config = read_config(get_default_config())
            write_config(self.config_path, config)
            self.read_settings()
            self.update_miner_locate_duration()
            self.create_or_destroy_systray()
            self.update_stacked_widget()
            self.iprStatus.showMessage(
                "Status :: Successfully restored to default settings.", 5000
            )

    def write_settings(self):
        self.update_settings()
        write_config(self.config_path, self.config)

    def set_logger_level(self):
        logger.manager.root.setLevel(self.comboLogLevel.currentText())
        logger.log(
            logger.manager.root.level,
            f" change logger to level {self.comboLogLevel.currentText()}.",
        )

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def close_to_tray_or_exit(self):
        if self.sys_tray and self.comboOnWindowClose.currentIndex() == 0:
            # force disable ID table option
            self.menu_bar.actionEnableIDTable.setChecked(False)
            self.update_stacked_widget()
            self.setVisible(False)
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
        logger.info(" write settings to disk.")
        self.write_settings()
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
