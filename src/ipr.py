# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
import os
import shlex
import shutil
import subprocess
import time
import webbrowser
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError
from PySide6.QtCore import (
    QDateTime,
    QEventLoop,
    QFile,
    QIODevice,
    QItemSelectionModel,
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
    QDialog,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QWidget,
)

import ui.resources  # noqa F401
from config import IPRConfig, PoolPreset
from iprabout import IPRAbout
from iprconfirmation import IPRConfirmation
from mod.apiv2 import ASICClient
from mod.apiv2 import settings as api_settings
from mod.apiv2.data import MinerData, MinerFirmware, MinerType
from mod.apiv2.errors import UnknownClientError
from mod.lm import IPRDListener, IPReport, ListenerManager
from mod.updater import (
    DebInstaller,
    UpdateChecker,
    UpdateDownloader,
    get_platform,
    select_asset,
)
from ui import Ui_MainWindow
from ui.widgets import (
    COL_LOCATE,
    COL_RECV_AT,
    COL_REFRESH,
    IPRActionDelegate,
    IPRFilterProxyModel,
    IPRMenubar,
    IPRMessage,
    IPRProgress,
    IPRTableContextMenu,
    IPRTableModel,
    IPRTitlebar,
)
from utils import (
    CURR_PLATFORM,
    IPR_METADATA,
    deep_update,
    get_download_dir,
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
        self.aboutDialog: IPRAbout | None = None
        self.update_checker: UpdateChecker | None = None
        self._update_check_silent = False
        self.downloader: UpdateDownloader | None = None
        self.download_dialog: IPRProgress | None = None
        self.installer: DebInstaller | None = None
        self.install_dialog: IPRProgress | None = None
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
        # init iprd listener
        self.iprd = IPRDListener(self)
        self.iprd.result.connect(self.process_result)
        self.iprd.error.connect(self.show_iprd_error)

        logger.info(" init mod api.")
        self.asic = ASICClient(self)
        logger.info(" init miner locate duration for 10000ms.")
        self.miner_locate_duration: int = api_settings.get("locate_duration_ms")

        # initialize IPR_Titlebar widget
        self.title_bar = IPRTitlebar(self, "BitCap IPReporter", ["min", "close"])
        self.title_bar.minimize_button.clicked.connect(self.window().showMinimized)
        self.title_bar.close_button.clicked.connect(self.close_to_tray_or_exit)
        title_bar_widget = self.titleBarWidget.layout()
        if title_bar_widget:
            title_bar_widget.addWidget(self.title_bar)

        # initialize IPR_Menubar widget
        self.menu_bar = IPRMenubar(self)
        menu_bar_widget = self.menuBarWidget.layout()
        if menu_bar_widget:
            menu_bar_widget.addWidget(self.menu_bar)

        # IPR_Menubar signals
        self.menu_bar.actionAbout.triggered.connect(self.about)
        self.menu_bar.actionOpenLog.triggered.connect(self.open_log)
        self.menu_bar.actionReportIssue.triggered.connect(self.open_issues)
        self.menu_bar.actionSourceCode.triggered.connect(self.open_source)
        self.menu_bar.actionCheckForUpdates.triggered.connect(self.check_for_updates)
        self.menu_bar.actionKillAllConfirmations.triggered.connect(self.killall)
        self.menu_bar.actionQuit.triggered.connect(self.quit)
        self.menu_bar.menuOptions.triggered.connect(self.update_settings)
        self.menu_bar.actionEnableIDTable.triggered.connect(self.update_stacked_widget)
        self.menu_bar.actionEnableIDTable.toggled.connect(self.toggle_table_settings)
        self.menu_bar.actionOpenSelectedIPs.triggered.connect(self.open_selected_ips)
        self.menu_bar.actionCopySelectedElements.triggered.connect(self.copy_selected)
        self.menu_bar.actionResetSort.triggered.connect(self.reset_sort)
        self.menu_bar.actionResetView.triggered.connect(self.reset_view)
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
        self.listenerConfig.addButton(self.checkListenAuradine, 9)
        self.listenerConfig.addButton(self.checkListenIPollo, 10)
        self.listenerConfig.buttonClicked.connect(self.restart_listen)
        # listener signals
        self.pushIPRListenStart.clicked.connect(self.start_listen)
        self.pushIPRListenStop.clicked.connect(self.stop_listen)

        self.checkEnableIPRDBackend.toggled.connect(self.restart_listen)
        self.lineIPRDSocketAddress.editingFinished.connect(self.restart_listen)

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
        self.actionIPRCreatePreset.clicked.connect(self.add_new_preset)
        self.actionIPRRemovePreset.clicked.connect(self.remove_preset)
        self.actionIPRSavePreset.clicked.connect(self.write_pool_preset)
        self.actionIPRClearPreset.clicked.connect(self.clear_pool_preset)

        # initialize ID Table (headers are provided by IPRTableModel)
        self.id_model = IPRTableModel(self)
        self.id_proxy = IPRFilterProxyModel(self)
        self.id_proxy.setSourceModel(self.id_model)
        self.tableIPRID.setModel(self.id_proxy)
        # action-column icons (refresh / locate) painted by a delegate
        self.id_action_delegate = IPRActionDelegate(self.tableIPRID)
        self.tableIPRID.setItemDelegateForColumn(COL_REFRESH, self.id_action_delegate)
        self.tableIPRID.setItemDelegateForColumn(COL_LOCATE, self.id_action_delegate)
        self.id_action_delegate.action_clicked.connect(self.handle_widget_action)
        self.tableIPRID.setColumnWidth(0, 15)
        self.tableIPRID.setColumnWidth(1, 15)
        self.tableIPRID.setColumnWidth(2, 180)
        self.tableIPRID.setColumnWidth(4, 120)
        self.tableIPRID.setColumnWidth(6, 130)
        self.tableIPRID.setColumnWidth(7, 145)
        self.tableIPRID.setColumnWidth(10, 385)
        self.tableIPRID.setColumnWidth(11, 300)
        self.tableIPRID.setColumnWidth(14, 180)
        self.tableIPRID.doubleClicked.connect(self.double_click_item)
        # sorting is driven by the toolbar controls, not header clicks, so a
        # header click is free to select the column without sorting it
        self.tableIPRID.setSortingEnabled(False)
        self.id_header = self.tableIPRID.horizontalHeader()
        self.id_header.setSortIndicatorShown(False)
        self.id_header.sectionClicked.connect(self.select_column)
        # vertical header: 1-based row-count column on the left
        v_header = self.tableIPRID.verticalHeader()
        v_header.setVisible(True)
        self.lineIDTableFilter.textChanged.connect(self.id_proxy.set_filter_text)
        # sort controls: column combo + asc/desc toggle (next to the filter)
        for col in range(self.id_model.columnCount()):
            header = self.id_model.headerData(
                col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
            )
            if header:  # skip the icon-only action columns (empty header)
                self.comboSortColumn.addItem(header, col)
        self.comboSortColumn.currentIndexChanged.connect(self.apply_sort)
        self.btnSortOrder.toggled.connect(self.apply_sort)
        self.btnResetView.setIcon(QIcon(":theme/icons/rc/clear.png"))
        self.btnResetView.clicked.connect(self.reset_view)
        # asc/desc glyphs for the sort order toggle (keyed by "is descending")
        self.id_sort_icons = {
            False: QIcon(":theme/icons/rc/arrow_up.png"),
            True: QIcon(":theme/icons/rc/arrow_down.png"),
        }
        # default sort: oldest -> newest by RECV AT (new arrivals at the bottom)
        self.reset_sort()

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
        self.id_context_menu.contextActionTableResetView.triggered.connect(
            self.reset_view
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
        self.actionToggleAuradinePasswd = self.create_passwd_toggle_action(
            self.lineAuradinePasswd
        )
        self.actionToggleIPolloPasswd = self.create_passwd_toggle_action(
            self.lineIPolloPasswd
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

        if self.config.general.check_updates_on_startup:
            self.check_for_updates(silent=True)

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

    def update_stacked_widget(self, view_index: int | None = None, *_):
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
        if (
            self.checkEnableIPRDBackend.isChecked()
            and self.iprd.active
            and not self.iprStatusBar.currentMessage()
        ):
            self.iprStatusBar.showMessage(
                f"Status :: Listening on [{self.iprd.__repr__()}]..."
            )
        if self.lm.count and not self.iprStatusBar.currentMessage():
            self.iprStatusBar.showMessage(
                f"Status :: Listening on 0.0.0.0[{self.lm.status}]..."
            )
        if not self.iprStatusBar.currentMessage():
            self.iprStatusBar.showMessage("Status :: Ready.")

    def update_pool_preset_names(self):
        for idx in range(0, len(self.config.pool_config.pool_presets)):
            self.comboPoolPreset.insertItem(
                idx, self.config.pool_config.pool_presets[idx].preset_name
            )
        self.comboPoolPreset.setCurrentIndex(self.config.pool_config.selected_preset)

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
        self.checkCheckUpdatesOnStartup.setChecked(
            self.config.general.check_updates_on_startup
        )
        self.checkIncludePreReleases.setChecked(self.config.general.include_prereleases)

        # listener
        self.groupListeners.setChecked(self.config.listener.enable_all)
        self.checkEnableListenFilter.setChecked(self.config.listener.enable_filter)
        self.checkListenAntminer.setChecked(self.config.listen_for.antminer)
        self.checkListenWhatsminer.setChecked(self.config.listen_for.whatsminer)
        self.checkListenIceRiver.setChecked(self.config.listen_for.iceriver)
        self.checkListenHammer.setChecked(self.config.listen_for.hammer)
        self.checkListenVolcminer.setChecked(self.config.listen_for.volcminer)
        self.checkListenGoldshell.setChecked(self.config.listen_for.goldshell)
        self.checkListenSealminer.setChecked(self.config.listen_for.sealminer)
        self.checkListenElphapex.setChecked(self.config.listen_for.elphapex)
        self.checkListenAuradine.setChecked(self.config.listen_for.auradine)
        self.checkListenIPollo.setChecked(self.config.listen_for.ipollo)
        self.checkEnableIPRDBackend.setChecked(self.config.listener.iprd.enable_iprd)
        self.lineIPRDSocketAddress.setText(self.config.listener.iprd.socket_addr)

        # api
        self.lineAntminerPasswd.setText(self.config.api.auth.antminer_alt_passwd)
        self.lineIceriverPasswd.setText(self.config.api.auth.iceriver_alt_passwd)
        self.lineWhatsminerPasswd.setText(self.config.api.auth.whatsminer_alt_passwd)
        self.lineVolcminerPasswd.setText(self.config.api.auth.volcminer_alt_passwd)
        self.lineGoldshellPasswd.setText(self.config.api.auth.goldshell_alt_passwd)
        self.lineElphapexPasswd.setText(self.config.api.auth.elphapex_alt_passwd)
        self.lineVnishPasswd.setText(self.config.api.firmware.vnish_alt_passwd)
        self.lineAuradinePasswd.setText(self.config.api.auth.auradine_alt_passwd)
        # disabled APIs
        # self.lineHammerPasswd.setText(self.config.api.auth.hammer_alt_passwd)
        # self.lineIPolloPasswd.setText(self.config.api.auth.ipollo_alt_passwd)

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
        if len(self.config.pool_config.pool_presets):
            self.linePoolURL.setText(
                self.config.pool_config.pool_presets[preset_idx].pool1
            )
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
            self.config.table.clear_table_on_stop
        )
        self.menu_bar.actionEnableIDTable.setChecked(
            self.config.instance.views.show_table
        )
        self.menu_bar.actionEnableLiveCapture.setChecked(
            self.config.table.table_live_capture
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
                "confirmsStayOnTop": self.menu_bar.actionConfirmsStayOnTop.isChecked(),
            },
            "idTable": {
                "enableTableLiveCapture": self.menu_bar.actionEnableLiveCapture.isChecked(),
                "clearTableOnStop": self.menu_bar.actionClearTableAfterStopListen.isChecked(),
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
            "inactiveTimeoutDuration": self.spinInactiveTimeout.value(),
            "checkForUpdatesOnStartup": self.checkCheckUpdatesOnStartup.isChecked(),
            "includePreReleases": self.checkIncludePreReleases.isChecked(),
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
                "auradine": self.checkListenAuradine.isChecked(),
                "ipollo": self.checkListenIPollo.isChecked(),
            },
            "iprd": {
                "enableIPRD": self.checkEnableIPRDBackend.isChecked(),
                "socketAddress": self.lineIPRDSocketAddress.text(),
            },
        }
        settings["api"] = {
            "locateDuration": self.spinLocateDuration.value(),
            "auth": {
                "antminerAltPasswd": self.lineAntminerPasswd.text(),
                "iceriverAltPasswd": self.lineIceriverPasswd.text(),
                "whatsminerAltPasswd": self.lineWhatsminerPasswd.text(),
                "goldshellAltPasswd": self.lineGoldshellPasswd.text(),
                # "hammerAltPasswd": self.lineHammerPasswd.text(),
                "volcminerAltPasswd": self.lineVolcminerPasswd.text(),
                "elphapexAltPasswd": self.lineElphapexPasswd.text(),
                "sealminerAltPasswd": self.lineSealminerPasswd.text(),
                "auradineAltPasswd": self.lineAuradinePasswd.text(),
                # "ipolloAltPasswd": self.lineIPolloPasswd.text()
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
            # reset pool presets
            self.clear_pool_preset()
            self.comboPoolPreset.clear()
            self.read_settings()
            self.update_inactive_timer()
            self.update_miner_locate_duration()
            self.update_stacked_widget()
            self.iprStatusBar.showMessage(
                "Status :: Successfully restored to default settings.", 5000
            )

    def update_current_preset_to_config(self) -> list[dict[str, str]]:
        presets = TypeAdapter(list[PoolPreset])
        saved_pools: list[dict[str, str]] = presets.dump_python(
            self.config.pool_config.pool_presets, by_alias=True
        )
        if not len(saved_pools):
            return []
        current_index = self.comboPoolPreset.currentIndex()
        saved_pools[current_index]["preset_name"] = self.comboPoolPreset.currentText()
        saved_pools[current_index]["pool1"] = self.linePoolURL.text()
        saved_pools[current_index]["pool2"] = self.linePoolURL_2.text()
        saved_pools[current_index]["pool3"] = self.linePoolURL_3.text()
        saved_pools[current_index]["user1"] = self.linePoolUser.text()
        saved_pools[current_index]["user2"] = self.linePoolUser_2.text()
        saved_pools[current_index]["user3"] = self.linePoolUser_3.text()
        saved_pools[current_index]["passwd1"] = self.linePoolPasswd.text()
        saved_pools[current_index]["passwd2"] = self.linePoolPasswd_2.text()
        saved_pools[current_index]["passwd3"] = self.linePoolPasswd_3.text()
        return saved_pools

    def update_pool_preset(self, preset_name: str):
        current_index = self.comboPoolPreset.currentIndex()
        self.comboPoolPreset.setItemText(current_index, preset_name)

    def add_new_preset(self, *_, preset: PoolPreset | None = None) -> None:
        index = len(self.config.pool_config.pool_presets)
        if preset is None:
            preset = PoolPreset(preset_name="New Preset")

        self.config.pool_config.pool_presets.append(preset)
        self.config.write()

        self.comboPoolPreset.insertItem(index, preset.preset_name)
        self.comboPoolPreset.setCurrentIndex(index)
        self.comboPoolPreset.setCurrentText(preset.preset_name)
        self.comboPoolPreset.lineEdit().setFocus()
        self.comboPoolPreset.lineEdit().selectAll()

    def remove_preset(self) -> None:
        index = self.comboPoolPreset.currentIndex()
        if not len(self.config.pool_config.pool_presets):
            return
        self.config.pool_config.pool_presets.pop(index)
        self.config.write()

        self.comboPoolPreset.removeItem(index)
        if self.comboPoolPreset.currentIndex() == -1:
            self.clear_pool_preset()

    def read_pool_preset(self, index: int) -> None:
        self.config.read()
        if not len(self.config.pool_config.pool_presets):
            return
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
        curr_index = self.comboPoolPreset.currentIndex()
        if curr_index == -1:
            # no existing presets, lets add one
            preset_name = self.comboPoolPreset.currentText()
            if preset_name == "":
                preset_name = "New Preset"
            new_preset = PoolPreset(
                preset_name=preset_name,
                pool1=self.linePoolURL.text(),
                pool2=self.linePoolURL_2.text(),
                pool3=self.linePoolURL_3.text(),
                user1=self.linePoolUser.text(),
                user2=self.linePoolUser_2.text(),
                user3=self.linePoolUser_3.text(),
                passwd1=self.linePoolPasswd.text(),
                passwd2=self.linePoolPasswd_2.text(),
                passwd3=self.linePoolPasswd_3.text(),
            )
            self.add_new_preset(preset=new_preset)
            self.config.pool_config.selected_preset = (
                self.comboPoolPreset.currentIndex()
            )
        else:
            # fetch existing index
            self.config.pool_config.selected_preset = curr_index
            preset = self.config.pool_config.pool_presets[curr_index]
            preset.preset_name = self.comboPoolPreset.currentText()
            preset.pool1 = self.linePoolURL.text()
            preset.pool2 = self.linePoolURL_2.text()
            preset.pool3 = self.linePoolURL_3.text()
            preset.user1 = self.linePoolUser.text()
            preset.user2 = self.linePoolUser_2.text()
            preset.user3 = self.linePoolUser_3.text()
            preset.passwd1 = self.linePoolPasswd.text()
            preset.passwd2 = self.linePoolPasswd_2.text()
            preset.passwd3 = self.linePoolPasswd_3.text()
        self.config.write()
        self.iprStatusBar.showMessage("Status :: successfully wrote pool preset.", 3000)

    def clear_pool_preset(self):
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
        self.menu_bar.actionEnableLiveCapture.setEnabled(enabled)
        self.menu_bar.actionOpenSelectedIPs.setEnabled(enabled)
        self.menu_bar.actionCopySelectedElements.setEnabled(enabled)
        self.menu_bar.menuTableAction.setEnabled(enabled)
        self.menu_bar.actionResetSort.setEnabled(enabled)
        self.menu_bar.actionClearTable.setEnabled(enabled)
        self.menu_bar.actionResetSort.setEnabled(enabled)
        self.menu_bar.actionResetView.setEnabled(enabled)
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

    def check_for_updates(self, silent: bool = False):
        if self.update_checker and self.update_checker.isRunning():
            return
        self._update_check_silent = silent
        self.menu_bar.actionCheckForUpdates.setEnabled(False)
        self.update_checker = UpdateChecker(
            IPR_METADATA["appversion"],
            self.config.general.include_prereleases,
            self,
        )
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.up_to_date.connect(self.on_up_to_date)
        self.update_checker.error.connect(self.on_update_error)
        self.update_checker.finished.connect(
            lambda: self.menu_bar.actionCheckForUpdates.setEnabled(True)
        )
        self.iprStatusBar.showMessage("Status :: Checking for updates...", 3000)
        self.update_checker.start()

    def on_update_available(self, release: dict):
        self.iprStatusBar.clearMessage()
        is_prerelease = release.get("prerelease", False)
        kind = "pre-release" if is_prerelease else "version"
        self.iprStatusBar.showMessage(
            f"Status :: {'Pre-release' if is_prerelease else 'Update'} available!",
            3000,
        )
        dialog = IPRMessage(
            self,
            "Update Available",
            f"A new {kind} of {IPR_METADATA['name']} is available: {release['name']}\n"
            f"You are currently running {IPR_METADATA['appversion']}.",
            action_text="Download",
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.download_update(release)

    def download_update(self, release: dict):
        os_name, is_arm = get_platform()
        asset = select_asset(release.get("assets", []), os_name, is_arm)
        if not asset:
            # no binary matches this platform; fall back to the release page.
            logger.warning(" no matching release asset; opening release page.")
            webbrowser.open(
                release["url"] or f"{IPR_METADATA['source']}/releases/latest", new=2
            )
            return

        dest = Path(get_download_dir(), asset["name"])
        logger.info(f" downloading update asset {asset['name']} to {dest}")
        self.download_dialog = IPRProgress(
            self, "Downloading Update", f"Downloading {asset['name']}..."
        )
        self.download_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.downloader = UpdateDownloader(asset["url"], str(dest), self)
        self.downloader.progress.connect(self.download_dialog.set_progress)
        self.downloader.completed.connect(self.on_download_complete)
        self.downloader.error.connect(self.on_download_error)
        self.download_dialog.cancelled.connect(self.downloader.cancel)
        self.iprStatusBar.showMessage("Status :: Downloading update...", 3000)
        self.downloader.start()
        self.download_dialog.show()

    def _close_download_dialog(self):
        if self.download_dialog:
            self.download_dialog.close()
            self.download_dialog = None

    def on_download_complete(self, path: str):
        self._close_download_dialog()
        self.iprStatusBar.showMessage("Status :: Update downloaded.", 3000)
        dialog = IPRMessage(
            self,
            "Download Complete",
            f"The update was saved to:\n{path}\n\n"
            "Install now? The application will close to complete installation.",
            action_text="Install",
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.install_update(path)

    def on_download_error(self, error: str):
        self._close_download_dialog()
        logger.error(f" failed to download update: {error}")
        self.iprStatusBar.showMessage("Status :: Download failed.", 5000)
        IPRMessage(
            self,
            "Download Failed",
            f"Could not download the update. Please try again later.\n\n{error}",
        ).exec()

    def install_update(self, path: str):
        logger.info(f" installing update from {path}")
        if CURR_PLATFORM.startswith("win") and path.lower().endswith(".exe"):
            self._install_windows(path)
        elif (
            CURR_PLATFORM.startswith("linux")
            and path.lower().endswith(".deb")
            and shutil.which("pkexec")
            and shutil.which("apt-get")
        ):
            self._install_deb(path)
        else:
            # hand the file to the OS default handler (e.g. a macOS .dmg, or
            # when no silent install path is available for this platform).
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            self.quit()

    def _install_windows(self, path: str):
        # silent install: the Inno Setup installer shows only a progress
        # window, closes the running app via Restart Manager and relaunches
        # it once the files are replaced.
        subprocess.Popen(
            [path, "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
            close_fds=True,
        )
        # quit so the installer can replace the running application.
        self.quit()

    def _install_deb(self, path: str):
        self.install_dialog = IPRProgress(
            self,
            "Installing Update",
            "Installing update... You may be prompted for your password.",
            cancellable=False,
        )
        self.install_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.installer = DebInstaller(path, self)
        self.installer.completed.connect(self.on_install_complete)
        self.installer.error.connect(self.on_install_error)
        self.iprStatusBar.showMessage("Status :: Installing update...", 3000)
        self.installer.start()
        self.install_dialog.show()

    def _close_install_dialog(self):
        if self.install_dialog:
            self.install_dialog.close()
            self.install_dialog = None

    def on_install_complete(self, version: str):
        self._close_install_dialog()
        self.iprStatusBar.showMessage("Status :: Update installed.", 3000)
        installed = f" (version {version})" if version else ""
        dialog = IPRMessage(
            self,
            "Update Installed",
            f"The update was installed successfully{installed}.\n\n"
            "Restart now to use the new version?",
            action_text="Restart",
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._relaunch()
            self.quit()

    def on_install_error(self, error: str):
        self._close_install_dialog()
        logger.error(f" failed to install update: {error}")
        self.iprStatusBar.showMessage("Status :: Install failed.", 5000)
        IPRMessage(
            self,
            "Install Failed",
            f"Could not install the update.\n\n{error}",
        ).exec()

    def _relaunch(self):
        # relaunch the installed binary after a short delay so the running
        # instance releases its single-instance lock before the new one starts.
        bin_path = "/opt/bitcap-ipr/BitCapIPR"
        if not os.path.exists(bin_path):
            logger.info(" installed binary not found; skipping relaunch.")
            return
        try:
            subprocess.Popen(
                ["sh", "-c", f"sleep 1; exec {shlex.quote(bin_path)}"],
                close_fds=True,
            )
        except OSError as exc:
            logger.warning(f" failed to relaunch app: {exc}")

    def on_up_to_date(self, current: str) -> None:
        self.iprStatusBar.clearMessage()
        self.iprStatusBar.showMessage("Status :: Up to date.", 3000)
        if not self._update_check_silent:
            IPRMessage(
                self,
                "No Updates",
                f"You are running the latest version ({current}).",
            ).exec()

    def on_update_error(self, error: str) -> None:
        self.iprStatusBar.clearMessage()
        self.iprStatusBar.showMessage("Status :: Failed to check for updates.", 5000)
        logger.error(f" failed to check for updates: {error}")
        if not self._update_check_silent:
            IPRMessage(
                self,
                "Update Check Failed",
                f"Could not check for updates. Please try again later.\n\n{error}",
            ).exec()

    def dashboard_url(
        self, host: str, miner_type: MinerType | str | None = None
    ) -> str:
        mtype = (
            miner_type
            if isinstance(miner_type, MinerType)
            else MinerType.from_value(str(miner_type or ""))
        )
        port = 4200 if mtype == MinerType.HIVEGPU else 80
        return f"http://{host}:{port}"

    def open_dashboard(self, host: str, miner_type: MinerType | str | None = None):
        webbrowser.open(self.dashboard_url(host, miner_type), new=2)

    def show_table_context(self):
        self.id_context_menu.exec(QCursor.pos())

    def double_click_item(self, model_index: QModelIndex):
        # model_index is a proxy index
        match model_index.column():
            case 3:  # ip column
                source_row = self.id_proxy.mapToSource(model_index).row()
                miner = self.id_model.miner_at(source_row)
                self.open_dashboard(model_index.data(), miner.type)
            case 7:  # serial column
                self.tableIPRID.edit(model_index)
            case _:
                return

    def get_selected_indexes_for_action(
        self, action: str, section: int | None = None
    ) -> list[QModelIndex] | None:
        rows = self.id_proxy.rowCount()
        if not rows:
            return
        selected = self.tableIPRID.selectionModel().selectedIndexes()
        if section is not None and section != 0:
            selected = [x for x in selected if x.column() == section]
        if not len(selected):
            return
        selected_text = [x.data() for x in selected]
        logger.info(f"{action} : running action for {selected_text}...")
        status_msg = f"Status :: Running action: {action} for [{','.join(selected_text[0:3])}...]..."
        self.iprStatusBar.showMessage(status_msg, 3000)
        return selected

    def open_selected_ips(self):
        if not self.id_proxy.rowCount():
            return
        selected_ips = [
            x
            for x in self.tableIPRID.selectionModel().selectedIndexes()
            if x.column() == 3
        ]
        for index in selected_ips:
            source_row = self.id_proxy.mapToSource(index).row()
            miner = self.id_model.miner_at(source_row)
            self.open_dashboard(index.data(), miner.type)

    def copy_selected(self):
        logger.info(" copy selected elements.")
        rows = self.id_proxy.rowCount()
        if not rows:
            return
        out = ""
        selected_indexes = self.tableIPRID.selectionModel().selectedIndexes()
        for r in range(rows):
            selected_indexes_in_row = [x for x in selected_indexes if x.row() == r]
            if len(selected_indexes_in_row) == 0:
                continue
            for index in range(len(selected_indexes_in_row)):
                sep = ""
                if len(selected_indexes_in_row) > 1:
                    sep = ","
                cell = selected_indexes_in_row[index]
                match cell.column():
                    case 0 | 1:  # ignore widget actions
                        continue
                    case 3:  # ip
                        source_row = self.id_proxy.mapToSource(cell).row()
                        miner = self.id_model.miner_at(source_row)
                        out += f"{self.dashboard_url(cell.data(), miner.type)}{sep}"
                    case _:
                        out += f"{cell.data()}{sep}"
                continue
            out += "\n"
        logger.info("copy_selected : copy elements to clipboard.")
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(out.strip(), mode=cb.Mode.Clipboard)
        self.iprStatusBar.showMessage("Status :: Copied elements to clipboard.", 3000)

    def select_column(self, section: int):
        rows = self.id_proxy.rowCount()
        if not rows:
            return
        if section != 0:
            selection_model = self.tableIPRID.selectionModel()
            for row in range(rows):
                selection_model.select(
                    self.id_proxy.index(row, section),
                    QItemSelectionModel.SelectionFlag.Select,
                )

    def apply_sort(self, *_args):
        """Sort the proxy from the current toolbar control state."""
        col = self.comboSortColumn.currentData()
        if col is None:
            return
        descending = self.btnSortOrder.isChecked()
        order = (
            Qt.SortOrder.DescendingOrder if descending else Qt.SortOrder.AscendingOrder
        )
        self.btnSortOrder.setIcon(self.id_sort_icons[descending])
        self.id_proxy.sort(col, order)

    def reset_sort(self):
        # reset to the default sort: RECV AT ascending
        self.comboSortColumn.setCurrentIndex(self.comboSortColumn.findData(COL_RECV_AT))
        self.btnSortOrder.setChecked(False)
        self.apply_sort()

    def reset_view(self):
        # clear the active filter and return the sort to its default
        self.lineIDTableFilter.clear()
        self.reset_sort()

    def clear_table(self):
        self.reset_view()
        return self.id_model.clear()

    def import_table(self):
        logger.info(" import table.")
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open .CSV",
            Path(Path.home(), "Documents", "ipr").resolve().__str__(),
            ".CSV Files (*.csv)",
        )
        self.clear_table()
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
                        MinerData().as_dict(),
                        dict(zip(included_headers, line.split(","))),
                    )
                    miner = self._miner_from_data(row)
                    self.id_model.append(miner)
            self.tableIPRID.scrollToBottom()
        else:
            logger.error(f"import_table : failed to read file {file_name}.")
            self.iprStatusBar.showMessage("Status :: Failed to import table.", 5000)
            return

    def export_table(self):
        logger.info("export table.")
        rows = self.id_proxy.rowCount()
        cols = self.id_proxy.columnCount()
        if not rows:
            return
        out = "RECV_AT,IP,MAC,TYPE,SUBTYPE,SERIAL,ALGORITHM,HOSTNAME,STRATUM_URL,USERNAME,WORKER_NAME,FIRMWARE,FW_VERSION,PLATFORM\n"
        for i in range(rows):
            # skip the two action columns; write data columns in display order
            for j in range(2, cols):
                out += str(self.id_proxy.index(i, j).data())
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
        if (
            not any(
                listenFor.isChecked() for listenFor in self.listenerConfig.buttons()
            )
            and not self.checkEnableIPRDBackend.isChecked()
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
        if not self.checkEnableIPRDBackend.isChecked():
            self.lm.start(self.listenerConfig)
            listen_status = f"Listening on 0.0.0.0[{self.lm.status}]..."
        else:
            self.iprd.subscribed.connect(self.update_status_msg)
            try:
                addr, port = self.lineIPRDSocketAddress.text().split(":")
                port = int(port)
            except ValueError:
                self.stop_listen()
                logger.error(
                    "start_listen : failed to start IPRD listener! Invalid socket address."
                )
                return self.iprStatusBar.showMessage(
                    "Status :: Failed to start IPRD Listener: Invalid socket address.",
                    5000,
                )
            else:
                self.iprd.set_socket_addr(addr, port)
                self.iprd.start()
                listen_status = f"Connecting to {addr}:{port}..."

        logger.info(f"start_listen : {listen_status}.")
        if self.is_minimized_to_tray():
            self.sys_tray.showMessage(
                "IPR Listener: Start",
                f"{listen_status}",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        self.iprStatusBar.showMessage(f"Status :: {listen_status}", 8000)

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
        # ensure lm is stopped
        self.lm.stop()
        if self.iprd.active:
            self.iprd.subscribed.disconnect(self.update_status_msg)
            self.iprd.stop()
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
        if self.lm.count or self.iprd.active:
            logger.info(" restart listeners.")
            self.stop_listen(restart=True)
            self.start_listen()

    def show_iprd_error(self, error_str: str):
        logger.error(f" received IPRD Listener error: {error_str}")
        self.stop_listen()
        if self.is_minimized_to_tray():
            self.sys_tray.showMessage(
                "IPR Listener: Error",
                f"Got Listener error: {error_str}",
                QSystemTrayIcon.MessageIcon.Warning,
                5000,
            )
        return self.iprStatusBar.showMessage(
            f"Status :: Got IPRD Listener error: {error_str}", 5000
        )

    def process_result(self, result: IPReport):
        # reset inactive timer
        if self.inactive.isActive():
            self.inactive.start()
        logger.debug(
            f"process_result : got {result.src_ip}, {result.src_mac}, {result.miner_sn}, {result.miner_type} from listener."
        )
        # identify miner type from src ip
        miner_type = self.asic.identify(ip=result.src_ip, miner_hint=result.port_type)
        if miner_type == MinerType.UNKNOWN:
            miner_data = MinerData(
                recv_at=int(result.updated_at),
                ip=result.src_ip,
                mac=result.src_mac,
                type=miner_type,
            ).as_dict()
        else:
            # get miner data from src ip
            alt_pwd = self.get_client_auth(miner_type=miner_type.value)
            try:
                self.asic.create_client(
                    miner_type=miner_type, ip=result.src_ip, alt_pwd=alt_pwd
                )
            except UnknownClientError as ex:
                # ignore error to at least get result
                logger.warning(f"process_result : {str(ex)}")
                pass
            miner_data = self.asic.get_miner_data()

        # in the event of an unsupported miner, return miner type hint from IP Report
        if miner_data["type"] == "N/A":
            miner_data["type"] = result.miner_type

        # check versus current listen configuration if listen filter is enabled
        if self.checkEnableListenFilter.isChecked() and miner_data["type"] not in [
            btn.text().lower()
            for btn in self.listenerConfig.buttons()
            if btn.isChecked()
        ]:
            logger.warning(
                f"process_result: received miner type {miner_data['type']} outside of enabled filter. Ignoring..."
            )
            return self.iprStatusBar.showMessage(
                f"Status :: Got miner type: {str(miner_data['type']).capitalize()} outside of listener configuration.",
                8000,
            )

        miner_data["recv_at"] = int(result.updated_at)
        miner_data["ip"] = result.src_ip
        miner_data["mac"] = (
            miner_data["mac"].lower() if miner_data["mac"] != "N/A" else result.src_mac
        )
        # update serial if IPReport has one
        if result.miner_sn:
            miner_data["serial"] = result.miner_sn
        # append IPReport data
        miner_data["ip_report"] = result.model_dump()
        # let user know that we got an error and may not have complete data
        if self.asic.client_error():
            self.iprStatusBar.showMessage(
                f"Status :: Failed to get complete miner data {result.src_ip}: {str(self.asic.client_error())}",
                5000,
            )
            return self.show_confirmation(miner_data)
        self.asic.close_client()

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
        recv_at: int = result["recv_at"]
        fw_type: str = result["firmware"]
        type_str = type.capitalize()
        if type != "unknown":
            type_str = f"{type.capitalize()} ({fw_type})"

        recv_timestamp = QDateTime.fromSecsSinceEpoch(recv_at).toString()
        if self.menu_bar.actionAlwaysOpenIPInBrowser.isChecked():
            self.open_dashboard(ip, type)
        if self.menu_bar.actionEnableIDTable.isChecked() and self.isVisible():
            logger.info("show_confirmation : populate ID table.")
            if self.menu_bar.actionEnableLiveCapture.isChecked():
                self.populate_table_row(result)
            else:
                self.populate_table_row(result, dedupe_key="mac")
            self.activateWindow()
        else:
            confirm = IPRConfirmation(self.menu_bar.actionConfirmsStayOnTop.isChecked())
            confirm.actionOpenDashboard.triggered.connect(
                lambda: self.open_dashboard(ip, type)
            )

            logger.info("show_confirmation : show IPRConfirmation.")
            confirm.lineRecvAtField.setText(recv_timestamp)
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
            case "auradine":
                client_auth = self.lineAuradinePasswd.text()
            case "vnish":
                if not self.checkUseAntminerLogin.isChecked():
                    client_auth = self.lineVnishPasswd.text()
                else:
                    client_auth = self.lineAntminerPasswd.text()
            case _:
                return None
        return client_auth

    @staticmethod
    def _coerce_recv_at(value: Any) -> int | None:
        """Normalize a recv_at value (epoch int, numeric string, or a CSV
        datetime string) to an epoch int for the typed MinerData field."""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        text = str(value)
        if text.isdigit():
            return int(text)
        # datetime string produced by a previous export
        recv_at_datetime = QDateTime.fromString(text)
        return (
            recv_at_datetime.toSecsSinceEpoch() if recv_at_datetime.isValid() else None
        )

    def _miner_from_data(self, data: dict[str, Any]) -> MinerData:
        """Build a MinerData from a stringified dict (the "N/A"-filled
        as_dict() shape used throughout the listener/import pipeline)."""
        cleaned: dict[str, Any] = {}
        for key in MinerData.model_fields:
            if key not in data:
                continue
            value = data[key]
            cleaned[key] = None if value in ("N/A", "") else value
        cleaned["recv_at"] = self._coerce_recv_at(data.get("recv_at"))
        return MinerData(**cleaned)

    def populate_table_row(
        self,
        data: dict[str, Any],
        row: int | None = None,
        dedupe_key: str | None = None,
    ) -> None:
        """
        Arguments:
            data (dict[str, Any]): stringified MinerData.
            row (int | None): optional source row to update in place.
            dedupe_key (str | None): when set (and row is None), refresh an
                existing row whose MinerData field matches instead of
                appending a duplicate (e.g. "mac" for repeat IP reports).
        """
        logger.info("populate_table : write table data.")
        miner = self._miner_from_data(data)
        if row is not None:
            self.id_model.update_row(row, miner)
        elif dedupe_key:
            before = self.id_model.rowCount()
            self.id_model.upsert(miner, key=dedupe_key)
            # only follow the view to the bottom when a new row was appended
            if self.id_model.rowCount() > before:
                self.tableIPRID.scrollToBottom()
        else:
            self.id_model.append(miner)
            self.tableIPRID.scrollToBottom()

    def retrieve_miner_from_table(
        self, row: int
    ) -> tuple[str, MinerType, MinerFirmware]:
        miner = self.id_model.miner_at(row)
        ip_addr = miner.ip
        miner_type = (
            miner.type
            if isinstance(miner.type, MinerType)
            else MinerType.from_value(str(miner.type or ""))
        )
        fw_type = (
            miner.firmware
            if isinstance(miner.firmware, MinerFirmware)
            else MinerFirmware.from_value(str(miner.firmware or ""))
        )

        match fw_type:
            case MinerFirmware.LUX_OS:
                miner_type = MinerType.LUX_OS
            case MinerFirmware.VNISH:
                miner_type = MinerType.VNISH
            case _:
                pass
        return ip_addr, miner_type, fw_type

    def handle_widget_action(self, col: int, row: int) -> None:
        # col/row come from IPRActionDelegate.action_clicked (source row)
        match col:
            case _ if col == COL_REFRESH:
                self.refresh_miner(row)
            case _ if col == COL_LOCATE:
                self.locate_miner(row)
            case _:
                return

    def locate_miner(self, row: int):
        ip_addr, miner_type, fw_type = self.retrieve_miner_from_table(row)
        if self.asic.locate_timer and self.asic.locate_timer.isActive():
            return logger.warning(
                "locate_miner : already locating a miner. Ignoring..."
            )
        logger.info(f" locate miner {ip_addr}.")
        match miner_type:
            case MinerType.VOLCMINER | MinerType.HIVEGPU:
                logger.error(
                    f"locate_miner : {miner_type.value} is currently not supported."
                )
                return self.iprStatusBar.showMessage(
                    f"Status :: Failed to locate miner: {miner_type.value.capitalize()} is currently not supported.",
                    5000,
                )
        alt_pwd = self.get_client_auth(miner_type.value)
        try:
            self.asic.create_client(miner_type=miner_type, ip=ip_addr, alt_pwd=alt_pwd)
        except UnknownClientError as ex:
            logger.error(f"locate_miner : {str(ex)}")
            return self.iprStatusBar.showMessage(
                f"Status :: Failed action: {str(ex)}", 5000
            )
        self.asic.locate_miner()
        if self.asic.client_error():
            return self.iprStatusBar.showMessage(
                f"Status :: Failed to locate miner: {str(self.asic.client_error())}",
                5000,
            )
        self.iprStatusBar.showMessage(
            f"Status :: Locating miner: {ip_addr}...",
            self.miner_locate_duration,
        )

    def refresh_miner(self, row: int):
        ip_addr, miner_type, fw_type = self.retrieve_miner_from_table(row)
        logger.info(f" refresh miner {ip_addr}.")
        alt_pwd = self.get_client_auth(miner_type.value)
        try:
            self.asic.create_client(miner_type=miner_type, ip=ip_addr, alt_pwd=alt_pwd)
        except UnknownClientError as ex:
            logger.error(f"refresh_miner : {str(ex)}")
            return self.iprStatusBar.showMessage(
                f"Status :: Failed action: {str(ex)}", 5000
            )
        miner_data = self.asic.get_miner_data()
        if self.asic.client_error():
            return self.iprStatusBar.showMessage(
                f"Status :: Failed to get complete miner data {ip_addr}: {str(self.asic.client_error())}",
                5000,
            )
        self.asic.close_client()
        miner_data["recv_at"] = int(time.time())
        miner_data["ip"] = ip_addr
        miner_data["mac"] = (
            miner_data["mac"].lower() if miner_data["mac"] != "N/A" else "N/A"
        )
        self.populate_table_row(miner_data, row)
        self.iprStatusBar.showMessage(
            f"Status :: Successfully refreshed {ip_addr} miner data.", 3000
        )

    def get_miner_pool(self):
        if not self.id_proxy.rowCount():
            return
        selected_ips = [
            x
            for x in self.tableIPRID.selectionModel().selectedIndexes()
            if x.column() == 3
        ]
        if not selected_ips:
            return self.iprStatusBar.showMessage(
                "Status :: Failed action: no selected IPs.", 5000
            )
        index = selected_ips[0]
        source_row = self.id_proxy.mapToSource(index).row()
        ip_addr, miner_type, fw_type = self.retrieve_miner_from_table(source_row)
        alt_pwd = self.get_client_auth(miner_type.value)
        try:
            self.asic.create_client(miner_type=miner_type, ip=ip_addr, alt_pwd=alt_pwd)
        except UnknownClientError as ex:
            logger.error(f"get_miner_pool : {str(ex)}")
            return self.iprStatusBar.showMessage(
                f"Status :: Failed action: {str(ex)}", 5000
            )
        urls, users, passwds = self.asic.get_miner_pool_conf()
        if self.asic.client_error():
            return self.iprStatusBar.showMessage(
                f"Status :: Failed to get pool config: {str(self.asic.client_error())}",
                5000,
            )
        self.asic.close_client()

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
            f"Status :: Updated {self.comboPoolPreset.currentText()} preset from {ip_addr}.",
            3000,
        )

    def update_miner_pools(self):
        passed: list[str] = []
        failed: list[str] = []
        selected_ips = self.get_selected_indexes_for_action(
            "update_miner_pools", section=3
        )
        self._app_instance.processEvents(
            QEventLoop.ProcessEventsFlag.AllEvents
            | QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents
        )
        if selected_ips is None:
            return self.iprStatusBar.showMessage(
                "Status :: Failed action: no selected IPs.", 5000
            )
        for index in selected_ips:
            source_row = self.id_proxy.mapToSource(index).row()
            ip_addr, miner_type, fw_type = self.retrieve_miner_from_table(source_row)
            miner = self.id_model.miner_at(source_row)
            macaddr = miner.mac
            serial = miner.serial
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
                worker_name = ""
                if serial and serial not in ("N/A", "Unknown"):
                    worker_name = f".{serial[-5:]}"
                elif macaddr and macaddr != "N/A":
                    worker_name = f".{macaddr.replace(':', '')[-5:]}"
                if worker_name:
                    for i in range(0, len(users)):
                        if len(users[i]):
                            users[i] = users[i] + worker_name
                else:
                    logger.warning(
                        "update_miner_pools : failed to find applicable worker name. Continuing.."
                    )
            passwds = [
                self.linePoolPasswd.text(),
                self.linePoolPasswd_2.text(),
                self.linePoolPasswd_3.text(),
            ]

            alt_pwd = self.get_client_auth(miner_type.value)
            try:
                self.asic.create_client(
                    miner_type=miner_type, ip=ip_addr, alt_pwd=alt_pwd
                )
            except UnknownClientError as ex:
                logger.error(f"update_miner_pools : {str(ex)}")
                failed.append(ip_addr)
                continue
            self.asic.update_miner_pools(urls, users, passwds)
            if self.asic.client_error():
                failed.append(ip_addr)
                continue
            self.asic.close_client()
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

    def _stop_update_threads(self):
        # stop any in-flight update check/download so their QThreads do not
        # outlive the application and abort the process on exit.
        if self.downloader and self.downloader.isRunning():
            logger.info(" cancelling in-progress update download.")
            self.downloader.cancel()
            if not self.downloader.wait(5000):
                self.downloader.terminate()
                self.downloader.wait()
        if self.update_checker and self.update_checker.isRunning():
            logger.info(" waiting for update check to finish.")
            if not self.update_checker.wait(3000):
                self.update_checker.terminate()
                self.update_checker.wait()
        if self.installer and self.installer.isRunning():
            # let the install finish; the underlying apt-get child outlives a
            # terminated thread and completes on its own.
            logger.info(" waiting for update install to finish.")
            if not self.installer.wait(3000):
                self.installer.terminate()
                self.installer.wait()

    def quit(self):
        if self.is_minimized_to_tray():
            self.toggle_visibility()
        self.sys_tray.hide()
        self._stop_update_threads()
        self.iprd.close()
        self.iprd.error.disconnect(self.show_iprd_error)
        self.iprd.result.disconnect(self.process_result)
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
