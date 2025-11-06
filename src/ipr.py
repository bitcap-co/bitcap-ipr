import logging
import os
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import (
    QEventLoop,
    QFile,
    QIODevice,
    QMetaMethod,
    QModelIndex,
    Qt,
    QTextStream,
    QTimer,
    QUrl,
)
from PySide6.QtGui import (
    QAction,
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
    QWidget,
)

import ui.resources  # noqa F401
from iprabout import IPRAbout
from iprconfirmation import IPRConfirmation
from mod.api import settings as api_settings
from mod.api.client import APIClient
from mod.lm.listenermanager import ListenerManager
from ui.MainWindow import Ui_MainWindow
from ui.widgets.ipr import (
    IPR_Menubar,
    IPR_Titlebar,
    IPRIndexWidgetItem,
    IPRIPWidgetItem,
    IPRTableContextMenu,
)
from utils import (
    APP_INFO,
    CURR_PLATFORM,
    deep_update,
    get_config_file_path,
    get_default_config,
    get_log_dir,
    read_config,
    write_config,
)

logger = logging.getLogger(__name__)


class IPR(QMainWindow, Ui_MainWindow):
    def __init__(self):
        logger.info(" start IPR() init.")
        super().__init__(flags=Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)
        self._app_instance = QApplication.instance()
        self.confirms: List[IPRConfirmation] = []
        self.sys_tray: Optional[QSystemTrayIcon] = None

        logger.info(" init inactive timer for 900000ms.")
        self.inactive = QTimer()
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        logger.info(" init mod lm.")
        self.lm = ListenerManager(self)
        self.lm.listen_complete.connect(self.process_result)
        # restart listeners on fail
        self.lm.listen_error.connect(self.restart_listen)

        logger.info(" init mod api.")
        self.api_client = APIClient(self)
        logger.info(" init miner locate duration for 10000ms.")
        self.miner_locate_duration: int = api_settings.get("locate_duration_ms")

        # initialize IPR_Titlebar widget
        if CURR_PLATFORM == "darwin":
            self.title_bar = IPR_Titlebar(
                self, "BitCap IPReporter", ["close", "min"], style="mac"
            )
        else:
            self.title_bar = IPR_Titlebar(self, "BitCap IPReporter", ["min", "close"])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.close_to_tray_or_exit)
        titlebarwidget = self.titlebar.layout()
        if titlebarwidget:
            titlebarwidget.addWidget(self.title_bar)

        # initialize IPR_Menubar widget
        self.menu_bar = IPR_Menubar()
        menubarwidget = self.menubar.layout()
        if menubarwidget:
            menubarwidget.addWidget(self.menu_bar)

        # IPR_Menubar signals
        self.menu_bar.actionAbout.triggered.connect(self.about)
        self.menu_bar.actionOpenLog.triggered.connect(self.open_log)
        self.menu_bar.actionReportIssue.triggered.connect(self.open_issues)
        self.menu_bar.actionSourceCode.triggered.connect(self.open_source)
        self.menu_bar.actionKillAllConfirmations.triggered.connect(self.killall)
        self.menu_bar.actionQuit.triggered.connect(self.quit)
        self.menu_bar.menuOptions.triggered.connect(self.update_settings)
        self.menu_bar.actionEnableIDTable.triggered.connect(self.update_stacked_widget)
        self.menu_bar.actionEnableIDTable.toggled.connect(self.toggle_table_settings)
        self.menu_bar.actionOpenSelectedIPs.triggered.connect(self.open_selected_ips)
        self.menu_bar.actionCopySelectedElements.triggered.connect(self.copy_selected)
        self.menu_bar.actionResetSort.triggered.connect(self.reset_sort)
        self.menu_bar.actionClearTable.triggered.connect(self.clear_table)
        self.menu_bar.actionImport.triggered.connect(self.import_table)
        self.menu_bar.actionExport.triggered.connect(self.export_table)
        self.menu_bar.actionShowPoolConfigurator.toggled.connect(
            self.toggle_pool_settings
        )
        self.menu_bar.actionGetMinerPoolConfig.triggered.connect(self.get_miner_pool)
        self.menu_bar.actionSetPoolFromPreset.triggered.connect(self.update_miner_pools)
        self.menu_bar.actionSettings.triggered.connect(
            lambda: self.update_stacked_widget(view_index=2)
        )
        self.menu_bar.actionDisableInactiveTimer.changed.connect(
            self.update_inactive_timer
        )

        # set logo
        self.labelLogo.setPixmap(QPixmap(":rc/img/scalable/BitCapIPRCenterLogo.svg"))

        # listener config
        for child in self.groupListeners.children():
            if isinstance(child, QWidget):
                child.setEnabled(True)
        self.groupListeners.toggled.connect(self.toggle_all_listeners)

        self.listenerConfig = QButtonGroup(exclusive=False)
        self.listenerConfig.addButton(self.checkListenAntminer, 1)
        self.listenerConfig.addButton(self.checkListenIceRiver, 2)
        self.listenerConfig.addButton(self.checkListenWhatsminer, 3)
        self.listenerConfig.addButton(self.checkListenVolcminer, 4)
        self.listenerConfig.addButton(self.checkListenGoldshell, 5)
        self.listenerConfig.addButton(self.checkListenSealminer, 6)
        self.listenerConfig.addButton(self.checkListenElphapex, 7)
        self.listenerConfig.buttonClicked.connect(self.restart_listen)
        # listener signals
        self.actionIPRStart.clicked.connect(self.start_listen)
        self.actionIPRStop.clicked.connect(self.stop_listen)

        self.poolConfigurator.hide()
        self.actionTogglePoolPasswd = self.create_passwd_toggle_action(
            self.linePoolPasswd
        )
        self.actionTogglePoolPasswd2 = self.create_passwd_toggle_action(
            self.linePoolPasswd_2
        )
        self.actionTogglePoolPasswd3 = self.create_passwd_toggle_action(
            self.linePoolPasswd_3
        )
        self.comboPoolPreset.currentIndexChanged.connect(self.read_pool_preset)
        self.comboPoolPreset.editTextChanged.connect(self.update_pool_preset)
        self.actionIPRSavePreset.clicked.connect(self.write_pool_preset)
        self.actionIPRClearPreset.clicked.connect(self.clear_pool_preset)

        # initialize ID Table
        self.idTable.setHorizontalHeaderLabels(
            [
                "",
                "IP",
                "MAC",
                "SERIAL",
                "TYPE",
                "SUBTYPE",
                "ALGORITHM",
                "POOL",
                "WORKER",
                "FIRMWARE",
                "PLATFORM",
            ]
        )
        self.idTable.setColumnWidth(0, 15)
        self.idTable.setColumnWidth(2, 120)
        self.idTable.setColumnWidth(3, 145)
        self.idTable.setColumnWidth(5, 130)
        self.idTable.setColumnWidth(7, 385)
        self.idTable.setColumnWidth(8, 300)
        self.idTable.setColumnWidth(9, 180)
        self.idTable.doubleClicked.connect(self.double_click_item)
        self.idTable.cellClicked.connect(self.locate_miner)
        self.idTable.setSortingEnabled(True)
        self.id_header = self.idTable.horizontalHeader()
        self.id_header.sectionDoubleClicked.connect(self.select_column)

        # id table context menu
        self.id_context_menu = IPRTableContextMenu()
        self.id_context_menu.contextActionOpenSelectedIPs.triggered.connect(
            self.open_selected_ips
        )
        self.id_context_menu.contextActionCopySelected.triggered.connect(
            self.copy_selected
        )
        self.id_context_menu.contextActionClearTable.triggered.connect(self.clear_table)
        self.id_context_menu.contextActionTableImport.triggered.connect(
            self.import_table
        )
        self.id_context_menu.contextActionTableExport.triggered.connect(
            self.export_table
        )
        self.id_context_menu.contextActionTableResetSortOrder.triggered.connect(
            self.reset_sort
        )
        self.id_context_menu.contextActionConfiguratorShowHide.toggled.connect(
            self.toggle_pool_config
        )
        self.id_context_menu.contextActionConfiguratorGetPool.triggered.connect(
            self.get_miner_pool
        )
        self.id_context_menu.contextActionConfiguratorSetPools.triggered.connect(
            self.update_miner_pools
        )
        self.idTable.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.idTable.customContextMenuRequested.connect(self.show_table_context)

        # read-only spinboxes
        self.spinLocateDuration.lineEdit().setReadOnly(True)
        self.spinInactiveTimeout.lineEdit().setReadOnly(True)

        # show/hide toggles for API passwords
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
        self.actionToggleVnishPasswd = self.create_passwd_toggle_action(
            self.lineVnishPasswd
        )

        # configuration control signals
        self.actionIPRCancelConfig.clicked.connect(self.update_stacked_widget)
        self.actionIPRSaveConfig.clicked.connect(self.update_settings)
        self.actionIPRResetConfig.clicked.connect(self.reset_settings)

        # status bar
        self.iprStatus.messageChanged.connect(self.update_status_msg)

        # system tray signals
        self.checkEnableSysTray.toggled.connect(self.update_sys_tray_settings)
        self.checkEnableSysTray.stateChanged.connect(self.create_or_destroy_systray)
        self.comboOnWindowClose.currentIndexChanged.connect(
            self.update_sys_tray_visibility
        )

        # configuration signals
        self.checkUseCustomTimeout.toggled.connect(self.update_inactive_timer_settings)
        self.spinInactiveTimeout.valueChanged.connect(self.update_inactive_timer)
        self.spinLocateDuration.valueChanged.connect(self.update_miner_locate_duration)
        self.comboLogLevel.currentIndexChanged.connect(self.set_logger_level)

        # set configuration
        self.read_settings()

        self.update_stacked_widget()
        self.update_status_msg()
        self.update_pool_preset_names()
        self.create_or_destroy_systray()

        if self.menu_bar.actionEnableIDTable.isChecked():
            self.toggle_table_settings(True)

        if self.menu_bar.actionShowPoolConfigurator.isChecked():
            self.toggle_pool_settings(True)

        if self.menu_bar.actionAutoStartOnLaunch.isChecked():
            self.start_listen()

    # logger
    def set_logger_level(self):
        logger.manager.root.setLevel(self.comboLogLevel.currentText())
        logger.log(
            logger.manager.root.level,
            f" change logger to level {self.comboLogLevel.currentText()}.",
        )

    # window
    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def update_stacked_widget(self, view_index: Optional[int] = None, *_):
        logger.info(" update view.")
        if not view_index:
            if self.menu_bar.actionShowPoolConfigurator.isChecked():
                self.poolConfigurator.setVisible(True)
            if self.menu_bar.actionEnableIDTable.isChecked():
                self.stackedWidget.setCurrentIndex(0)
            else:
                self.stackedWidget.setCurrentIndex(1)
        elif view_index < self.stackedWidget.count():
            if self.sys_tray and not self.isVisible():
                self.toggle_visibility()
            if self.menu_bar.actionShowPoolConfigurator.isChecked():
                if view_index == 2:
                    self.poolConfigurator.setVisible(False)
            self.stackedWidget.setCurrentIndex(view_index)

    def update_status_msg(self):
        if self.lm.listeners and not self.iprStatus.currentMessage():
            self.iprStatus.showMessage(
                f"Status :: UDP listening on 0.0.0.0[{self.active_miners}]..."
            )
        if not self.iprStatus.currentMessage():
            self.iprStatus.showMessage("Status :: Ready.")

    def update_pool_preset_names(self):
        for idx in range(1, len(self.config["savedPools"])):
            self.comboPoolPreset.setItemText(
                idx, self.config["savedPools"][idx]["preset_name"]
            )

    # system tray
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
            self.system_tray_menu.addAction(
                "Settings", lambda: self.update_stacked_widget(view_index=2)
            )
            self.system_tray_menu.addAction("Quit", self.quit)
            if self.lm.listeners:
                self.actionSysStartListen.setEnabled(False)
                self.actionSysStopListen.setEnabled(True)
            self.sys_tray.setContextMenu(self.system_tray_menu)
            self.sys_tray.setToolTip("BitCap IPR")
        else:
            if self.sys_tray:
                self.sys_tray.hide()
            self.sys_tray = None

    def update_sys_tray_visibility(self, current_index: int):
        if self.sys_tray:
            match current_index:
                case 0:  # minimize to tray
                    if self.sys_tray.isVisible():
                        self.sys_tray.hide()
                case 1:  # close
                    if not self.sys_tray.isVisible():
                        self.sys_tray.show()

    # configuration
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
            self.checkUseCustomTimeout.setChecked(
                self.config["general"]["useCustomTimeout"]
            )
            self.spinInactiveTimeout.setValue(
                self.config["general"]["inactiveTimeoutMins"]
            )

            # listeners
            self.groupListeners.setChecked(self.config["general"]["enableAllListeners"])
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
            self.checkListenElphapex.setChecked(
                self.config["general"]["listenFor"]["additional"]["elphapex"]
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

            # pools
            self.comboPoolPreset.setCurrentIndex(self.config["selectedPoolPreset"])
            preset_idx = self.comboPoolPreset.currentIndex()
            self.linePoolURL.setText(self.config["savedPools"][preset_idx]["pool"])
            self.linePoolURL_2.setText(self.config["savedPools"][preset_idx]["pool2"])
            self.linePoolURL_3.setText(self.config["savedPools"][preset_idx]["pool3"])
            self.linePoolUser.setText(self.config["savedPools"][preset_idx]["user"])
            self.linePoolUser_2.setText(self.config["savedPools"][preset_idx]["user2"])
            self.linePoolUser_3.setText(self.config["savedPools"][preset_idx]["user3"])
            self.linePoolPasswd.setText(self.config["savedPools"][preset_idx]["passwd"])
            self.linePoolPasswd_2.setText(
                self.config["savedPools"][preset_idx]["passwd2"]
            )
            self.linePoolPasswd_3.setText(
                self.config["savedPools"][preset_idx]["passwd3"]
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
            self.menu_bar.actionClearTableAfterStopListen.setChecked(
                self.config["instance"]["options"]["clearTableAfterStopListen"]
            )
            self.menu_bar.actionEnableIDTable.setChecked(
                self.config["instance"]["table"]["enableIDTable"]
            )
            self.menu_bar.actionShowPoolConfigurator.setChecked(
                self.config["instance"]["pools"]["enablePoolConfigurator"]
            )
            self.checkAutomaticWorkerNames.setChecked(
                self.config["instance"]["pools"]["automaticWorkerNames"]
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
                "clearTableAfterStopListen": self.menu_bar.actionClearTableAfterStopListen.isChecked(),
            },
            "table": {"enableIDTable": self.menu_bar.actionEnableIDTable.isChecked()},
            "pools": {
                "enablePoolConfigurator": self.menu_bar.actionShowPoolConfigurator.isChecked(),
                "automaticWorkerNames": self.checkAutomaticWorkerNames.isChecked(),
            },
        }
        savedPools = self.update_current_preset_to_config()
        config = {
            "general": {
                "enableSysTray": self.checkEnableSysTray.isChecked(),
                "onWindowClose": self.comboOnWindowClose.currentIndex(),
                "useCustomTimeout": self.checkUseCustomTimeout.isChecked(),
                "inactiveTimeoutMins": self.spinInactiveTimeout.value(),
                "enableAllListeners": self.groupListeners.isChecked(),
                "listenFor": {
                    "antminer": self.checkListenAntminer.isChecked(),
                    "whatsminer": self.checkListenWhatsminer.isChecked(),
                    "iceriver": self.checkListenIceRiver.isChecked(),
                    "additional": {
                        "volcminer": self.checkListenVolcminer.isChecked(),
                        "goldshell": self.checkListenGoldshell.isChecked(),
                        "sealminer": self.checkListenSealminer.isChecked(),
                        "elphapex": self.checkListenElphapex.isChecked(),
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
            "selectedPoolPreset": self.comboPoolPreset.currentIndex(),
            "savedPools": savedPools,
            "instance": instance,
        }
        self.config = config
        # update view from configuration
        if self.stackedWidget.currentIndex() == 2:
            self.update_stacked_widget()
        self.iprStatus.showMessage("Status :: Updated settings to config.", 1000)

    def write_settings(self):
        self.update_settings()
        write_config(self.config_path, self.config)

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
            self.toggle_pool_config()
            self.read_settings()
            self.update_inactive_timer()
            self.update_miner_locate_duration()
            self.create_or_destroy_systray()
            self.update_stacked_widget()
            self.iprStatus.showMessage(
                "Status :: Successfully restored to default settings.", 5000
            )

    def update_current_preset_to_config(self) -> List[Dict[str, str]]:
        savedPools = self.config["savedPools"]
        current_index = self.comboPoolPreset.currentIndex()
        savedPools[current_index]["preset_name"] = self.comboPoolPreset.currentText()
        savedPools[current_index]["pool"] = self.linePoolURL.text()
        savedPools[current_index]["pool2"] = self.linePoolURL_2.text()
        savedPools[current_index]["pool3"] = self.linePoolURL_3.text()
        savedPools[current_index]["user"] = self.linePoolUser.text()
        savedPools[current_index]["user2"] = self.linePoolUser_2.text()
        savedPools[current_index]["user3"] = self.linePoolUser_3.text()
        savedPools[current_index]["passwd"] = self.linePoolPasswd.text()
        savedPools[current_index]["passwd2"] = self.linePoolPasswd_2.text()
        savedPools[current_index]["passwd3"] = self.linePoolPasswd_3.text()
        return savedPools

    def update_pool_preset(self, preset_name: str):
        current_index = self.comboPoolPreset.currentIndex()
        if current_index != 0:
            self.comboPoolPreset.setItemText(current_index, preset_name)
            if self.comboPoolPreset.currentText() == "":
                self.comboPoolPreset.setItemText(
                    current_index,
                    self.config["savedPools"][current_index]["preset_name"],
                )

    def read_pool_preset(self, index: int) -> None:
        self.config = read_config(self.config_path)
        pool_preset = self.config["savedPools"][index]
        self.linePoolURL.setText(pool_preset["pool"])
        self.linePoolURL_2.setText(pool_preset["pool2"])
        self.linePoolURL_3.setText(pool_preset["pool3"])
        self.linePoolUser.setText(pool_preset["user"])
        self.linePoolUser_2.setText(pool_preset["user2"])
        self.linePoolUser_3.setText(pool_preset["user3"])
        self.linePoolPasswd.setText(pool_preset["passwd"])
        self.linePoolPasswd_2.setText(pool_preset["passwd2"])
        self.linePoolPasswd_3.setText(pool_preset["passwd3"])

    def write_pool_preset(self):
        current_index = self.comboPoolPreset.currentIndex()
        self.config["savedPools"][current_index]["preset_name"] = (
            self.comboPoolPreset.currentText()
        )
        self.config["savedPools"][current_index]["pool"] = self.linePoolURL.text()
        self.config["savedPools"][current_index]["pool2"] = self.linePoolURL_2.text()
        self.config["savedPools"][current_index]["pool3"] = self.linePoolURL_3.text()
        self.config["savedPools"][current_index]["user"] = self.linePoolUser.text()
        self.config["savedPools"][current_index]["user2"] = self.linePoolUser_2.text()
        self.config["savedPools"][current_index]["user3"] = self.linePoolUser_3.text()
        self.config["savedPools"][current_index]["passwd"] = self.linePoolPasswd.text()
        self.config["savedPools"][current_index]["passwd2"] = (
            self.linePoolPasswd_2.text()
        )
        self.config["savedPools"][current_index]["passwd3"] = (
            self.linePoolPasswd_3.text()
        )
        write_config(self.config_path, self.config)
        self.iprStatus.showMessage("Status :: successfully wrote pool preset.", 3000)

    def clear_pool_preset(self):
        current_index = self.comboPoolPreset.currentIndex()
        if current_index != 0:
            self.update_pool_preset(preset_name=f"Saved Pool {current_index + 1}")
        for child in self.pcwrapper.children():
            if isinstance(child, QWidget):
                for line in child.children():
                    if isinstance(line, QLineEdit):
                        line.setText("")

    def update_inactive_timer(self):
        self.groupInactiveTimer.setEnabled(
            not self.menu_bar.actionDisableInactiveTimer.isChecked()
        )
        if self.groupInactiveTimer.isEnabled():
            inactiveDuration = self.spinInactiveTimeout.value() * 60 * 1000
            self.inactive.setInterval(inactiveDuration)
            logger.info(f" update inactive timer duration: {inactiveDuration}ms")
        self.restart_listen()

    def update_miner_locate_duration(self):
        self.miner_locate_duration = self.spinLocateDuration.value() * 1000
        api_settings.update("locate_duration_ms", self.miner_locate_duration)
        logger.info(f" update miner locate duration: {self.miner_locate_duration}ms.")

    def update_inactive_timer_settings(self):
        if self.checkUseCustomTimeout.isChecked():
            self.spinInactiveTimeout.setEnabled(True)
        else:
            self.spinInactiveTimeout.setValue(self.spinInactiveTimeout.minimum())
            self.spinInactiveTimeout.setEnabled(False)

    def update_sys_tray_settings(self):
        if self.checkEnableSysTray.isChecked():
            self.comboOnWindowClose.setEnabled(True)
        else:
            self.comboOnWindowClose.setCurrentIndex(0)
            self.comboOnWindowClose.setEnabled(False)

    def toggle_table_settings(self, enabled: bool):
        self.menu_bar.actionOpenSelectedIPs.setEnabled(enabled)
        self.menu_bar.actionCopySelectedElements.setEnabled(enabled)
        self.menu_bar.menuTableAction.setEnabled(enabled)
        self.menu_bar.actionResetSort.setEnabled(enabled)
        self.menu_bar.actionClearTable.setEnabled(enabled)
        self.menu_bar.actionResetSort.setEnabled(enabled)
        self.menu_bar.actionImport.setEnabled(enabled)
        self.menu_bar.actionExport.setEnabled(enabled)
        if not enabled:
            self.menu_bar.actionShowPoolConfigurator.setChecked(enabled)
        self.menu_bar.actionShowPoolConfigurator.setEnabled(enabled)

    def toggle_pool_settings(self, enabled: bool):
        self.menu_bar.actionGetMinerPoolConfig.setEnabled(enabled)
        self.menu_bar.actionSetPoolFromPreset.setEnabled(enabled)
        self.toggle_pool_config(enabled)

    def toggle_all_listeners(self, enabled: bool):
        for button in self.listenerConfig.buttons():
            button.setChecked(enabled)
        if not enabled:
            for child in self.groupListeners.children():
                if isinstance(child, QWidget):
                    child.setEnabled(True)

    # actions
    def create_passwd_toggle_action(self, line: QLineEdit) -> QAction:
        passwd_action = line.addAction(
            QIcon(":theme/icons/rc/view.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        passwd_action.setToolTip("Show/Hide password")
        passwd_action.triggered.connect(
            lambda: self.toggle_show_passwd(line, passwd_action)
        )
        return passwd_action

    def toggle_show_passwd(self, line: QLineEdit, action: QAction):
        if line.echoMode() == QLineEdit.EchoMode.Password:
            line.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(QIcon(":theme/icons/rc/hide.png"))
        elif line.echoMode() == QLineEdit.EchoMode.Normal:
            line.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(QIcon(":theme/icons/rc/view.png"))

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

    def open_dashboard(self, host: str):
        webbrowser.open(f"http://{host}", new=2)

    def show_table_context(self):
        self.id_context_menu.exec(QCursor.pos())

    def double_click_item(self, model_index: QModelIndex):
        item = self.idTable.itemFromIndex(model_index)
        match item.column():
            case 1:  # ip column
                self.open_dashboard(item.text())
            case 3:  # serial column
                self.idTable.editItem(item)
            case _:
                return

    def get_selected_indexes_for_action(
        self, action: str, section: Optional[int] = None
    ) -> Optional[List[QModelIndex]]:
        rows = self.idTable.rowCount()
        if not rows:
            return
        if section is not None and section != 0:
            selected = [
                x for x in self.idTable.selectedIndexes() if x.column() == section
            ]
        else:
            selected = self.idTable.selectedIndexes()
        if not len(selected):
            return
        selected_text = [self.idTable.itemFromIndex(x).text() for x in selected]
        logger.info(f"{action} : running action for {selected_text}...")
        status_msg = f"Status :: Running action: {action} for [{','.join(selected_text[0:3])}...]..."
        self.iprStatus.showMessage(status_msg, 3000)
        return selected

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
            for index in range(len(selected_indexes_in_row)):
                sep = ""
                if len(selected_indexes_in_row) > 1:
                    sep = ","
                if not self.idTable.itemFromIndex(selected_indexes_in_row[index]):
                    continue
                item = self.idTable.itemFromIndex(selected_indexes_in_row[index])
                match item.column():
                    case 0:  # ignore locate
                        continue
                    case 1:  # ip
                        out += f"http://{item.text()}{sep}"
                    case _:
                        out += f"{item.text()}{sep}"
                continue
            out += "\n"
        logger.info("copy_selected : copy elements to clipboard.")
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(out.strip(), mode=cb.Mode.Clipboard)
        self.iprStatus.showMessage("Status :: Copied elements to clipboard.", 3000)

    def select_column(self, section: int):
        rows = self.idTable.rowCount()
        if not rows:
            return
        if section != 0:
            for row in range(rows):
                item = self.idTable.item(row, section)
                item.setSelected(True)

    def reset_sort(self):
        self.idTable.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.id_header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

    def clear_table(self):
        return self.idTable.setRowCount(0)

    def import_table(self):
        logger.info(" import table.")
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open .CSV",
            Path(Path.home(), "Documents", "ipr").resolve().__str__(),
            ".CSV Files (*.csv)",
        )
        self.clear_table()
        self.reset_sort()
        csv = QFile(file_name)
        if csv.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            data_stream = QTextStream(csv)
            header_line = data_stream.readLine()
            included_headers = [x.strip().lower() for x in header_line.split(",")]
            data_stream.seek(len(header_line) + 1)
            while not data_stream.atEnd():
                line = data_stream.readLine()
                if line:
                    row = deep_update(
                        self.api_client.target_info.copy(),
                        dict(zip(included_headers, line.split(","))),
                    )
                    self.populate_table_row(row)
        else:
            logger.error(f"import_table : failed to read file {file_name}.")
            self.iprStatus.showMessage("Status :: Failed to import table.", 5000)
            return

    def export_table(self):
        logger.info("export table.")
        rows = self.idTable.rowCount()
        cols = self.idTable.columnCount()
        if not rows:
            return
        out = "IP,MAC,SERIAL,TYPE,SUBTYPE,ALGORITHM,POOL,WORKER,FIRMWARE,PLATFORM\n"
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

    def toggle_pool_config(self, enabled: bool = False):
        self.menu_bar.actionShowPoolConfigurator.setChecked(enabled)
        self.id_context_menu.contextActionConfiguratorShowHide.setChecked(enabled)
        self.id_context_menu.contextActionConfiguratorGetPool.setEnabled(enabled)
        self.id_context_menu.contextActionConfiguratorSetPools.setEnabled(enabled)
        self.poolConfigurator.setVisible(enabled)
        if self.menu_bar.actionShowPoolConfigurator.isChecked():
            self.setGeometry(self.x(), self.y(), self.width(), self.maximumHeight())
        else:
            self.setGeometry(
                self.x(),
                self.y(),
                self.width(),
                self.config["instance"]["geometry"]["mainWindow"][3],
            )

    # listener
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

    def stop_listen(self, timeout: bool = False, restart: bool = False):
        logger.info(" stop listeners.")
        self.inactive.stop()
        if self.sys_tray:
            self.actionSysStartListen.setEnabled(True)
            self.actionSysStopListen.setEnabled(False)
        if (
            self.menu_bar.actionEnableIDTable.isChecked()
            and self.menu_bar.actionClearTableAfterStopListen.isChecked()
        ):
            self.clear_table()
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
            self.stop_listen(restart=True)
            self.start_listen()

    def process_result(self, result: List[str]):
        # reset inactive timer
        if self.inactive.isActive():
            self.inactive.start()
        ip, mac, type, sn = result
        logger.debug(f"process_result : got {ip},{mac},{sn},{type} from listener.")
        if type == "bitmain-common":
            bitmain_common_miners = [
                self.checkListenAntminer,
                self.checkListenVolcminer,
            ]
            enabled_common_filter = [
                btn.text().lower() for btn in bitmain_common_miners if btn.isChecked()
            ]
            for miner in bitmain_common_miners:
                match miner.text().lower():
                    case "antminer":
                        self.api_client.create_bitmain_client(
                            ip,
                            self.lineBitmainPasswd.text(),
                            self.lineVnishPasswd.text(),
                        )
                        if (
                            not self.api_client.client
                            or not self.api_client.is_antminer()
                        ):
                            continue
                        type = "antminer"
                        self.api_client.close_client()
                        break
                    case "volcminer":
                        self.api_client.create_volcminer_client(
                            ip, self.lineVolcminerPasswd.text()
                        )
                        if (
                            not self.api_client.client
                            or not self.api_client.is_volcminer()
                        ):
                            continue
                        type = "volcminer"
                        self.api_client.close_client()
                        break
            # workaround: check all listeners to accept unknown types
            if (
                type not in enabled_common_filter
                and not self.groupListeners.isChecked()
            ):
                logger.warning(
                    f"process_result : recieved miner type {type} outside of filter: {enabled_common_filter}. Ignoring..."
                )
                self.iprStatus.showMessage(
                    f"Status :: Got miner type: {type.capitalize()} outside of listener configuration.",
                    8000,
                )
                return
            elif type == "bitmain-common":
                type = "Unknown"
        # get missing mac addr
        match type:
            case "iceriver":
                self.api_client.create_iceriver_client(ip, None)
            case "elphapex":
                self.api_client.create_elphapex_client(ip, None)
        missing_mac = self.api_client.get_missing_mac_addr()
        self.api_client.close_client()
        if missing_mac:
            mac = missing_mac
        logger.info(f"process_result : got updated result {ip},{mac},{sn},{type}.")
        self.iprStatus.showMessage(f"Status :: Got {type}: IP:{ip}, MAC:{mac}", 5000)
        self.result: Dict[str, str] = {
            "ip": ip,
            "mac": mac.upper(),
            "type": type,
            "sn": sn,
            **self.api_client.target_info,
        }
        self.show_confirmation()

    # ip confirmation
    def show_confirmation(self):
        logger.info(" show IP confirmation.")
        ip = self.result["ip"]
        mac = self.result["mac"]
        type = self.result["type"]
        if self.menu_bar.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip)
        if self.menu_bar.actionEnableIDTable.isChecked() and self.isVisible():
            logger.info("show_confirmation : populate ID table.")
            self.populate_id_table()
        else:
            confirm = IPRConfirmation(self)
            # IPRConfirmation Signals
            confirm.accept.clicked.connect(confirm.hide)
            confirm.lineIPField.actionDashboard.triggered.connect(
                lambda: self.open_dashboard(ip)
            )

            logger.info("show_confirmation : show IPRConfirmation.")
            confirm.lineIPField.setText(ip)
            confirm.lineMACField.setText(mac)
            confirm.lineASICField.setText(type)
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
                confirm.showNormal()
                confirm.activateWindow()
                confirm.raise_()

    def show_confirm_from_sys_tray(self, confirm: IPRConfirmation):
        confirm.showNormal()
        confirm.activateWindow()
        confirm.raise_()
        self.sys_tray.messageClicked.disconnect()

    # ID table
    def populate_id_table(self) -> None:
        sn = self.result["sn"]
        target_data = self.get_target_data_from_type()
        self.result.update(target_data)
        if sn:
            self.result["serial"] = sn
        self.populate_table_row()
        self.activateWindow()

    def get_client_auth_from_type(
        self, miner_type: str
    ) -> Tuple[Optional[str], Optional[str]]:
        client_auth: Optional[str] = None
        custom_auth: Optional[str] = None
        match miner_type:
            case "antminer":
                client_auth = self.lineBitmainPasswd.text()
                if not self.checkVnishUseAntminerLogin.isChecked():
                    custom_auth = self.lineVnishPasswd.text()
                else:
                    custom_auth = self.lineBitmainPasswd.text()
            case "whatsminer":
                client_auth = self.lineWhatsminerPasswd.text()
            case "goldshell":
                client_auth = self.lineGoldshellPasswd.text()
            case "volcminer":
                client_auth = self.lineVolcminerPasswd.text()
            case "sealminer":
                client_auth = self.lineSealminerPasswd.text()
        return client_auth, custom_auth

    def get_target_data_from_type(self) -> Dict[str, str]:
        ip = self.result["ip"]
        type = self.result["type"]
        client_auth, custom_auth = self.get_client_auth_from_type(type)
        self.api_client.create_client_from_type(type, ip, client_auth, custom_auth)
        if not self.api_client.client:
            self.iprStatus.showMessage(
                "Status :: Failed to connect or authenticate client.", 5000
            )
        logger.info(f"populate_table : get target data from ip {ip}.")
        t_data = self.api_client.get_target_data_from_type(type)
        self.api_client.close_client()
        return t_data

    def populate_table_row(self, data: Dict[str, str] = None) -> None:
        """
        arguments:
            **data: dict[str. str] -- row data with the following key structure:
                'ip', 'mac', 'serial', 'type', 'subtype', 'algoritmn', 'firmware', 'platform'
        """
        logger.info("populate_table : write table data.")
        if data:
            self.result = data
        rowPosition = self.idTable.rowCount()
        self.idTable.insertRow(rowPosition)
        actionLocateMiner = QLabel()
        actionLocateMiner.setPixmap(QPixmap(":theme/icons/rc/flash.png"))
        actionLocateMiner.setToolTip("Locate Miner")
        self.idTable.setCellWidget(rowPosition, 0, actionLocateMiner)
        self.idTable.setItem(rowPosition, 0, IPRIndexWidgetItem(rowPosition))
        self.idTable.setItem(rowPosition, 1, IPRIPWidgetItem(self.result["ip"]))
        self.idTable.setItem(rowPosition, 2, QTableWidgetItem(self.result["mac"]))
        self.idTable.setItem(rowPosition, 3, QTableWidgetItem(self.result["serial"]))
        # ASIC TYPE
        self.idTable.setItem(rowPosition, 4, QTableWidgetItem(self.result["type"]))
        # SUBTYPE
        self.idTable.setItem(rowPosition, 5, QTableWidgetItem(self.result["subtype"]))
        # ALGO
        self.idTable.setItem(rowPosition, 6, QTableWidgetItem(self.result["algorithm"]))
        # ACTIVE POOL
        self.idTable.setItem(rowPosition, 7, QTableWidgetItem(self.result["pool"]))
        # ACTIVE WORKER
        self.idTable.setItem(rowPosition, 8, QTableWidgetItem(self.result["worker"]))
        # FIRMWARE
        self.idTable.setItem(rowPosition, 9, QTableWidgetItem(self.result["firmware"]))
        # PLATFORM
        self.idTable.setItem(rowPosition, 10, QTableWidgetItem(self.result["platform"]))
        self.idTable.scrollToBottom()

    def locate_miner(self, row: int, col: int):
        if col == 0:
            miner_type = self.idTable.item(row, 4).text()
            ip_addr = self.idTable.item(row, 1).text()
            if self.api_client.locate and self.api_client.locate.isActive():
                return logger.warning(
                    "locate_miner : already locating a miner. Ignoring..."
                )
            logger.info(f" locate miner {ip_addr}.")
            match miner_type:
                case "volcminer":
                    # client_auth = self.lineVolcminerPasswd.text()
                    return self.iprStatus.showMessage(
                        "Status :: Failed to locate miner: VolcMiner is currently not supported.",
                        5000,
                    )
            client_auth, custom_auth = self.get_client_auth_from_type(miner_type)
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
                self.miner_locate_duration,
            )

    def get_miner_pool(self):
        rows = self.idTable.rowCount()
        if not rows:
            return
        selected_ips = [x for x in self.idTable.selectedIndexes() if x.column() == 1]
        index = selected_ips[0]
        item = self.idTable.itemFromIndex(index)
        miner_type = self.idTable.item(item.row(), 4).text()
        client_auth, custom_auth = self.get_client_auth_from_type(miner_type)
        self.api_client.create_client_from_type(
            miner_type, item.text(), client_auth, custom_auth
        )
        client = self.api_client.get_client()
        if not client:
            return
        urls, users, passwds = self.api_client.get_miner_pool_conf(miner_type)
        if client._error:
            return self.iprStatus.showMessage(
                f"Status :: Failed to get pool config: {client._error}", 5000
            )
        # set to "current" preset
        self.comboPoolPreset.setCurrentIndex(0)
        self.linePoolURL.setText(urls[0])
        self.linePoolUser.setText(users[0])
        self.linePoolPasswd.setText(passwds[0])
        self.linePoolURL_2.setText(urls[1])
        self.linePoolUser_2.setText(users[1])
        self.linePoolPasswd_2.setText(passwds[1])
        self.linePoolURL_3.setText(urls[2])
        self.linePoolUser_3.setText(users[2])
        self.linePoolPasswd_3.setText(passwds[2])
        self.write_pool_preset()
        self.iprStatus.showMessage(
            f"Status :: Updated {self.comboPoolPreset.currentText()} preset from {item.text()}.",
            3000,
        )

    def update_miner_pools(self):
        passed: List[str] = []
        failed: List[str] = []
        selected_ips = self.get_selected_indexes_for_action(
            "update_miner_pools", section=1
        )
        self._app_instance.processEvents(
            QEventLoop.ProcessEventsFlag.AllEvents
            | QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents
        )
        if selected_ips is None:
            return
        for index in selected_ips:
            item = self.idTable.itemFromIndex(index)
            ip_addr = item.text()
            miner_type = self.idTable.item(item.row(), 4).text()
            macaddr = self.idTable.item(item.row(), 2).text()
            serial = self.idTable.item(item.row(), 3).text()
            worker = ""
            if serial and (
                serial != "N/A" and serial != "Unknown" and serial != "Failed"
            ):
                worker = f".{serial[-5:]}"
            elif macaddr and (macaddr != "N/A" and macaddr != "Failed"):
                worker = f".{macaddr.replace(':', '')[-5:]}"
            client_auth, custom_auth = self.get_client_auth_from_type(miner_type)
            self.api_client.create_client_from_type(
                miner_type, ip_addr, client_auth, custom_auth
            )
            client = self.api_client.get_client()
            if not client:
                failed.append(ip_addr)
                continue
            urls = [
                self.linePoolURL.text(),
                self.linePoolURL_2.text(),
                self.linePoolURL_3.text(),
            ]
            users = [
                self.linePoolUser.text(),
                self.linePoolUser_2.text(),
                self.linePoolUser_3.text(),
            ]
            # append worker name
            if self.checkAutomaticWorkerNames.isChecked():
                if worker:
                    for idx in range(0, len(users)):
                        if users[idx]:
                            users[idx] = users[idx].split(".")[0] + worker
                else:
                    logger.warning(
                        "update_miner_pools : failed to find applicable worker name. Continuing.."
                    )

            passwds = [
                self.linePoolPasswd.text(),
                self.linePoolPasswd_2.text(),
                self.linePoolPasswd_3.text(),
            ]
            self.api_client.update_miner_pools(urls, users, passwds)
            if client._error:
                failed.append(ip_addr)
                continue
            self.api_client.close_client()
            passed.append(ip_addr)

        # action status
        logger.info(
            f"status for action 'update_miner_pools': passed - {passed}, failed - {failed}"
        )
        if len(failed) > 0:
            return self.iprStatus.showMessage(
                f"Status :: Failed to update pools for {failed}.", 5000
            )
        self.iprStatus.showMessage("Status :: Successfully updated pools.", 3000)

    # exit
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

    def close_root_logger(self, log: logging.Logger):
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
        del self
