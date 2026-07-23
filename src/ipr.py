# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import logging
import os
import shlex
import shutil
import subprocess
import time
import webbrowser
from datetime import datetime
from enum import Enum, auto
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable

from pydantic import TypeAdapter, ValidationError
from PySide6.QtCore import (
    QDateTime,
    QEvent,
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
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QWidget,
)
from qasync import asyncSlot

import ui.resources  # noqa F401
from config import IPRConfig, IPRDPreset, PoolPreset
from iprabout import IPRAbout
from iprconfirmation import IPRConfirmation
from mod.ipr_asic import ASICClient, MinerResult
from mod.ipr_asic import settings as api_settings
from mod.ipr_asic.data import MinerData, MinerFirmware, MinerType
from mod.ipr_asic.errors import UnknownClientError
from mod.lm import (
    IPRDListener,
    IPRDService,
    IPRDServiceListener,
    IPReport,
    ListenerManager,
)
from mod.powermonitor import PowerMonitor
from mod.updater import (
    DebInstaller,
    UpdateChecker,
    UpdateDownloader,
    get_platform,
    select_asset,
)
from ui import Ui_MainWindow
from ui.widgets import (
    COL_ACTION,
    COL_RECV_AT,
    FILTERABLE_COLUMNS,
    ColumnFilterPopup,
    FilterHeaderView,
    IPRActionDelegate,
    IPRFilterProxyModel,
    IPRMenubar,
    IPRMessage,
    IPRPresetSelector,
    IPRProgress,
    IPRTableContextMenu,
    IPRTableModel,
    IPRTitlebar,
    MinerControlPopup,
)
from utils import (
    CURR_PLATFORM,
    IPR_METADATA,
    deep_update,
    get_download_dir,
    get_log_dir,
)

logger = logging.getLogger(__name__)

# px band along the frameless window border that triggers an edge/corner resize
RESIZE_MARGIN = 6
IPRD_DISCOVERY_TIMEOUT_MS = 10_000


class ListenState(Enum):
    """Persistent state of the listening backend, reflected in the status bar."""

    READY = auto()  # idle, not listening
    LISTENING = auto()  # ListenerManager UDP listeners active
    DISCOVERING = auto()  # browsing for an iprd service over mDNS
    CONNECTING = auto()  # iprd socket connecting/subscribing
    SUBSCRIBED = auto()  # iprd connected and subscribed to the stream
    RECONNECTING = auto()  # iprd connection lost, retrying


class IPR(QMainWindow, Ui_MainWindow):
    def __init__(self, stored: IPRConfig):
        logger.info(" start IPR() init.")
        super().__init__(flags=Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)
        self.config = stored
        self._app_instance = QApplication.instance()
        # frameless-window edge/corner resizing: a global event filter hit-tests
        # the window border and hands off to the OS via startSystemResize (which
        # also lets the resize participate in window snapping).
        self._active_resize_cursor: Qt.CursorShape | None = None
        self.setMouseTracking(True)
        self.centralWidget().setMouseTracking(True)
        self._app_instance.installEventFilter(self)
        # applied once on first show (Windows only) to re-enable Aero Snap
        self._snapping_enabled = False
        # re-entrancy guard for the configurator toggle (its setChecked
        # calls re-emit toggled and re-enter the slot)
        self._toggling_configurator = False
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
        self.iprd.subscribed.connect(self.on_iprd_subscribed)
        self.iprd.error.connect(self.show_iprd_error)
        self.iprd.reconnecting.connect(self.on_iprd_reconnecting)
        self.iprd.reconnect_failed.connect(self.on_iprd_reconnect_failed)
        self.iprd_discovery = IPRDServiceListener(self)
        self.iprd_discovery.service_found.connect(self.on_iprd_service_found)
        self.iprd_discovery.service_updated.connect(self.on_iprd_service_updated)
        self.iprd_discovery.service_removed.connect(self.on_iprd_service_removed)
        self.iprd_discovery.error.connect(self.on_iprd_discovery_error)
        self._discovered_iprd_service_name: str | None = None
        self.iprd_discovery_timeout = QTimer(self)
        self.iprd_discovery_timeout.setSingleShot(True)
        self.iprd_discovery_timeout.setInterval(IPRD_DISCOVERY_TIMEOUT_MS)
        self.iprd_discovery_timeout.timeout.connect(self.on_iprd_discovery_timeout)

        # pause/resume iprd reconnect around OS sleep so we don't wake the host.
        self.power = PowerMonitor(self)
        self.power.aboutToSuspend.connect(self.iprd.on_suspend)
        self.power.resumed.connect(self.iprd.on_resume)
        # whether the user currently wants the iprd backend listening. Survives a
        # reconnect give-up so we can recover when the window is reactivated
        # (e.g. resume from sleep, where the network isn't up yet for the
        # automatic retry burst). See _maybe_reconnect_iprd().
        self._iprd_listening = False
        if self._app_instance is not None:
            self._app_instance.applicationStateChanged.connect(
                self.on_application_state_changed
            )

        # status bar state: a single persistent "base" message reflects what the
        # app is currently doing; transient notifications are layered on top via
        # notify() and fall back to the base when they expire.
        self._listen_state = ListenState.READY
        self._showing_transient = False
        self._reconnect_attempt = 0
        self._reconnect_delay_ms = 0
        self._last_iprd_error = ""

        logger.info(" init mod ipr_asic.")
        self.asic = ASICClient(self)
        # tracks the in-flight locate coroutine to prevent concurrent locates
        self._locate_task: asyncio.Task | None = None
        logger.info(" init miner locate duration for 10000ms.")
        self.locate_duration_ms: int = api_settings.get("locate_duration_ms")

        # initialize IPR_Titlebar widget
        self.title_bar = IPRTitlebar(self, "BitCap IPReporter", ["min", "max", "close"])
        self.title_bar.minimize_button.clicked.connect(self.window().showMinimized)
        self.title_bar.maximize_button.clicked.connect(self.title_bar.toggle_maximize)
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
        self.menu_bar.actionShowConfigurator.toggled.connect(
            self.toggle_configurator_settings
        )
        self.menu_bar.actionConfiguratorGetPoolConfig.triggered.connect(
            self.get_miner_pool
        )
        self.menu_bar.actionConfiguratorSetPoolFromPreset.triggered.connect(
            self.update_miner_pools
        )
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
        # HiveGPU is IPR Daemon only; id has no ListenerManager port mapping
        # so it acts purely as a listen filter option.
        self.listenerConfig.addButton(self.checkListenHiveGPU, 11)
        self.listenerConfig.buttonClicked.connect(self.restart_listen)
        # listener signals
        self.pushIPRListenStart.clicked.connect(self.start_listen)
        self.pushIPRListenStop.clicked.connect(self.stop_listen)

        self.checkEnableIPRDBackend.toggled.connect(self.toggle_iprd_settings)
        self.checkEnableIPRDBackend.toggled.connect(self.restart_listen)
        self.checkEnableIPRDAutoDiscover.toggled.connect(self.toggle_iprd_settings)
        self.checkEnableIPRDAutoDiscover.toggled.connect(self.restart_listen)
        self.lineIPRDSocketAddress.editingFinished.connect(self.write_iprd_preset)
        self.lineIPRDSocketAddress.editingFinished.connect(self.restart_listen)
        self.checkIPRDAutoReconnect.toggled.connect(self.update_iprd_reconnect_settings)
        self.checkIPRDAutoReconnect.toggled.connect(self.restart_listen)
        self.spinIPRDMaxRetries.valueChanged.connect(self.restart_listen)
        self.iprd_preset = IPRPresetSelector(
            tooltip="Saved IPR Daemon socket addresses. Select one to switch instances.",
            add_tooltip="Save current socket address as a new preset",
            remove_tooltip="Remove selected preset",
        )
        iprd_preset_layout = self.iprdPresetSet.layout()
        if iprd_preset_layout:
            iprd_preset_layout.addWidget(self.iprd_preset)
        # alias the combo so the preset handlers read like the pool ones
        self.comboIPRDPreset = self.iprd_preset.combo
        self.comboIPRDPreset.currentIndexChanged.connect(self.read_iprd_preset)
        self.comboIPRDPreset.editTextChanged.connect(self.update_iprd_preset)
        self.iprd_preset.create_requested.connect(self.add_new_iprd_preset)
        self.iprd_preset.remove_requested.connect(self.remove_iprd_preset)

        # configurator
        self.configurator.hide()
        self.btnConfiguratorCancel.clicked.connect(self.toggle_configurator_settings)
        self.btnConfiguratorApply.clicked.connect(self.apply_configuration)
        self.actionTogglePoolPasswd = self.create_passwd_toggle_action(
            self.linePoolPasswd
        )
        self.actionTogglePoolPasswd2 = self.create_passwd_toggle_action(
            self.linePoolPasswd_2
        )
        self.actionTogglePoolPasswd3 = self.create_passwd_toggle_action(
            self.linePoolPasswd_3
        )
        self.pool_preset = IPRPresetSelector(combo_max_width=280)
        pool_preset_layout = self.presetSet.layout()
        if pool_preset_layout:
            pool_preset_layout.addWidget(self.pool_preset)
        # alias the combo so the existing pool-preset handlers are unchanged
        self.comboPoolPreset = self.pool_preset.combo
        self.comboPoolPreset.currentIndexChanged.connect(self.read_pool_preset)
        self.comboPoolPreset.editTextChanged.connect(self.update_pool_preset)
        self.pool_preset.create_requested.connect(self.add_new_preset)
        self.pool_preset.remove_requested.connect(self.remove_preset)
        self.actionIPRSavePreset.clicked.connect(self.write_pool_preset)
        self.actionIPRClearPreset.clicked.connect(self.clear_pool_preset)

        # initialize ID Table (headers are provided by IPRTableModel)
        self.id_model = IPRTableModel(self)
        self.id_proxy = IPRFilterProxyModel(self)
        self.id_proxy.setSourceModel(self.id_model)
        self.tableIPRID.setModel(self.id_proxy)
        # custom header: funnel dropdowns on low-cardinality columns, alongside
        # the existing click-to-select-column behaviour on the header text.
        # Installed before the setColumnWidth calls below so the widths apply to
        # this header rather than being reset when it replaces the default one.
        self.id_header = FilterHeaderView(self.tableIPRID)
        self.tableIPRID.setHorizontalHeader(self.id_header)
        # restore the section-size config setupUi applied to the default header
        # (a fresh header defaults to a larger minimum, which would clamp the
        # 15px action columns wider and upscale their icons)
        self.id_header.setMinimumSectionSize(15)
        self.id_header.setDefaultSectionSize(150)
        # action-column icons (refresh / locate) painted by a delegate
        self.id_action_delegate = IPRActionDelegate(self.tableIPRID)
        self.tableIPRID.setItemDelegateForColumn(COL_ACTION, self.id_action_delegate)
        self.id_action_delegate.action_clicked.connect(self.handle_widget_action)
        self.tableIPRID.setColumnWidth(0, 15)
        self.tableIPRID.setColumnWidth(1, 180)
        self.tableIPRID.setColumnWidth(6, 180)
        self.tableIPRID.setColumnWidth(9, 400)
        self.tableIPRID.setColumnWidth(10, 300)
        self.tableIPRID.setColumnWidth(13, 180)
        self.tableIPRID.doubleClicked.connect(self.double_click_item)
        # sorting is driven by the toolbar controls, not header clicks, so a
        # header click is free to select the column without sorting it
        self.tableIPRID.setSortingEnabled(False)
        self.id_header.setSortIndicatorShown(False)
        self.id_header.set_filterable_columns(FILTERABLE_COLUMNS)
        # right-click a header to toggle highlighting its column (left-click is
        # reserved for the funnel filter and no longer highlights)
        self.id_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.id_header.customContextMenuRequested.connect(self.toggle_column_at)
        self.id_header.filter_clicked.connect(self.open_column_filter)
        self.id_filter_popup: ColumnFilterPopup | None = None
        # vertical header: 1-based row-count column on the left. Left-click a
        # row number to select that row (default behaviour); right-click to
        # toggle highlighting the whole row (add/remove without clearing others).
        v_header = self.tableIPRID.verticalHeader()
        v_header.setVisible(True)
        v_header.setSectionsClickable(True)
        # fixed, non-resizable row height for a consistent table layout
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        v_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        v_header.customContextMenuRequested.connect(self.toggle_row_at)
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

        # action center
        self.btnBulkRefresh.setIcon(QIcon(":theme/icons/rc/refresh.png"))
        self.btnBulkRefresh.clicked.connect(self.bulk_refresh_miners)
        self.btnBulkLocate.setIcon(QIcon(":theme/icons/rc/flash.png"))
        self.btnBulkLocate.clicked.connect(self.bulk_locate_miners)
        self.btnBulkControl.setIcon(QIcon(":theme/icons/rc/wrench.png"))
        self.btnBulkControl.clicked.connect(self.open_bulk_control)
        self.btnBulkConfig.setIcon(QIcon(":theme/icons/rc/edit.png"))
        self.btnBulkConfig.clicked.connect(
            lambda: self.toggle_configurator_settings(True)
        )

        # id table context menu
        self.id_context_menu = IPRTableContextMenu(self)
        self.id_context_menu.contextActionOpenSelectedIPs.triggered.connect(
            self.open_selected_ips
        )
        self.id_context_menu.contextActionCopySelected.triggered.connect(
            self.copy_selected
        )
        self.id_context_menu.contextActionClearTable.triggered.connect(self.clear_table)
        self.id_context_menu.contextActionRefreshMiners.triggered.connect(
            self.bulk_refresh_miners
        )
        self.id_context_menu.contextActionLocateMiners.triggered.connect(
            self.bulk_locate_miners
        )
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
            self.toggle_configurator
        )
        self.id_context_menu.contextActionConfigutorGetPool.triggered.connect(
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
        self.iprStatusBar.messageChanged.connect(self._on_status_message_changed)

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
        self._show_base_status()
        self.update_preset_names()

        if self.menu_bar.actionEnableIDTable.isChecked():
            self.toggle_table_settings(True)

        if self.menu_bar.actionShowConfigurator.isChecked():
            self.toggle_configurator_settings(True)

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

    def changeEvent(self, event):
        # keep the titlebar's maximize/restore glyph correct even when the OS
        # changes the window state (e.g. drag-snap to the top edge)
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            title_bar = getattr(self, "title_bar", None)
            if title_bar is not None:
                title_bar.sync_maximize_button()
        elif event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            # the resize cursor is an app-wide override set only while active
            # (see eventFilter); clear it on deactivation so a stale resize
            # cursor doesn't linger over the unfocused window.
            self._apply_resize_cursor(None)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._snapping_enabled and CURR_PLATFORM.startswith("win"):
            self._enable_windows_snapping()
            self._snapping_enabled = True

    def _enable_windows_snapping(self):
        """Re-enable native Aero Snap for the frameless window (Windows).

        Qt strips ``WS_THICKFRAME``/``WS_MAXIMIZEBOX`` from a frameless window,
        and without them Windows won't snap it (drag-to-edge, Win+Arrow) even
        though the titlebar drag uses ``startSystemMove``. Adding the styles
        back on the HWND restores snapping; the ``FramelessWindowHint`` handling
        keeps the frame itself from being drawn.
        """
        try:
            import ctypes
            from ctypes import wintypes

            GWL_STYLE = -16
            WS_MAXIMIZEBOX = 0x00010000
            WS_THICKFRAME = 0x00040000
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOZORDER = 0x0004
            SWP_FRAMECHANGED = 0x0020

            user32 = ctypes.windll.user32
            user32.GetWindowLongW.restype = ctypes.c_long
            user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.SetWindowLongW.restype = ctypes.c_long
            user32.SetWindowLongW.argtypes = [
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_long,
            ]

            hwnd = int(self.winId())
            style = user32.GetWindowLongW(hwnd, GWL_STYLE) & 0xFFFFFFFF
            style |= WS_MAXIMIZEBOX | WS_THICKFRAME
            # SetWindowLongW takes a signed 32-bit LONG
            if style >= 0x80000000:
                style -= 0x100000000
            user32.SetWindowLongW(hwnd, GWL_STYLE, style)
            user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED,
            )
        except Exception as exc:  # pragma: no cover - platform specific
            logger.warning(f" could not enable native window snapping: {exc}")

    # frameless window resizing
    #
    # A frameless window has no native resize border, so we hit-test the mouse
    # against the window edges ourselves and delegate the actual resize to the
    # OS via QWindow.startSystemResize(). Using the system resize means the
    # drag behaves natively, including snapping.
    def _resize_edges(self, global_pos) -> Qt.Edge | None:
        if self.isMaximized() or self.isFullScreen():
            return None
        rect = self.frameGeometry()
        margin = RESIZE_MARGIN
        edges: Qt.Edge | None = None

        def add(edge: Qt.Edge) -> None:
            nonlocal edges
            edges = edge if edges is None else edges | edge

        if global_pos.x() <= rect.left() + margin:
            add(Qt.Edge.LeftEdge)
        elif global_pos.x() >= rect.right() - margin:
            add(Qt.Edge.RightEdge)
        if global_pos.y() <= rect.top() + margin:
            add(Qt.Edge.TopEdge)
        elif global_pos.y() >= rect.bottom() - margin:
            add(Qt.Edge.BottomEdge)
        return edges

    @staticmethod
    def _cursor_for_edges(edges: Qt.Edge | None) -> Qt.CursorShape | None:
        left, right = Qt.Edge.LeftEdge, Qt.Edge.RightEdge
        top, bottom = Qt.Edge.TopEdge, Qt.Edge.BottomEdge
        if edges in (left | top, right | bottom):
            return Qt.CursorShape.SizeFDiagCursor
        if edges in (right | top, left | bottom):
            return Qt.CursorShape.SizeBDiagCursor
        if edges in (left, right):
            return Qt.CursorShape.SizeHorCursor
        if edges in (top, bottom):
            return Qt.CursorShape.SizeVerCursor
        return None

    def _apply_resize_cursor(self, edges: Qt.Edge | None) -> None:
        shape = self._cursor_for_edges(edges)
        if shape == self._active_resize_cursor:
            return
        if self._active_resize_cursor is not None:
            self._app_instance.restoreOverrideCursor()
        if shape is not None:
            self._app_instance.setOverrideCursor(QCursor(shape))
        self._active_resize_cursor = shape

    def eventFilter(self, obj, event):
        if self.isActiveWindow() and not self.isMaximized():
            event_type = event.type()
            if (
                event_type == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                edges = self._resize_edges(event.globalPosition().toPoint())
                handle = self.windowHandle()
                if edges is not None and handle is not None:
                    if handle.startSystemResize(edges):
                        return True
            elif event_type == QEvent.Type.MouseMove and not (
                QApplication.mouseButtons() & Qt.MouseButton.LeftButton
            ):
                self._apply_resize_cursor(
                    self._resize_edges(event.globalPosition().toPoint())
                )
        return super().eventFilter(obj, event)

    def update_stacked_widget(self, view_index: int | None = None, *_):
        if not view_index:
            if self.menu_bar.actionShowConfigurator.isChecked():
                self.configurator.setVisible(True)
            if self.menu_bar.actionEnableIDTable.isChecked():
                self.stackedWidget.setCurrentIndex(1)
            else:
                self.stackedWidget.setCurrentIndex(0)
        elif view_index < self.stackedWidget.count():
            if self.is_minimized_to_tray():
                self.toggle_visibility()
            if self.menu_bar.actionShowConfigurator.isChecked():
                if view_index == 2:
                    self.configurator.setVisible(False)
            self.stackedWidget.setCurrentIndex(view_index)

    # status bar
    #
    # The status bar shows exactly one of two kinds of message at a time:
    #   - a persistent "base" message describing the current ListenState
    #     (Ready / Listening / Connecting / Reconnecting). It has no timeout.
    #   - a transient notification (errors, save confirmations, timeouts) shown
    #     via notify() with a timeout. When it expires Qt clears the message and
    #     messageChanged fires, restoring the base message.
    #
    # State changes update the base message but never clobber a transient that is
    # still on screen; the new base simply takes effect once the transient ends.
    def _base_status_text(self) -> str:
        """Build the persistent status message for the current ListenState."""
        if self._listen_state is ListenState.SUBSCRIBED:
            if (
                not self.checkEnableIPRDAutoDiscover.isChecked()
                and self.comboIPRDPreset.currentIndex() != -1
            ):
                curr_instance = self.config.listener.iprd.socket_presets[
                    self.comboIPRDPreset.currentIndex()
                ]
                if curr_instance.preset_name:
                    return f"Status :: Listening on instance {curr_instance.preset_name}[{self.iprd.addr.toString()}:{self.iprd.port}]..."
            return f"Status :: Listening on {self.iprd!r}..."
        if self._listen_state is ListenState.DISCOVERING:
            return "Status :: Discovering IPR Daemon instances..."
        if self._listen_state is ListenState.CONNECTING:
            return (
                f"Status :: Connecting to "
                f"{self.iprd.addr.toString()}:{self.iprd.port}..."
            )
        if self._listen_state is ListenState.RECONNECTING:
            reason = f" ({self._last_iprd_error})" if self._last_iprd_error else ""
            return (
                f"Status :: Connection lost{reason}; reconnecting "
                f"{self._reconnect_attempt}/{self.iprd.max_reconnect_attempts} "
                f"in {self._reconnect_delay_ms // 1000}s…"
            )
        if self._listen_state is ListenState.LISTENING:
            return f"Status :: Listening on 0.0.0.0[{self.lm.status}]..."
        return "Status :: Ready."

    def _show_base_status(self):
        """Display the persistent base message for the current state."""
        self._showing_transient = False
        self.iprStatusBar.showMessage(self._base_status_text())

    def set_listen_state(self, state: ListenState):
        """Update the persistent state and refresh the status bar.

        If a transient notification is currently displayed it is left alone; the
        new base message takes over once that notification expires.
        """
        self._listen_state = state
        if not self._showing_transient:
            self._show_base_status()

    def notify(self, message: str, timeout: int = 5000):
        """Show a transient status message that reverts to the base state."""
        self._showing_transient = True
        self.iprStatusBar.showMessage(message, timeout)

    def _on_status_message_changed(self, message: str):
        # Qt clears the message (empty string) when a transient times out or
        # clearMessage() is called; restore whatever the app is currently doing.
        if not message:
            self._show_base_status()

    def update_preset_names(self):
        # pool presets
        for idx in range(0, len(self.config.pool_config.pool_presets)):
            self.comboPoolPreset.insertItem(
                idx, self.config.pool_config.pool_presets[idx].preset_name
            )
        self.comboPoolPreset.setCurrentIndex(self.config.pool_config.selected_preset)
        # iprd presets
        for idx in range(0, len(self.config.listener.iprd.socket_presets)):
            self.comboIPRDPreset.insertItem(
                idx, self.config.listener.iprd.socket_presets[idx].preset_name
            )
        self.comboIPRDPreset.setCurrentIndex(self.config.listener.iprd.selected_preset)

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
        self.checkListenHiveGPU.setChecked(self.config.listen_for.hivegpu)
        self.checkEnableIPRDBackend.setChecked(self.config.listener.iprd.enable_iprd)
        self.checkEnableIPRDAutoDiscover.setChecked(
            self.config.listener.iprd.auto_discover
        )
        self.lineIPRDSocketAddress.setText(self.config.listener.iprd.socket_addr)
        self.checkIPRDAutoReconnect.setChecked(self.config.listener.iprd.auto_reconnect)
        self.spinIPRDMaxRetries.setValue(
            self.config.listener.iprd.max_reconnect_attempts
        )
        self.toggle_iprd_settings()

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
        self.menu_bar.actionShowConfigurator.setChecked(
            self.config.instance.views.show_configurator
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
                "showConfigurator": self.menu_bar.actionShowConfigurator.isChecked(),
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
                "hivegpu": self.checkListenHiveGPU.isChecked(),
            },
            "iprd": {
                "enableIPRD": self.checkEnableIPRDBackend.isChecked(),
                "autoDiscover": self.checkEnableIPRDAutoDiscover.isChecked(),
                "socketAddress": self.lineIPRDSocketAddress.text(),
                "autoReconnect": self.checkIPRDAutoReconnect.isChecked(),
                "maxReconnectAttempts": self.spinIPRDMaxRetries.value(),
                "selectedSocketPreset": self.comboIPRDPreset.currentIndex(),
                "socketPresets": self.update_current_iprd_preset_to_config(),
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
            self.notify("Status :: Failed to update configuration!", 5000)
            return

        self.notify("Status :: Updated settings to config.", 1000)

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
            self.toggle_configurator()
            # reset pool presets
            self.clear_pool_preset()
            self.comboPoolPreset.clear()
            # reset iprd socket presets
            self.comboIPRDPreset.clear()
            self.read_settings()
            self.update_inactive_timer()
            self.update_miner_locate_duration()
            self.update_stacked_widget()
            self.notify("Status :: Successfully restored to default settings.", 5000)

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
        self.notify("Status :: successfully wrote pool preset.", 3000)

    def clear_pool_preset(self):
        for child in self.poolConfigurator.children():
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
        self.locate_duration_ms = self.spinLocateDuration.value() * 1000
        api_settings.update("locate_duration_ms", self.locate_duration_ms)
        logger.info(f" update miner locate duration: {self.locate_duration_ms}ms.")

    def update_inactive_timer_settings(self):
        if self.checkUseCustomTimeout.isChecked():
            self.spinInactiveTimeout.setEnabled(True)
        else:
            self.spinInactiveTimeout.setValue(self.spinInactiveTimeout.minimum())
            self.spinInactiveTimeout.setEnabled(False)

    def toggle_iprd_settings(self):
        # Discovery replaces manual endpoint selection while it is enabled.
        enabled = self.checkEnableIPRDBackend.isChecked()
        auto_discover = enabled and self.checkEnableIPRDAutoDiscover.isChecked()
        self.checkEnableIPRDAutoDiscover.setEnabled(enabled)
        self.iprd_preset.setEnabled(enabled and not auto_discover)
        self.lineIPRDSocketAddress.setEnabled(enabled and not auto_discover)
        self.checkIPRDAutoReconnect.setEnabled(enabled)
        self.update_iprd_reconnect_settings()

        if auto_discover:
            self.iprd_discovery.start()
        else:
            self.iprd_discovery_timeout.stop()
            self.iprd_discovery.stop()
            self._discovered_iprd_service_name = None

    def update_iprd_reconnect_settings(self):
        # max retries only applies when the backend and auto-reconnect are both on.
        self.spinIPRDMaxRetries.setEnabled(
            self.checkEnableIPRDBackend.isChecked()
            and self.checkIPRDAutoReconnect.isChecked()
        )

    def update_current_iprd_preset_to_config(self) -> list[dict[str, str]]:
        presets = TypeAdapter(list[IPRDPreset])
        saved: list[dict[str, str]] = presets.dump_python(
            self.config.listener.iprd.socket_presets, by_alias=True
        )
        current_index = self.comboIPRDPreset.currentIndex()
        if (
            self.checkEnableIPRDAutoDiscover.isChecked()
            or not len(saved)
            or current_index < 0
        ):
            return saved
        saved[current_index]["preset_name"] = self.comboIPRDPreset.currentText()
        saved[current_index]["socket_addr"] = self.lineIPRDSocketAddress.text()
        return saved

    def update_iprd_preset(self, preset_name: str):
        current_index = self.comboIPRDPreset.currentIndex()
        if current_index < 0:
            return
        self.comboIPRDPreset.setItemText(current_index, preset_name)

    def add_new_iprd_preset(self, *_, preset: IPRDPreset | None = None) -> None:
        iprd = self.config.listener.iprd
        index = len(iprd.socket_presets)
        if preset is None:
            preset = IPRDPreset(
                preset_name="New Preset",
                socket_addr=self.lineIPRDSocketAddress.text(),
            )
        iprd.socket_presets.append(preset)
        iprd.selected_preset = index
        self.config.write()

        self.comboIPRDPreset.insertItem(index, preset.preset_name)
        self.comboIPRDPreset.setCurrentIndex(index)
        self.comboIPRDPreset.setCurrentText(preset.preset_name)
        self.comboIPRDPreset.lineEdit().setFocus()
        self.comboIPRDPreset.lineEdit().selectAll()

    def remove_iprd_preset(self) -> None:
        iprd = self.config.listener.iprd
        index = self.comboIPRDPreset.currentIndex()
        if index < 0 or not len(iprd.socket_presets):
            return
        iprd.socket_presets.pop(index)
        self.comboIPRDPreset.removeItem(index)
        iprd.selected_preset = self.comboIPRDPreset.currentIndex()
        if self.comboIPRDPreset.currentIndex() == -1:
            self.lineIPRDSocketAddress.clear()
        self.config.write()

    def read_iprd_preset(self, index: int) -> None:
        presets = self.config.listener.iprd.socket_presets
        if index < 0 or index >= len(presets):
            return
        self.lineIPRDSocketAddress.setText(presets[index].socket_addr)
        # switch the live connection over to the newly selected instance.
        self.restart_listen()

    def write_iprd_preset(self) -> None:
        iprd = self.config.listener.iprd
        index = self.comboIPRDPreset.currentIndex()
        if index < 0 or index >= len(iprd.socket_presets):
            return
        preset = iprd.socket_presets[index]
        new_addr = self.lineIPRDSocketAddress.text()
        new_name = self.comboIPRDPreset.currentText()
        if preset.socket_addr == new_addr and preset.preset_name == new_name:
            return
        preset.socket_addr = new_addr
        preset.preset_name = new_name
        iprd.selected_preset = index
        self.config.write()

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
            self.menu_bar.actionShowConfigurator.setChecked(enabled)
        self.menu_bar.actionShowConfigurator.setEnabled(enabled)

    def toggle_configurator_settings(self, enabled: bool):
        self.menu_bar.actionConfiguratorGetPoolConfig.setEnabled(enabled)
        self.menu_bar.actionConfiguratorSetPoolFromPreset.setEnabled(enabled)
        self.toggle_configurator(enabled)

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
        self.notify("Status :: Checking for updates...", 3000)
        self.update_checker.start()

    def on_update_available(self, release: dict):
        self.iprStatusBar.clearMessage()
        is_prerelease = release.get("prerelease", False)
        kind = "pre-release" if is_prerelease else "version"
        self.notify(
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
        self.notify("Status :: Downloading update...", 3000)
        self.downloader.start()
        self.download_dialog.show()

    def _close_download_dialog(self):
        if self.download_dialog:
            self.download_dialog.close()
            self.download_dialog = None

    def on_download_complete(self, path: str):
        self._close_download_dialog()
        self.notify("Status :: Update downloaded.", 3000)
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
        self.notify("Status :: Download failed.", 5000)
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
        self.notify("Status :: Installing update...", 3000)
        self.installer.start()
        self.install_dialog.show()

    def _close_install_dialog(self):
        if self.install_dialog:
            self.install_dialog.close()
            self.install_dialog = None

    def on_install_complete(self, version: str):
        self._close_install_dialog()
        self.notify("Status :: Update installed.", 3000)
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
        self.notify("Status :: Install failed.", 5000)
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
        self.notify("Status :: Up to date.", 3000)
        if not self._update_check_silent:
            IPRMessage(
                self,
                "No Updates",
                f"You are running the latest version ({current}).",
            ).exec()

    def on_update_error(self, error: str) -> None:
        self.iprStatusBar.clearMessage()
        self.notify("Status :: Failed to check for updates.", 5000)
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
            case 2:  # ip column
                source_row = self.id_proxy.mapToSource(model_index).row()
                miner = self.id_model.miner_at(source_row)
                self.open_dashboard(model_index.data(), miner.type)
            case 6:  # serial column
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
        self.notify(status_msg, 3000)
        return selected

    def get_action_target_rows(self, action: str) -> list[int]:
        """Resolve the source rows a bulk action should operate on.

        Uses the current IP-column selection, or falls back to every
        currently visible (filtered) row when nothing is selected. Returns
        an empty list when the table has no rows. This is the seam the
        future Global Action Center toolbar will call.
        """
        rows = self.id_proxy.rowCount()
        if not rows:
            return []
        selected = [
            x
            for x in self.tableIPRID.selectionModel().selectedIndexes()
            if x.column() == 2
        ]
        if selected:
            source_rows = [self.id_proxy.mapToSource(x).row() for x in selected]
        else:
            source_rows = [
                self.id_proxy.mapToSource(self.id_proxy.index(r, 2)).row()
                for r in range(rows)
            ]
        scope = "selected" if selected else "all"
        logger.info(
            f"{action} : running action for {len(source_rows)} ({scope}) miners..."
        )
        self.notify(
            f"Status :: Running action: {action} for {len(source_rows)} ({scope}) miners...",
            3000,
        )
        return source_rows

    def open_selected_ips(self):
        if not self.id_proxy.rowCount():
            return
        selected_ips = [
            x
            for x in self.tableIPRID.selectionModel().selectedIndexes()
            if x.column() == 2
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
                    case 0:  # ignore action column
                        continue
                    case 2:  # ip
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
        self.notify("Status :: Copied elements to clipboard.", 3000)

    def _toggle_selection(self, indexes: list[QModelIndex]):
        """Select every index, or clear them if all are already selected.

        Giving an explicit un-highlight and letting rows/columns stay
        highlighted independently.
        """
        if not indexes:
            return
        selection_model = self.tableIPRID.selectionModel()
        fully_selected = all(selection_model.isSelected(index) for index in indexes)
        flag = (
            QItemSelectionModel.SelectionFlag.Deselect
            if fully_selected
            else QItemSelectionModel.SelectionFlag.Select
        )
        for index in indexes:
            selection_model.select(index, flag)

    def toggle_column_at(self, pos):
        """Right-click a column header to toggle highlighting that column."""
        section = self.id_header.logicalIndexAt(pos)
        # skip invalid hits and the icon-only action columns (no cell content)
        if section < COL_RECV_AT:
            return
        rows = self.id_proxy.rowCount()
        self._toggle_selection(
            [self.id_proxy.index(row, section) for row in range(rows)]
        )

    def toggle_row_at(self, pos):
        """Right-click a row header to toggle highlighting that whole row."""
        row = self.tableIPRID.verticalHeader().logicalIndexAt(pos)
        if row < 0:
            return
        columns = self.id_proxy.columnCount()
        self._toggle_selection(
            [self.id_proxy.index(row, col) for col in range(columns)]
        )

    def open_column_filter(self, section: int):
        """Pop up the value checklist for a filterable header column."""
        title = self.id_model.headerData(
            section, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )
        values = self.id_model.distinct_values(section)
        popup = ColumnFilterPopup(
            str(title), values, self.id_proxy.column_filter(section), self
        )
        popup.applied.connect(
            lambda labels, col=section, choices=values: self._apply_column_filter(
                col, labels, choices
            )
        )
        popup.cleared.connect(lambda col=section: self._apply_column_filter(col, None))
        self.id_filter_popup = popup
        popup.show_at(self.id_header.filter_anchor(section))

    def _apply_column_filter(
        self, section: int, labels: list[str] | None, choices: list[str] | None = None
    ):
        # all values checked is equivalent to no filter; keep the header glyph
        # indicator in sync with what the proxy is actually filtering on.
        if labels is not None and choices is not None and len(labels) == len(choices):
            labels = None
        self.id_proxy.set_column_filter(section, labels)
        self.id_header.set_active_columns(self.id_proxy.active_filter_columns())

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
        # clear the text filter and every per-column filter, then return the
        # sort to its default
        self.lineIDTableFilter.clear()
        self.id_proxy.clear_column_filters()
        self.id_header.set_active_columns(self.id_proxy.active_filter_columns())
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
        else:
            logger.error(f"import_table : failed to read file {file_name}.")
            self.notify("Status :: Failed to import table.", 5000)
            return

    def export_table(self):
        logger.info("export table.")
        rows = self.id_proxy.rowCount()
        cols = self.id_proxy.columnCount()
        if not rows:
            return
        out = "RECV_AT,IP,MAC,TYPE,SUBTYPE,SERIAL,ALGORITHM,HOSTNAME,STRATUM_URL,USERNAME,WORKER_NAME,FIRMWARE,FW_VERSION,PLATFORM\n"
        for i in range(rows):
            # skip the action column; write data columns in display order
            for j in range(1, cols):
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
        self.notify(f"Status :: Wrote table as .CSV to {p}.", 3000)

    def toggle_configurator(self, enabled: bool = False):
        # setChecked() below re-emits toggled and re-enters this slot; the guard
        # keeps the one-off window resize from being applied more than once.
        if self._toggling_configurator:
            return
        self._toggling_configurator = True
        try:
            self.menu_bar.actionShowConfigurator.setChecked(enabled)
            self.id_context_menu.contextActionConfiguratorShowHide.setChecked(enabled)
            self.id_context_menu.contextActionConfigutorGetPool.setEnabled(enabled)
            self.id_context_menu.contextActionConfiguratorSetPools.setEnabled(enabled)
            if enabled == (not self.configurator.isHidden()):
                return  # already in the requested state; nothing to resize
            # grow/shrink the window by exactly the configurator's own height so
            # the rest of the layout keeps its size
            delta = self.configurator.sizeHint().height()
            self.configurator.setVisible(enabled)
            # Only resize for a live user toggle. During start-up the window
            # isn't shown yet and a restored geometry already accounts for the
            # configurator, so growing again would double-count. When
            # maximized/snapped, leave the size to the OS and let the layout
            # absorb the configurator instead of fighting the state.
            if self.isVisible() and not (self.isMaximized() or self.isFullScreen()):
                if enabled:
                    available = self.screen().availableGeometry().height()
                    height = min(self.height() + delta, available)
                else:
                    height = max(self.height() - delta, self.minimumHeight())
                self.resize(self.width(), height)
        finally:
            self._toggling_configurator = False

    def apply_configuration(self) -> None:
        match self.tabConfigurator.currentIndex():
            case 0:
                self.update_miner_pools()
            case _:
                return

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
            self.notify("Status :: Failed to start listeners. No listeners configured")
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
            self._last_iprd_error = ""
            self._iprd_listening = False
            self.set_listen_state(ListenState.LISTENING)
        else:
            self._iprd_listening = True
            if self.checkEnableIPRDAutoDiscover.isChecked():
                self.iprd_discovery.start()
                service = self._selected_iprd_service()
                if service is None:
                    self._last_iprd_error = ""
                    self._wait_for_iprd_service()
                else:
                    self._connect_to_iprd_service(service)
            else:
                try:
                    addr, port_text = self.lineIPRDSocketAddress.text().rsplit(":", 1)
                    addr = addr.strip("[]")
                    port = int(port_text)
                except ValueError:
                    self.stop_listen()
                    logger.error(
                        "start_listen : failed to start IPRD listener! Invalid socket address."
                    )
                    return self.notify(
                        "Status :: Failed to start IPRD Listener: Invalid socket address."
                    )
                else:
                    self._start_iprd_connection(addr, port)

        listen_status = self._base_status_text().removeprefix("Status :: ")
        logger.info(f"start_listen : {listen_status}")
        if self.is_minimized_to_tray():
            self.sys_tray.showMessage(
                "IPR Listener: Start",
                f"{listen_status}",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    def stop_listen(
        self, timeout: bool = False, restart: bool = False, from_giveup: bool = False
    ):
        logger.info(" stop listeners.")
        # A reconnect give-up stops the socket but keeps the user's intent to be
        # listening, so reactivating the window can recover (see
        # _maybe_reconnect_iprd). Any other stop clears that intent.
        if not from_giveup:
            self._iprd_listening = False
        self.iprd_discovery_timeout.stop()
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
        # always stop iprd: during a reconnect loop active is False but the retry
        # timer is still running, so a guard on active would leave it retrying.
        self.iprd.stop()
        # back to idle; any transient below will revert here once it expires.
        self._last_iprd_error = ""
        self.set_listen_state(ListenState.READY)
        if timeout:
            logger.warning("stop_listen : timeout.")
            self.notify("Status :: Inactive timeout. Stopped listeners")
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

    def restart_listen(self):
        if self.lm.count or self.iprd.active or self._iprd_listening:
            logger.info(" restart listeners.")
            self.stop_listen(restart=True)
            self.start_listen()

    def _selected_iprd_service(self) -> IPRDService | None:
        if self._discovered_iprd_service_name is not None:
            service = self.iprd_discovery.get_service(
                self._discovered_iprd_service_name
            )
            if service is not None:
                return service
        services = self.iprd_discovery.services
        if not services:
            return None
        self._discovered_iprd_service_name = services[0].name
        return services[0]

    def _wait_for_iprd_service(self) -> None:
        self.iprd_discovery_timeout.start()
        self.set_listen_state(ListenState.DISCOVERING)

    def _start_iprd_connection(self, addr: str, port: int) -> None:
        self.iprd_discovery_timeout.stop()
        self.iprd.auto_reconnect = self.checkIPRDAutoReconnect.isChecked()
        self.iprd.max_reconnect_attempts = self.spinIPRDMaxRetries.value()
        self.iprd.set_socket_addr(addr, port)
        self.iprd.start()
        self._last_iprd_error = ""
        self.set_listen_state(ListenState.CONNECTING)

    def _connect_to_iprd_service(self, service: IPRDService) -> None:
        self._discovered_iprd_service_name = service.name
        address = service.address
        endpoint = (
            f"[{address}]:{service.port}"
            if ":" in address
            else f"{address}:{service.port}"
        )
        endpoint_changed = self.lineIPRDSocketAddress.text() != endpoint
        self.lineIPRDSocketAddress.setText(endpoint)
        if not self._iprd_listening or (self.iprd.active and not endpoint_changed):
            return
        self.iprd.stop()
        self._start_iprd_connection(address, service.port)

    def on_iprd_service_found(self, service: IPRDService) -> None:
        if self._discovered_iprd_service_name not in (None, service.name):
            return
        self._connect_to_iprd_service(service)

    def on_iprd_service_updated(self, service: IPRDService) -> None:
        if service.name == self._discovered_iprd_service_name:
            self._connect_to_iprd_service(service)

    def on_iprd_service_removed(self, name: str) -> None:
        if name != self._discovered_iprd_service_name:
            return
        self._discovered_iprd_service_name = None
        replacement = self._selected_iprd_service()
        if replacement is not None:
            self._connect_to_iprd_service(replacement)
            return
        self.lineIPRDSocketAddress.clear()
        if self._iprd_listening:
            self.iprd.stop()
            self._wait_for_iprd_service()

    def on_iprd_discovery_timeout(self) -> None:
        if (
            not self._iprd_listening
            or self._listen_state is not ListenState.DISCOVERING
        ):
            return
        logger.warning("IPRD discovery timed out without finding a service.")
        self.stop_listen()
        self.notify("Status :: IPRD discovery timed out. Stopped listening.")

    def on_iprd_discovery_error(self, error_str: str) -> None:
        logger.error(f"IPRD discovery error: {error_str}")
        if self.checkEnableIPRDAutoDiscover.isChecked():
            self.notify(f"Status :: IPRD discovery error: {error_str}")

    def on_iprd_subscribed(self):
        self._last_iprd_error = ""
        self.set_listen_state(ListenState.SUBSCRIBED)

    def show_iprd_error(self, error_str: str):
        # The daemon emits error() once per drop, immediately followed by
        # reconnecting(). Rather than flash a standalone error message that the
        # reconnect status would instantly overwrite, we stash the reason so it
        # can be folded into the persistent "reconnecting…" message.
        logger.error(f" received IPRD Listener error: {error_str}")
        self._last_iprd_error = error_str
        # If auto-reconnect is disabled no reconnecting() follows, so fully stop
        # the listener and surface the error.
        if not self.iprd.auto_reconnect:
            self.stop_listen()
            self.notify(f"Status :: IPRD Listener error: {error_str}. Stopped.")

    def on_iprd_reconnecting(self, attempt: int, delay_ms: int):
        self._reconnect_attempt = attempt
        self._reconnect_delay_ms = delay_ms
        self.set_listen_state(ListenState.RECONNECTING)

    def on_iprd_reconnect_failed(self):
        logger.error("IPRD reconnect failed; giving up.")
        # keep the listening intent if auto-reconnect is on so refocusing the
        # window retries (covers resume-from-sleep where the network isn't up
        # yet during the automatic retry burst).
        self.stop_listen(from_giveup=self.iprd.auto_reconnect)
        if self.is_minimized_to_tray():
            self.sys_tray.showMessage(
                "IPR Listener: Disconnected",
                "Could not reconnect to the daemon.",
                QSystemTrayIcon.MessageIcon.Critical,
                5000,
            )
        if self._iprd_listening:
            self.notify("Status :: Could not reconnect. Will retry when refocused.")
        else:
            self.notify("Status :: Could not reconnect. Stopped.")

    def on_application_state_changed(self, state: Qt.ApplicationState):
        if state is Qt.ApplicationState.ApplicationActive:
            self._maybe_reconnect_iprd()

    def _maybe_reconnect_iprd(self):
        """Recover an iprd connection that was dropped while the app was inactive
        (typically a resume from sleep whose automatic retry burst ran before the
        network was back). Triggered when the window regains focus."""
        if not self._iprd_listening or self.iprd.active:
            return
        # don't interrupt an attempt already in flight.
        if self._listen_state in (
            ListenState.CONNECTING,
            ListenState.RECONNECTING,
            ListenState.DISCOVERING,
        ):
            return
        logger.info(" app activated; retrying iprd listen.")
        self.start_listen()

    @asyncSlot(IPReport)
    async def process_result(self, result: IPReport):
        # reset inactive timer
        if self.inactive.isActive():
            self.inactive.start()
        logger.debug(
            f"process_result : got {result.src_ip}, {result.src_mac}, {result.miner_sn}, {result.miner_type} from listener."
        )
        # identify miner type from src ip
        miner_type = await self.asic.identify(
            ip=result.src_ip, miner_hint=result.port_type
        )
        error: Exception | None = None
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
            res = await self.asic.get_miner_data(
                miner_type, result.src_ip, alt_pwd=alt_pwd
            )
            miner_data = res.data
            # an unsupported backend is non-fatal; still surface partial data
            if isinstance(res.error, UnknownClientError):
                logger.warning(f"process_result : {str(res.error)}")
            else:
                error = res.error

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
            return self.notify(
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
        if error:
            self.notify(
                f"Status :: Failed to get complete miner data {result.src_ip}: {str(error)}",
                5000,
            )
            return self.show_confirmation(miner_data)

        logger.debug(f"process_result: got miner data: {miner_data}.")
        self.notify(
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
            case _ if col == COL_ACTION:
                self.open_miner_control(row)
            case _:
                return

    def open_miner_control(self, row: int) -> None:
        # single-use control popup anchored under the clicked action cell
        popup = MinerControlPopup(self)
        popup.action_selected.connect(
            lambda key, r=row: self._dispatch_miner_control(r, key)
        )
        self.id_control_popup = popup
        proxy_index = self.id_proxy.mapFromSource(self.id_model.index(row, COL_ACTION))
        rect = self.tableIPRID.visualRect(proxy_index)
        anchor = self.tableIPRID.viewport().mapToGlobal(rect.bottomLeft())
        popup.show_at(anchor)

    def _dispatch_miner_control(self, row: int, key: str) -> None:
        match key:
            case "refresh":
                asyncio.ensure_future(self.refresh_miner(row))
            case "locate":
                asyncio.ensure_future(self.locate_miner(row))
            case "start" | "stop" | "restart" | "reboot":
                asyncio.ensure_future(self._control_miner(row, key))
            case _:
                logger.warning(f"_dispatch_miner_control : unknown action '{key}'.")

    async def _control_miner(self, row: int, key: str) -> None:
        ip_addr, miner_type, _ = self.retrieve_miner_from_table(row)
        logger.info(f"_control_miner : '{key}' requested for {ip_addr}.")
        alt_pwd = self.get_client_auth(miner_type.value)
        operation = getattr(self.asic, f"{key}_miner")
        res = await operation(miner_type, ip_addr, alt_pwd=alt_pwd)
        if res.error:
            logger.error(f"_control_miner : {key} failed for {ip_addr}: {res.error}")
            return self.notify(
                f"Status :: Failed to {key} {ip_addr}: {str(res.error)}",
                5000,
            )
        self.notify(
            f"Status :: Successfully completed {key} for {ip_addr}.",
            3000,
        )

    def open_bulk_control(self) -> None:
        # same control popup as the per-row glyph, anchored under the toolbar
        # button; actions apply to the selection (or all visible rows)
        popup = MinerControlPopup(self)
        popup.action_selected.connect(self._dispatch_bulk_control)
        self.id_control_popup = popup
        btn = self.btnBulkControl
        anchor = btn.mapToGlobal(btn.rect().bottomLeft())
        popup.show_at(anchor)

    def _dispatch_bulk_control(self, key: str) -> None:
        match key:
            case "refresh":
                self.bulk_refresh_miners()
            case "locate":
                self.bulk_locate_miners()
            case "start" | "stop" | "restart" | "reboot":
                asyncio.ensure_future(self._bulk_control_miners(key))
            case _:
                logger.warning(f"_dispatch_bulk_control : unknown action '{key}'.")

    async def _bulk_control_miners(self, key: str) -> None:
        action = key.capitalize()
        rows = self.get_action_target_rows(action)
        if not rows:
            return self.notify(
                f"Status :: Failed action: no miners to {key}.",
                5000,
            )

        operation = getattr(self.asic, f"{key}_miner")

        def make_coro(row, ip_addr, miner_type, fw_type, alt_pwd):
            return operation(miner_type, ip_addr, alt_pwd=alt_pwd)

        await self._run_bulk_action(action, rows, make_coro)

    async def _run_bulk_action(
        self,
        action: str,
        rows: list[int],
        coro_factory: Callable[[int, str, MinerType, MinerFirmware, str | None], Any],
        *,
        on_success: Callable[[int, str, MinerResult], None] | None = None,
    ) -> None:
        """Fan a per-miner async operation out over ``rows`` concurrently.

        ``coro_factory(row, ip, miner_type, fw_type, alt_pwd)`` returns the
        coroutine to run for a row, or ``None`` to skip that row. Results are
        gathered, classified into passed/failed with the same rule as
        ``update_miner_pools``, and summarised via ``notify``. ``on_success``
        (if given) runs for each miner whose result carried no error.
        """
        ips: list[str] = []
        task_rows: list[int] = []
        tasks = []
        for row in rows:
            ip_addr, miner_type, fw_type = self.retrieve_miner_from_table(row)
            alt_pwd = self.get_client_auth(miner_type.value)
            coro = coro_factory(row, ip_addr, miner_type, fw_type, alt_pwd)
            if coro is None:
                continue
            ips.append(ip_addr)
            task_rows.append(row)
            tasks.append(coro)
        if not tasks:
            return

        if action == "Locate":
            self.notify(
                f"Status :: {action} started for {self.locate_duration_ms / 1000}s.",
                self.locate_duration_ms,
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        passed: list[str] = []
        failed: list[str] = []
        for row, ip_addr, res in zip(task_rows, ips, results):
            if isinstance(res, Exception) or res.error is not None:
                err = res if isinstance(res, Exception) else res.error
                logger.error(f"{action} : {ip_addr} : {str(err)}")
                failed.append(ip_addr)
            else:
                if on_success is not None:
                    on_success(row, ip_addr, res)
                passed.append(ip_addr)

        logger.info(
            f"status for action '{action}': passed - {passed}, failed - {failed}"
        )
        if failed:
            return self.notify(f"Status :: {action} failed for {failed}.", 5000)
        self.notify(f"Status :: {action} succeeded for {len(passed)} miners.", 3000)

    async def _locate_rows(self, rows: list[int]) -> None:
        """Blink the fault light on every miner in ``rows`` concurrently.

        Unsupported miners (Volcminer/HiveGPU) are skipped. The cancel-safe
        blink-off is handled inside ``ASICClient.locate_miner``'s ``finally``,
        so cancelling this batch turns every LED back off.
        """

        def make_coro(row, ip_addr, miner_type, fw_type, alt_pwd):
            if miner_type in (MinerType.VOLCMINER, MinerType.HIVEGPU):
                logger.error(f"locate : {miner_type.value} is currently not supported.")
                self.notify(
                    f"Status :: Skipping {ip_addr}: {miner_type.value.capitalize()} locate is not supported.",
                    5000,
                )
                return None
            return self.asic.locate_miner(miner_type, ip_addr, alt_pwd=alt_pwd)

        await self._run_bulk_action("Locate", rows, make_coro)

    async def _start_locate(self, rows: list[int]) -> None:
        """Launch a locate batch, cancelling any locate already in flight.

        A single cancellable ``self._locate_task`` backs both the per-row
        glyph and the bulk action (cancel-and-replace guard).
        """
        if not rows:
            return
        if self._locate_task and not self._locate_task.done():
            self._locate_task.cancel()
            try:
                await self._locate_task
            except asyncio.CancelledError:
                pass
        self._locate_task = asyncio.ensure_future(self._locate_rows(rows))
        try:
            await self._locate_task
        except asyncio.CancelledError:
            return

    async def locate_miner(self, row: int):
        # single-row locate is the N=1 case of the shared locate engine
        await self._start_locate([row])

    @asyncSlot()
    async def bulk_locate_miners(self):
        rows = self.get_action_target_rows("Locate")
        if not rows:
            return self.notify("Status :: Failed action: no miners to locate.", 5000)
        await self._start_locate(rows)

    async def refresh_miner(self, row: int):
        ip_addr, miner_type, fw_type = self.retrieve_miner_from_table(row)
        logger.info(f" refresh miner {ip_addr}.")
        alt_pwd = self.get_client_auth(miner_type.value)
        res = await self.asic.get_miner_data(miner_type, ip_addr, alt_pwd=alt_pwd)
        if isinstance(res.error, UnknownClientError):
            logger.error(f"refresh_miner : {str(res.error)}")
            return self.notify(f"Status :: Failed action: {str(res.error)}", 5000)
        if res.error:
            return self.notify(
                f"Status :: Failed to get complete miner data {ip_addr}: {str(res.error)}",
                5000,
            )
        miner_data = res.data
        miner_data["recv_at"] = int(time.time())
        miner_data["ip"] = ip_addr
        miner_data["mac"] = (
            miner_data["mac"].lower() if miner_data["mac"] != "N/A" else "N/A"
        )
        self.populate_table_row(miner_data, row)
        self.notify(f"Status :: Successfully refreshed {ip_addr} miner data.", 3000)

    @asyncSlot()
    async def bulk_refresh_miners(self):
        rows = self.get_action_target_rows("Refresh")
        if not rows:
            return self.notify("Status :: Failed action: no miners to refresh.", 5000)

        def make_coro(row, ip_addr, miner_type, fw_type, alt_pwd):
            return self.asic.get_miner_data(miner_type, ip_addr, alt_pwd=alt_pwd)

        def on_success(row, ip_addr, res):
            miner_data = res.data
            miner_data["recv_at"] = int(time.time())
            miner_data["ip"] = ip_addr
            miner_data["mac"] = (
                miner_data["mac"].lower() if miner_data["mac"] != "N/A" else "N/A"
            )
            self.populate_table_row(miner_data, row)

        await self._run_bulk_action("Refresh", rows, make_coro, on_success=on_success)

    @asyncSlot()
    async def get_miner_pool(self):
        if not self.id_proxy.rowCount():
            return
        selected_ips = [
            x
            for x in self.tableIPRID.selectionModel().selectedIndexes()
            if x.column() == 2
        ]
        if not selected_ips:
            return self.notify("Status :: Failed action: no selected IPs.", 5000)
        index = selected_ips[0]
        source_row = self.id_proxy.mapToSource(index).row()
        ip_addr, miner_type, fw_type = self.retrieve_miner_from_table(source_row)
        alt_pwd = self.get_client_auth(miner_type.value)
        res = await self.asic.get_miner_pool_conf(miner_type, ip_addr, alt_pwd=alt_pwd)
        if isinstance(res.error, UnknownClientError):
            logger.error(f"get_miner_pool : {str(res.error)}")
            return self.notify(f"Status :: Failed action: {str(res.error)}", 5000)
        if res.error:
            return self.notify(
                f"Status :: Failed to get pool config: {str(res.error)}",
                5000,
            )
        urls, users, passwds = res.data.urls, res.data.users, res.data.passwds

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
        self.notify(
            f"Status :: Updated {self.comboPoolPreset.currentText()} preset from {ip_addr}.",
            3000,
        )

    @asyncSlot()
    async def update_miner_pools(self):
        passed: list[str] = []
        failed: list[str] = []
        selected_ips = self.get_selected_indexes_for_action(
            "update_miner_pools", section=2
        )
        if selected_ips is None:
            return self.notify("Status :: Failed action: no selected IPs.", 5000)

        ips: list[str] = []
        tasks = []
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
            ips.append(ip_addr)
            tasks.append(
                self.asic.update_miner_pools(
                    miner_type, ip_addr, urls, users, passwds, alt_pwd=alt_pwd
                )
            )

        # run all pool updates concurrently (keeps the UI responsive without
        # the previous manual processEvents() pump)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for ip_addr, res in zip(ips, results):
            if isinstance(res, Exception) or res.error is not None:
                err = res if isinstance(res, Exception) else res.error
                logger.error(f"update_miner_pools : {ip_addr} : {str(err)}")
                failed.append(ip_addr)
            else:
                passed.append(ip_addr)

        # action status
        logger.info(
            f"status for action 'update_miner_pools': passed - {passed}, failed - {failed}"
        )
        if len(failed) > 0:
            return self.notify(f"Status :: Failed to update pools for {failed}.", 5000)
        self.notify("Status :: Successfully updated pools.", 3000)

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
        self.notify("Status :: Killed all confirmations.", 3000)

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
        self.iprd_discovery.close()
        self.iprd.close()
        self.iprd.error.disconnect(self.show_iprd_error)
        self.iprd.result.disconnect(self.process_result)
        self.iprd.subscribed.disconnect(self.on_iprd_subscribed)
        self.iprd.reconnecting.disconnect(self.on_iprd_reconnecting)
        self.iprd.reconnect_failed.disconnect(self.on_iprd_reconnect_failed)
        self.power.aboutToSuspend.disconnect(self.iprd.on_suspend)
        self.power.resumed.disconnect(self.iprd.on_resume)
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
