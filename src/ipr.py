import logging
import os
import time
import webbrowser
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import TypeAdapter, ValidationError
from PySide6.QtCore import (
    QEventLoop,
    QFile,
    QIODevice,
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
from config import IPRConfig, PoolPreset
from iprabout import IPRAbout
from iprconfirmation import IPRConfirmation
from mod.apiv2 import ASICClient
from mod.apiv2 import settings as api_settings
from mod.lm import IPReport, ListenerManager
from ui.MainWindow import Ui_MainWindow
from ui.widgets import (
    IPR_Menubar,
    IPR_Titlebar,
    IPRIndexWidgetItem,
    IPRTableContextMenu,
)
from utils import (
    IPR_METADATA,
    deep_update,
    get_log_dir,
)

logger = logging.getLogger(__name__)


class IPR(QMainWindow, Ui_MainWindow):
    def __init__(self, stored: IPRConfig):
        logger.info(" start IPR() init.")
        super().__init__(flags=Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)
        self.config = stored
        self._app_instance = QApplication.instance()
        self.confirms: list[IPRConfirmation] = []
        self.aboutDialog: Optional[IPRAbout] = None
        self.sys_tray: QSystemTrayIcon = QSystemTrayIcon(
            QIcon(":rc/img/BitCapIPR_BLK-02_Square.png"),
            parent=self,
            toolTip="BitCap IPReporter",
            visible=False,
        )
        self.system_tray_context = QMenu(self)
        self.system_tray_context.addAction("Show/Hide", self.toggle_visibility)
        self.system_tray_context.addAction("Open Log", self.open_log)
        self.actionSysStartListen = self.system_tray_context.addAction(
            "Start Listen", self.start_listen
        )
        self.actionSysStopListen = self.system_tray_context.addAction(
            "Stop Listen", self.stop_listen
        )
        self.actionSysStopListen.setEnabled(False)
        self.system_tray_context.addSeparator()
        self.system_tray_context.addAction(
            "Settings", lambda: self.update_stacked_widget(view_index=2)
        )
        self.system_tray_context.addAction("Quit", self.quit)
        self.sys_tray.setContextMenu(self.system_tray_context)
        self.sys_tray.activated.connect(self.activate_system_tray)

        logger.info(" init inactive timer for 900000ms.")
        self.inactive = QTimer(self)
        self.inactive.setInterval(900000)
        self.inactive.timeout.connect(lambda: self.stop_listen(timeout=True))

        logger.info(" init mod lm.")
        self.lm = ListenerManager(self)
        self.lm.listen_complete.connect(self.process_result)
        # restart listeners on fail
        self.lm.listen_error.connect(self.restart_listen)

        logger.info(" init mod api.")
        self.asic = ASICClient(self)
        logger.info(" init miner locate duration for 10000ms.")
        self.miner_locate_duration: int = api_settings.get("locate_duration_ms")

        # initialize IPR_Titlebar widget
        self.title_bar = IPR_Titlebar(self, "BitCap IPReporter", ["min", "close"])
        self.title_bar.minimize_button.clicked.connect(self.window().showMinimized)
        self.title_bar.close_button.clicked.connect(self.close_to_tray_or_exit)
        title_bar_widget = self.titleBarWidget.layout()
        if title_bar_widget:
            title_bar_widget.addWidget(self.title_bar)

        # initialize IPR_Menubar widget
        self.menu_bar = IPR_Menubar(self)
        menu_bar_widget = self.menuBarWidget.layout()
        if menu_bar_widget:
            menu_bar_widget.addWidget(self.menu_bar)

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
        self.labelIPRLogo.setPixmap(QPixmap(":rc/img/scalable/BitCapIPRCenterLogo.svg"))

        # listener config
        for child in self.groupListeners.children():
            if isinstance(child, QWidget):
                child.setEnabled(True)
        self.groupListeners.toggled.connect(self.toggle_all_listeners)

        self.listenerConfig = QButtonGroup(self, exclusive=False)
        self.listenerConfig.addButton(self.checkListenAntminer, 1)
        self.listenerConfig.addButton(self.checkListenIceRiver, 2)
        self.listenerConfig.addButton(self.checkListenWhatsminer, 3)
        self.listenerConfig.addButton(self.checkListenVolcminer, 4)
        self.listenerConfig.addButton(self.checkListenHammer, 5)
        self.listenerConfig.addButton(self.checkListenGoldshell, 6)
        self.listenerConfig.addButton(self.checkListenSealminer, 7)
        self.listenerConfig.addButton(self.checkListenElphapex, 8)
        self.listenerConfig.buttonClicked.connect(self.restart_listen)
        # listener signals
        self.pushIPRListenStart.clicked.connect(self.start_listen)
        self.pushIPRListenStop.clicked.connect(self.stop_listen)

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
        self.tableIPRID.setHorizontalHeaderLabels(
            [
                "",
                "IP",
                "MAC",
                "TYPE",
                "SUBTYPE",
                "SERIAL",
                "ALGORITHM",
                "HOSTNAME",
                "STRATUM URL",
                "USERNAME",
                "WORKER NAME",
                "FIRMWARE",
                "FW VERSION",
                "PLATFORM",
            ]
        )
        self.tableIPRID.setColumnWidth(0, 15)
        self.tableIPRID.setColumnWidth(2, 120)
        self.tableIPRID.setColumnWidth(4, 130)
        self.tableIPRID.setColumnWidth(5, 145)
        self.tableIPRID.setColumnWidth(8, 385)
        self.tableIPRID.setColumnWidth(9, 300)
        self.tableIPRID.setColumnWidth(12, 180)
        self.tableIPRID.doubleClicked.connect(self.double_click_item)
        self.tableIPRID.cellClicked.connect(self.locate_miner)
        self.tableIPRID.setSortingEnabled(True)
        self.id_header = self.tableIPRID.horizontalHeader()
        self.id_header.sectionDoubleClicked.connect(self.select_column)

        # id table context menu
        self.id_context_menu = IPRTableContextMenu(self)
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
        self.tableIPRID.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableIPRID.customContextMenuRequested.connect(self.show_table_context)

        # read-only spinboxes
        self.spinLocateDuration.lineEdit().setReadOnly(True)
        self.spinInactiveTimeout.lineEdit().setReadOnly(True)

        # show/hide toggles for API passwords
        self.actionToggleAntminerPasswd = self.create_passwd_toggle_action(
            self.lineAntminerPasswd
        )
        self.actionToggleIceriverPasswd = self.create_passwd_toggle_action(
            self.lineIceriverPasswd
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
        self.actionToggleHammerPasswd = self.create_passwd_toggle_action(
            self.lineHammerPasswd
        )
        self.actionToggleSealminerPasswd = self.create_passwd_toggle_action(
            self.lineSealminerPasswd
        )
        self.actionToggleElphapexPasswd = self.create_passwd_toggle_action(
            self.lineElphapexPasswd
        )
        self.actionToggleVnishPasswd = self.create_passwd_toggle_action(
            self.lineVnishPasswd
        )

        # configuration control signals
        self.pushIPRCancelConfig.clicked.connect(self.update_stacked_widget)
        self.pushIPRSaveConfig.clicked.connect(self.update_settings)
        self.pushIPRResetConfig.clicked.connect(self.reset_settings)

        # status bar
        self.iprStatusBar.messageChanged.connect(self.update_status_msg)

        # system tray signals
        self.checkEnableSysTray.toggled.connect(self.toggle_system_tray_settings)
        self.checkEnableSysTray.stateChanged.connect(self.update_system_tray_visibility)

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

    def show_window(self):
        if self.isHidden() or self.isMinimized():
            self.showNormal()
            self.activate_window()
        else:
            self.activate_window()

    def activate_window(self):
        self.setWindowState(
            self.windowState() & ~Qt.WindowState.WindowMinimized
            | Qt.WindowState.WindowActive
        )
        self.raise_()
        self.activateWindow()

    def is_minimized_to_tray(self) -> bool:
        if self.sys_tray.isVisible() and not self.isVisible():
            return True
        return False

    def update_stacked_widget(self, view_index: Optional[int] = None, *_):
        logger.info(" update view.")
        if not view_index:
            if self.menu_bar.actionShowPoolConfigurator.isChecked():
                self.poolConfigurator.setVisible(True)
            if self.menu_bar.actionEnableIDTable.isChecked():
                self.stackedWidget.setCurrentIndex(1)
            else:
                self.stackedWidget.setCurrentIndex(0)
        elif view_index < self.stackedWidget.count():
            if self.is_minimized_to_tray():
                self.toggle_visibility()
            if self.menu_bar.actionShowPoolConfigurator.isChecked():
                if view_index == 2:
                    self.poolConfigurator.setVisible(False)
            self.stackedWidget.setCurrentIndex(view_index)

    def update_status_msg(self):
        if self.lm.count and not self.iprStatusBar.currentMessage():
            self.iprStatusBar.showMessage(
                f"Status :: UDP listening on 0.0.0.0[{self.lm.status}]..."
            )
        if not self.iprStatusBar.currentMessage():
            self.iprStatusBar.showMessage("Status :: Ready.")

    def update_pool_preset_names(self):
        for idx in range(1, len(self.config.pool_config.pool_presets)):
            self.comboPoolPreset.setItemText(
                idx, self.config.pool_config.pool_presets[idx].preset_name
            )

    # system tray
    def activate_system_tray(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self.show_window()

    def update_system_tray_visibility(self):
        if self.checkEnableSysTray.isChecked():
            self.sys_tray.show()
        else:
            self.sys_tray.hide()

    # configuration
    def read_settings(self):
        logger.info(" read settings.")
        # general
        self.checkEnableSysTray.setChecked(self.config.general.enable_sys_tray)
        self.comboOnWindowClose.setCurrentIndex(self.config.general.on_close)
        self.checkUseCustomTimeout.setChecked(self.config.general.use_custom_timeout)
        self.spinInactiveTimeout.setValue(self.config.general.inactive_timeout)

        # listener
        self.groupListeners.setChecked(self.config.listener.enable_all)
        self.checkListenAntminer.setChecked(self.config.listen_for.antminer)
        self.checkListenWhatsminer.setChecked(self.config.listen_for.whatsminer)
        self.checkListenIceRiver.setChecked(self.config.listen_for.iceriver)
        self.checkListenHammer.setChecked(self.config.listen_for.hammer)
        self.checkListenVolcminer.setChecked(self.config.listen_for.volcminer)
        self.checkListenGoldshell.setChecked(self.config.listen_for.goldshell)
        self.checkListenSealminer.setChecked(self.config.listen_for.sealminer)
        self.checkListenElphapex.setChecked(self.config.listen_for.elphapex)

        # api
        self.lineAntminerPasswd.setText(self.config.api.auth.antminer_alt_passwd)
        self.lineIceriverPasswd.setText(self.config.api.auth.iceriver_alt_passwd)
        self.lineWhatsminerPasswd.setText(self.config.api.auth.whatsminer_alt_passwd)
        self.lineHammerPasswd.setText(self.config.api.auth.hammer_alt_passwd)
        self.lineVolcminerPasswd.setText(self.config.api.auth.volcminer_alt_passwd)
        self.lineGoldshellPasswd.setText(self.config.api.auth.goldshell_alt_passwd)
        self.lineElphapexPasswd.setText(self.config.api.auth.elphapex_alt_passwd)
        self.lineVnishPasswd.setText(self.config.api.firmware.vnish_alt_passwd)

        # api settings
        self.spinLocateDuration.setValue(self.config.api.locate_duration)
        self.checkUseAntminerLogin.setChecked(
            self.config.api.firmware.use_antminer_login
        )

        # logs
        self.comboLogLevel.setCurrentText(self.config.logs.log_level)
        self.spinMaxLogSize.setValue(self.config.logs.max_log_size)
        self.comboOnMaxLogSize.setCurrentIndex(self.config.logs.on_max_log_size)
        self.checkFlushOnClose.setChecked(self.config.logs.flush_on_close)

        # pools
        self.comboPoolPreset.setCurrentIndex(self.config.pool_config.selected_preset)
        self.checkAutomaticWorkerNames.setChecked(
            self.config.pool_config.auto_set_workers
        )
        preset_idx = self.comboPoolPreset.currentIndex()
        self.linePoolURL.setText(self.config.pool_config.pool_presets[preset_idx].pool1)
        self.linePoolURL_2.setText(
            self.config.pool_config.pool_presets[preset_idx].pool2
        )
        self.linePoolURL_3.setText(
            self.config.pool_config.pool_presets[preset_idx].pool3
        )
        self.linePoolUser.setText(
            self.config.pool_config.pool_presets[preset_idx].user1
        )
        self.linePoolUser_2.setText(
            self.config.pool_config.pool_presets[preset_idx].user2
        )
        self.linePoolUser_3.setText(
            self.config.pool_config.pool_presets[preset_idx].user3
        )
        self.linePoolPasswd.setText(
            self.config.pool_config.pool_presets[preset_idx].passwd1
        )
        self.linePoolPasswd_2.setText(
            self.config.pool_config.pool_presets[preset_idx].passwd2
        )
        self.linePoolPasswd_3.setText(
            self.config.pool_config.pool_presets[preset_idx].passwd3
        )

        # instance
        window_geometry = self.config.instance.geometry
        if window_geometry:
            self.setGeometry(*window_geometry)

        self.menu_bar.actionAlwaysOpenIPInBrowser.setChecked(
            self.config.instance.options.always_open_ip
        )
        self.menu_bar.actionDisableInactiveTimer.setChecked(
            self.config.instance.options.disable_inactive
        )
        self.menu_bar.actionConfirmsStayOnTop.setChecked(
            self.config.instance.options.confirms_on_top
        )
        self.menu_bar.actionAutoStartOnLaunch.setChecked(
            self.config.instance.options.auto_start
        )
        self.menu_bar.actionClearTableAfterStopListen.setChecked(
            self.config.instance.options.clear_table_on_stop
        )
        self.menu_bar.actionEnableIDTable.setChecked(
            self.config.instance.views.show_table
        )
        self.menu_bar.actionShowPoolConfigurator.setChecked(
            self.config.instance.views.show_pool_conf
        )

    def update_settings(self):
        logger.info(" update settings.")
        settings = self.config.dict
        settings["instance"] = {
            "geometry": [
                self.geometry().x(),
                self.geometry().y(),
                self.geometry().width(),
                self.geometry().height(),
            ],
            "options": {
                "alwaysOpenIP": self.menu_bar.actionAlwaysOpenIPInBrowser.isChecked(),
                "disableInactiveTimer": self.menu_bar.actionDisableInactiveTimer.isChecked(),
                "autoStartOnLaunch": self.menu_bar.actionAutoStartOnLaunch.isChecked(),
                "clearTableOnStop": self.menu_bar.actionClearTableAfterStopListen.isChecked(),
                "confirmsStayOnTop": self.menu_bar.actionConfirmsStayOnTop.isChecked(),
            },
            "views": {
                "showIDTable": self.menu_bar.actionEnableIDTable.isChecked(),
                "showPoolConfigurator": self.menu_bar.actionShowPoolConfigurator.isChecked(),
            },
        }
        settings["general"] = {
            "enableSystemTray": self.checkEnableSysTray.isChecked(),
            "onWindowClose": self.comboOnWindowClose.currentIndex(),
            "useCustomTimeout": self.checkUseCustomTimeout.isChecked(),
            "inactiveTimeoutMins": self.spinInactiveTimeout.value(),
        }
        settings["listener"] = {
            "enableFiltering": self.checkEnableListenFilter.isChecked(),
            "enableAll": self.groupListeners.isChecked(),
            "listenFor": {
                "antminer": self.checkListenAntminer.isChecked(),
                "whatsminer": self.checkListenWhatsminer.isChecked(),
                "iceriver": self.checkListenIceRiver.isChecked(),
                "hammer": self.checkListenHammer.isChecked(),
                "volcminer": self.checkListenVolcminer.isChecked(),
                "goldshell": self.checkListenGoldshell.isChecked(),
                "sealminer": self.checkListenSealminer.isChecked(),
                "elphapex": self.checkListenElphapex.isChecked(),
            },
        }
        settings["api"] = {
            "locateDuration": self.spinLocateDuration.value(),
            "auth": {
                "antminerAltPasswd": self.lineAntminerPasswd.text(),
                "iceriverAltPasswd": self.lineIceriverPasswd.text(),
                "whatsminerAltPasswd": self.lineWhatsminerPasswd.text(),
                "goldshellAltPasswd": self.lineGoldshellPasswd.text(),
                "hammerAltPasswd": self.lineHammerPasswd.text(),
                "volcminerAltPasswd": self.lineVolcminerPasswd.text(),
                "elphapexAltPasswd": self.lineElphapexPasswd.text(),
                "sealminerAltPasswd": self.lineSealminerPasswd.text(),
            },
            "firmware": {
                "useAntminerLogin": self.checkUseAntminerLogin.isChecked(),
                "vnishAltPasswd": self.lineVnishPasswd.text(),
            },
        }
        pool_presets = self.update_current_preset_to_config()
        settings["poolConfigurator"] = {
            "autoSetWorkers": self.checkAutomaticWorkerNames.isChecked(),
            "selectedPoolPreset": self.comboPoolPreset.currentIndex(),
            "poolPresets": pool_presets,
        }
        settings["logs"] = {
            "logLevel": self.comboLogLevel.currentText(),
            "flushOnClose": self.checkFlushOnClose.isChecked(),
            "maxLogSize": self.spinMaxLogSize.value(),
            "onMaxLogSize": self.comboOnMaxLogSize.currentIndex(),
        }
        # update view from configuration
        if self.stackedWidget.currentIndex() == 2:
            self.update_stacked_widget()
        try:
            self.config.validate(settings)
        except ValidationError as exc:
            logger.error(
                f"update_settings: failed to validate config model.\n{exc.__repr__()}"
            )
            self.iprStatusBar.showMessage(
                "Status :: Failed to update configuration!", 5000
            )
            return

        self.iprStatusBar.showMessage("Status :: Updated settings to config.", 1000)

    def write_settings(self):
        self.update_settings()
        self.config.write()

    def reset_settings(self):
        ok = QMessageBox.warning(
            self,
            "Confirm Reset Settings",
            "Are you sure you want to reset configuration to default?",
            buttons=QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
        )
        if ok == QMessageBox.StandardButton.Ok:
            logger.info(" reset settings.")
            self.config.write_default()
            self.toggle_pool_config()
            self.read_settings()
            self.update_inactive_timer()
            self.update_miner_locate_duration()
            self.update_stacked_widget()
            self.iprStatusBar.showMessage(
                "Status :: Successfully restored to default settings.", 5000
            )

    def update_current_preset_to_config(self) -> list[Dict[str, str]]:
        presets = TypeAdapter(list[PoolPreset])
        savedPools: list[Dict[str, str]] = presets.dump_python(
            self.config.pool_config.pool_presets, by_alias=True
        )
        current_index = self.comboPoolPreset.currentIndex()
        savedPools[current_index]["preset_name"] = self.comboPoolPreset.currentText()
        savedPools[current_index]["pool1"] = self.linePoolURL.text()
        savedPools[current_index]["pool2"] = self.linePoolURL_2.text()
        savedPools[current_index]["pool3"] = self.linePoolURL_3.text()
        savedPools[current_index]["user1"] = self.linePoolUser.text()
        savedPools[current_index]["user2"] = self.linePoolUser_2.text()
        savedPools[current_index]["user3"] = self.linePoolUser_3.text()
        savedPools[current_index]["passwd1"] = self.linePoolPasswd.text()
        savedPools[current_index]["passwd2"] = self.linePoolPasswd_2.text()
        savedPools[current_index]["passwd3"] = self.linePoolPasswd_3.text()
        return savedPools

    def update_pool_preset(self, preset_name: str):
        current_index = self.comboPoolPreset.currentIndex()
        self.comboPoolPreset.setItemText(current_index, preset_name)

    def read_pool_preset(self, index: int) -> None:
        self.config.read()
        pool_preset = self.config.pool_config.pool_presets[index]
        self.linePoolURL.setText(pool_preset.pool1)
        self.linePoolURL_2.setText(pool_preset.pool2)
        self.linePoolURL_3.setText(pool_preset.pool3)
        self.linePoolUser.setText(pool_preset.user1)
        self.linePoolUser_2.setText(pool_preset.user2)
        self.linePoolUser_3.setText(pool_preset.user3)
        self.linePoolPasswd.setText(pool_preset.passwd1)
        self.linePoolPasswd_2.setText(pool_preset.passwd2)
        self.linePoolPasswd_3.setText(pool_preset.passwd3)

    def write_pool_preset(self):
        current_index = self.comboPoolPreset.currentIndex()
        self.config.pool_config.pool_presets[
            current_index
        ].preset_name = self.comboPoolPreset.currentText()
        self.config.pool_config.pool_presets[
            current_index
        ].pool1 = self.linePoolURL.text()
        self.config.pool_config.pool_presets[
            current_index
        ].pool2 = self.linePoolURL_2.text()
        self.config.pool_config.pool_presets[
            current_index
        ].pool3 = self.linePoolURL_3.text()
        self.config.pool_config.pool_presets[
            current_index
        ].user1 = self.linePoolUser.text()
        self.config.pool_config.pool_presets[
            current_index
        ].user2 = self.linePoolUser_2.text()
        self.config.pool_config.pool_presets[
            current_index
        ].user3 = self.linePoolUser_3.text()
        self.config.pool_config.pool_presets[
            current_index
        ].passwd1 = self.linePoolPasswd.text()
        self.config.pool_config.pool_presets[
            current_index
        ].passwd2 = self.linePoolPasswd_2.text()
        self.config.pool_config.pool_presets[
            current_index
        ].passwd3 = self.linePoolPasswd_3.text()
        self.config.write()
        self.iprStatusBar.showMessage("Status :: successfully wrote pool preset.", 3000)

    def clear_pool_preset(self):
        current_index = self.comboPoolPreset.currentIndex()
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

    def toggle_system_tray_settings(self):
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
        self.restart_listen()

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
        if not self.aboutDialog or not self.aboutDialog.isVisible():
            self.aboutDialog = IPRAbout(
                self,
                "About",
                f"{IPR_METADATA['name']} is a {IPR_METADATA['desc']}\nVersion {IPR_METADATA['appversion']}\nQt Version {IPR_METADATA['qt']}\nPython Version {IPR_METADATA['python']}\n{IPR_METADATA['author']}\nPowered by {IPR_METADATA['company']}\n",
            )
            self.aboutDialog.show()

    def open_log(self):
        QDesktopServices.openUrl(
            QUrl(f"file:///{get_log_dir()}/ipr.log", QUrl.ParsingMode.TolerantMode)
        )

    def open_issues(self):
        webbrowser.open(f"{IPR_METADATA['source']}/issues", new=2)

    def open_source(self):
        webbrowser.open(f"{IPR_METADATA['source']}", new=2)

    def open_dashboard(self, host: str):
        webbrowser.open(f"http://{host}", new=2)

    def show_table_context(self):
        self.id_context_menu.exec(QCursor.pos())

    def double_click_item(self, model_index: QModelIndex):
        item = self.tableIPRID.itemFromIndex(model_index)
        match item.column():
            case 1:  # ip column
                self.open_dashboard(item.text())
            case 3:  # serial column
                self.tableIPRID.editItem(item)
            case _:
                return

    def get_selected_indexes_for_action(
        self, action: str, section: Optional[int] = None
    ) -> Optional[list[QModelIndex]]:
        rows = self.tableIPRID.rowCount()
        if not rows:
            return
        if section is not None and section != 0:
            selected = [
                x for x in self.tableIPRID.selectedIndexes() if x.column() == section
            ]
        else:
            selected = self.tableIPRID.selectedIndexes()
        if not len(selected):
            return
        selected_text = [self.tableIPRID.itemFromIndex(x).text() for x in selected]
        logger.info(f"{action} : running action for {selected_text}...")
        status_msg = f"Status :: Running action: {action} for [{','.join(selected_text[0:3])}...]..."
        self.iprStatusBar.showMessage(status_msg, 3000)
        return selected

    def open_selected_ips(self):
        rows = self.tableIPRID.rowCount()
        if not rows:
            return
        selected_ips = [x for x in self.tableIPRID.selectedIndexes() if x.column() == 1]
        for index in selected_ips:
            item = self.tableIPRID.itemFromIndex(index)
            self.open_dashboard(item.text())

    def copy_selected(self):
        logger.info(" copy selected elements.")
        rows = self.tableIPRID.rowCount()
        if not rows:
            return
        out = ""
        selected_indexes = self.tableIPRID.selectedIndexes()
        for r in range(rows):
            selected_indexes_in_row = [x for x in selected_indexes if x.row() == r]
            if len(selected_indexes_in_row) == 0:
                continue
            for index in range(len(selected_indexes_in_row)):
                sep = ""
                if len(selected_indexes_in_row) > 1:
                    sep = ","
                if not self.tableIPRID.itemFromIndex(selected_indexes_in_row[index]):
                    continue
                item = self.tableIPRID.itemFromIndex(selected_indexes_in_row[index])
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
        self.iprStatusBar.showMessage("Status :: Copied elements to clipboard.", 3000)

    def select_column(self, section: int):
        rows = self.tableIPRID.rowCount()
        if not rows:
            return
        if section != 0:
            for row in range(rows):
                item = self.tableIPRID.item(row, section)
                item.setSelected(True)

    def reset_sort(self):
        self.tableIPRID.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.id_header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

    def clear_table(self):
        return self.tableIPRID.setRowCount(0)

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
            self.iprStatusBar.showMessage("Status :: Failed to import table.", 5000)
            return

    def export_table(self):
        logger.info("export table.")
        rows = self.tableIPRID.rowCount()
        cols = self.tableIPRID.columnCount()
        if not rows:
            return
        out = "IP,MAC,SERIAL,TYPE,SUBTYPE,ALGORITHM,POOL,WORKER,FIRMWARE,PLATFORM\n"
        for i in range(rows):
            for j in range(1, cols):
                out += self.tableIPRID.item(i, j).text()
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
        self.iprStatusBar.showMessage(f"Status :: Wrote table as .CSV to {p}.", 3000)

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
                self.height(),
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
            self.iprStatusBar.showMessage(
                "Status :: Failed to start listeners. No listeners configured", 5000
            )
            return
        if not self.menu_bar.actionDisableInactiveTimer.isChecked():
            self.inactive.start()
        if self.checkEnableSysTray.isChecked():
            self.actionSysStartListen.setEnabled(False)
            self.actionSysStopListen.setEnabled(True)
        self.pushIPRListenStart.setEnabled(False)
        self.pushIPRListenStop.setEnabled(True)
        self.lm.start(self.listenerConfig)
        logger.info(f"start_listen : listening for [{self.lm.status}].")
        if self.is_minimized_to_tray():
            self.sys_tray.showMessage(
                "IPR Listener: Start",
                f"Started Listening on 0.0.0.0[{self.lm.status}]...",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.iprStatusBar.showMessage(
            f"Status :: UDP listening on 0.0.0.0[{self.lm.status}]..."
        )

    def stop_listen(self, timeout: bool = False, restart: bool = False):
        logger.info(" stop listeners.")
        self.inactive.stop()
        if self.checkEnableSysTray.isChecked():
            self.actionSysStartListen.setEnabled(True)
            self.actionSysStopListen.setEnabled(False)
        if (
            self.menu_bar.actionEnableIDTable.isChecked()
            and self.menu_bar.actionClearTableAfterStopListen.isChecked()
        ):
            self.clear_table()
        self.pushIPRListenStart.setEnabled(True)
        self.pushIPRListenStop.setEnabled(False)
        self.lm.stop()
        if timeout:
            logger.warning("stop_listen : timeout.")
            self.iprStatusBar.showMessage(
                "Status :: Inactive timeout. Stopped listeners", 5000
            )
            if self.is_minimized_to_tray():
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
        if self.is_minimized_to_tray():
            self.sys_tray.showMessage(
                "IPR Listener: Stop",
                "Stopped UDP listening.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.iprStatusBar.clearMessage()

    def restart_listen(self):
        if self.lm.count:
            logger.info(" restart listeners.")
            self.stop_listen(restart=True)
            self.start_listen()

    def process_result(self, result: IPReport):
        # reset inactive timer
        if self.inactive.isActive():
            self.inactive.start()
        logger.debug(
            f"process_result : got {result.src_ip}, {result.src_mac}, {result.miner_sn}, {result.miner_type} from listener."
        )
        # identify miner type from src ip
        miner_type = self.asic.identify(ip=result.src_ip, miner_hint=result.port_type)

        # get enabled "common" miners from listener config
        enabled_common_filter = [
            btn.text().lower()
            for btn in [self.checkListenAntminer, self.checkListenVolcminer]
            if btn.isChecked()
        ]
        # check if miner type is outside of enabled filter
        if (
            miner_type.value not in enabled_common_filter
            and self.checkEnableListenFilter.isChecked()
        ):
            logger.warning(
                f"process_result: received miner type {miner_type.value} outside of enabled filter. Ignoring..."
            )
            self.iprStatusBar.showMessage(
                f"Status :: Got miner type: {miner_type.value.capitalize()} outside of listener configuration.",
                8000,
            )
            return

        # get miner data from src ip
        alt_pwd = self.get_client_auth(miner_type=miner_type.value)
        self.asic.create_client(
            miner_type=miner_type, ip=result.src_ip, alt_pwd=alt_pwd
        )
        miner_data = self.asic.get_miner_data()
        miner_data["ip"] = result.src_ip
        miner_data["mac"] = miner_data["mac"].lower()
        # update serial if IPReport has
        if result.miner_sn:
            miner_data["serial"] = result.miner_sn
        # append IPReport data
        ip_report = result.model_dump()
        miner_data["ip_report"] = ip_report

        logger.debug(f"process_result: got miner data: {miner_data}.")

        self.iprStatusBar.showMessage(
            f"Status :: Got {miner_data['type']}: IP:{miner_data['ip']}, MAC:{miner_data['mac']}",
            5000,
        )
        self.show_confirmation(miner_data)

    # ip confirmation
    def show_confirmation(self, result: dict[str, Any]):
        logger.info(" show IP confirmation.")
        ip: str = result["ip"]
        mac: str = result["mac"]
        type: str = result["type"]
        fw_type: str = result["firmware"]
        type_str = f"{type.capitalize()} ({fw_type})"
        if self.menu_bar.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip)
        if self.menu_bar.actionEnableIDTable.isChecked() and self.isVisible():
            logger.info("show_confirmation : populate ID table.")
            self.populate_table_row(result)
            self.activateWindow()
        else:
            confirm = IPRConfirmation(self.menu_bar.actionConfirmsStayOnTop.isChecked())
            confirm.actionOpenDashboard.triggered.connect(
                lambda: self.open_dashboard(ip)
            )

            logger.info("show_confirmation : show IPRConfirmation.")
            confirm.lineIPField.setText(ip)
            confirm.lineMACField.setText(mac)
            confirm.lineASICField.setText(type_str)
            self.confirms.append(confirm)
            if self.is_minimized_to_tray():
                self.sys_tray.showMessage(
                    "Received IPR Confirmation",
                    f"IP: {ip}, MAC: {mac}",
                    QSystemTrayIcon.MessageIcon.Information,
                    15000,
                )
            confirm.showNormal()
            confirm.activateWindow()
            confirm.raise_()

    def get_client_auth(self, miner_type: str) -> str | None:
        client_auth: str | None = None
        match miner_type:
            case "antminer":
                client_auth = self.lineAntminerPasswd.text()
            case "whatsminer":
                client_auth = self.lineWhatsminerPasswd.text()
            case "goldshell":
                client_auth = self.lineGoldshellPasswd.text()
            case "volcminer":
                client_auth = self.lineVolcminerPasswd.text()
            case "sealminer":
                client_auth = self.lineSealminerPasswd.text()
            case "iceriver":
                client_auth = self.lineIceriverPasswd.text()
            case "elphapex":
                client_auth = self.lineElphapexPasswd.text()
            case "vnish":
                if not self.checkUseAntminerLogin.isChecked():
                    client_auth = self.lineVnishPasswd.text()
                else:
                    client_auth = self.lineAntminerPasswd.text()
                client_auth = self.lineVnishPasswd.text()
            case _:
                return None
        return client_auth

    def populate_table_row(self, data: Dict[str, Any]) -> None:
        """
        arguments:
            **data: dict[str. str] -- row data with the following key structure:
                'ip', 'mac', 'serial', 'type', 'subtype', 'algoritmn', 'firmware', 'platform'
        """
        logger.info("populate_table : write table data.")
        rowPosition = self.tableIPRID.rowCount()
        self.tableIPRID.insertRow(rowPosition)
        actionLocateMiner = QLabel()
        actionLocateMiner.setPixmap(QPixmap(":theme/icons/rc/flash.png"))
        actionLocateMiner.setToolTip("Locate Miner")
        self.tableIPRID.setCellWidget(rowPosition, 0, actionLocateMiner)
        self.tableIPRID.setItem(rowPosition, 0, IPRIndexWidgetItem(rowPosition))
        ip_item = QTableWidgetItem()
        ip_item.setData(Qt.ItemDataRole.UserRole, data["ip_report"]["src_addr"])
        ip_item.setText(data["ip"])
        self.tableIPRID.setItem(rowPosition, 1, ip_item)
        self.tableIPRID.setItem(rowPosition, 2, QTableWidgetItem(data["mac"]))
        # ASIC TYPE
        self.tableIPRID.setItem(rowPosition, 3, QTableWidgetItem(data["type"]))
        # SUBTYPE
        self.tableIPRID.setItem(rowPosition, 4, QTableWidgetItem(data["subtype"]))
        # SERIAL
        self.tableIPRID.setItem(rowPosition, 5, QTableWidgetItem(data["serial"]))
        # ALGO
        self.tableIPRID.setItem(rowPosition, 6, QTableWidgetItem(data["algorithm"]))
        # HOSTNAME
        self.tableIPRID.setItem(rowPosition, 7, QTableWidgetItem(data["hostname"]))
        # ACTIVE POOL
        self.tableIPRID.setItem(rowPosition, 8, QTableWidgetItem(data["stratum_url"]))
        # ACTIVE USER
        self.tableIPRID.setItem(rowPosition, 9, QTableWidgetItem(data["username"]))
        # ACTIVE WORKER
        self.tableIPRID.setItem(rowPosition, 10, QTableWidgetItem(data["worker_name"]))
        # FIRMWARE TYPE
        self.tableIPRID.setItem(rowPosition, 11, QTableWidgetItem(data["firmware"]))
        # FIRMWARE VERSION
        self.tableIPRID.setItem(rowPosition, 12, QTableWidgetItem(data["fw_version"]))
        # PLATFORM
        self.tableIPRID.setItem(rowPosition, 13, QTableWidgetItem(data["platform"]))
        self.tableIPRID.scrollToBottom()

    def locate_miner(self, row: int, col: int):
        if col == 0:
            miner_type = self.tableIPRID.item(row, 4).text()
            ip_addr = self.tableIPRID.item(row, 1).text()
            if self.api_client.locate and self.api_client.locate.isActive():
                return logger.warning(
                    "locate_miner : already locating a miner. Ignoring..."
                )
            logger.info(f" locate miner {ip_addr}.")
            match miner_type:
                case "volcminer":
                    # client_auth = self.lineVolcminerPasswd.text()
                    return self.iprStatusBar.showMessage(
                        "Status :: Failed to locate miner: VolcMiner is currently not supported.",
                        5000,
                    )
            client_auth, custom_auth = self.get_client_auth_from_type(miner_type)
            self.api_client.create_client_from_type(
                miner_type, ip_addr, client_auth, custom_auth
            )
            client = self.api_client.get_client()
            if not client:
                return self.iprStatusBar.showMessage(
                    "Status :: Failed to connect or authenticate client.", 5000
                )
            self.api_client.locate_miner(miner_type)
            if client._error:
                return self.iprStatusBar.showMessage(
                    f"Status :: Failed to locate miner: {client._error}", 5000
                )
            self.iprStatusBar.showMessage(
                f"Status :: Locating miner: {ip_addr}...",
                self.miner_locate_duration,
            )

    def get_miner_pool(self):
        rows = self.tableIPRID.rowCount()
        if not rows:
            return
        selected_ips = [x for x in self.tableIPRID.selectedIndexes() if x.column() == 1]
        index = selected_ips[0]
        item = self.tableIPRID.itemFromIndex(index)
        miner_type = self.tableIPRID.item(item.row(), 4).text()
        client_auth, custom_auth = self.get_client_auth_from_type(miner_type)
        self.api_client.create_client_from_type(
            miner_type, item.text(), client_auth, custom_auth
        )
        client = self.api_client.get_client()
        if not client:
            return
        urls, users, passwds = self.api_client.get_miner_pool_conf(miner_type)
        if client._error:
            return self.iprStatusBar.showMessage(
                f"Status :: Failed to get pool config: {client._error}", 5000
            )

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
        self.iprStatusBar.showMessage(
            f"Status :: Updated {self.comboPoolPreset.currentText()} preset from {item.text()}.",
            3000,
        )

    def update_miner_pools(self):
        passed: list[str] = []
        failed: list[str] = []
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
            item = self.tableIPRID.itemFromIndex(index)
            ip_addr = item.text()
            miner_type = self.tableIPRID.item(item.row(), 4).text()
            macaddr = self.tableIPRID.item(item.row(), 2).text()
            serial = self.tableIPRID.item(item.row(), 3).text()
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
            return self.iprStatusBar.showMessage(
                f"Status :: Failed to update pools for {failed}.", 5000
            )
        self.iprStatusBar.showMessage("Status :: Successfully updated pools.", 3000)

    # exit
    def close_to_tray_or_exit(self):
        if (
            self.checkEnableSysTray.isChecked()
            and self.comboOnWindowClose.currentIndex() == 0
        ):
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
            c.deleteLater()
        self.confirms = []
        self.iprStatusBar.showMessage("Status :: Killed all confirmations.", 3000)

    def quit(self):
        if self.is_minimized_to_tray():
            self.toggle_visibility()
        self.sys_tray.hide()
        self.lm.stop()
        self.lm.listen_complete.disconnect(self.process_result)
        self.lm.listen_error.disconnect(self.restart_listen)
        self.killall()
        logger.info(" write settings to disk.")
        self.write_settings()
        logger.info(" exit app.")
        # flush log on close if set
        if self.checkFlushOnClose.isChecked():
            for handler in logger.root.handlers:
                if isinstance(handler, RotatingFileHandler):
                    handler.doRollover()
        self.close()
        self.deleteLater()
