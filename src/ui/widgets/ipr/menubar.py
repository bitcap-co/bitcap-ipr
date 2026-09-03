# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMenu,
    QMenuBar,
    QWidget,
)

from utils import IPR_METADATA


class IPRMenubar(QMenuBar):
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._init_menubar()

    def _init_menubar(self):
        self.menuHelp: QMenu = self.addMenu("Help")
        self.menuHelp.setToolTipsVisible(True)
        self.menuOptions: QMenu = self.addMenu("Options")
        self.menuOptions.setToolTipsVisible(True)
        self.menuTable: QMenu = self.addMenu("ID Table")
        self.menuTable.setToolTipsVisible(True)
        self.menuConfigurator: QMenu = self.addMenu("Configuration")
        self.menuConfigurator.setToolTipsVisible(True)
        self.menuSettings: QMenu = self.addMenu("Settings")
        self.menuSettings.setToolTipsVisible(True)
        self.menuQuit: QMenu = self.addMenu("Quit")
        self.menuQuit.setToolTipsVisible(True)

        # help
        self.actionAbout: QAction = self.menuHelp.addAction("About")
        self.actionAbout.setToolTip("Opens the about dialog.")
        self.actionOpenLog: QAction = self.menuHelp.addAction("Open Log")
        self.actionOpenLog.setToolTip("Opens log file.")
        self.actionReportIssue: QAction = self.menuHelp.addAction("Report Issue")
        self.actionReportIssue.setToolTip("Report a new issue on GitHub.")
        self.actionSourceCode: QAction = self.menuHelp.addAction("Source Code")
        self.actionSourceCode.setToolTip("Opens the GitHub repo in browser.")
        self.actionCheckForUpdates: QAction = self.menuHelp.addAction(
            "Check for Updates"
        )
        self.actionCheckForUpdates.setToolTip(
            "Check GitHub for a newer release of the app."
        )
        self.actionVersion: QAction = self.menuHelp.addAction(
            f"Version {IPR_METADATA['appversion']}"
        )
        self.actionVersion.setEnabled(False)

        # options
        self.actionAlwaysOpenIPInBrowser: QAction = self.menuOptions.addAction(
            "Always Open IP in Browser"
        )
        self.actionAlwaysOpenIPInBrowser.setCheckable(True)
        self.actionAlwaysOpenIPInBrowser.setToolTip(
            "Always open received IPs in browser."
        )
        self.actionDisableInactiveTimer: QAction = self.menuOptions.addAction(
            "Disable Inactive Timer"
        )
        self.actionDisableInactiveTimer.setCheckable(True)
        self.actionDisableInactiveTimer.setToolTip(
            "Disables inactive timer of 15 minutes. (Listens until stopped)"
        )
        self.actionConfirmsStayOnTop: QAction = self.menuOptions.addAction(
            "Confirms Stay on Top"
        )
        self.actionConfirmsStayOnTop.setCheckable(True)
        self.actionConfirmsStayOnTop.setToolTip("Show IP Confirmation windows on top.")
        self.actionAutoStartOnLaunch: QAction = self.menuOptions.addAction(
            "Auto Start on Launch"
        )
        self.actionAutoStartOnLaunch.setCheckable(True)
        self.actionAutoStartOnLaunch.setToolTip(
            "Automatically start listeners on launch. (Takes effect on next launch)"
        )
        self.actionClearTableAfterStopListen: QAction = self.menuOptions.addAction(
            "Clear ID Table When Stopped"
        )
        self.actionClearTableAfterStopListen.setCheckable(True)
        self.actionClearTableAfterStopListen.setToolTip(
            "Clear ID Table data when listener is stopped."
        )

        # table
        self.actionEnableIDTable: QAction = self.menuTable.addAction("Enable ID Table")
        self.actionEnableIDTable.setCheckable(True)
        self.actionEnableIDTable.setToolTip(
            "Stores identifying information in a table on confirmation."
        )
        self.actionEnableLiveCapture: QAction = self.menuTable.addAction(
            "Enable Live Capture"
        )
        self.actionEnableLiveCapture.setCheckable(True)
        self.actionEnableLiveCapture.setEnabled(False)
        self.actionEnableLiveCapture.setToolTip(
            "Always inserts received IP reports to a new row, reflecting history of live capture."
        )
        self.actionOpenSelectedIPs: QAction = self.menuTable.addAction(
            "Open Selected IPs"
        )
        self.actionOpenSelectedIPs.setEnabled(False)
        self.actionOpenSelectedIPs.setToolTip("Open selected IPs in browser.")
        self.actionCopySelectedElements: QAction = self.menuTable.addAction(
            "Copy Selected Elements"
        )
        self.actionCopySelectedElements.setEnabled(False)
        self.actionCopySelectedElements.setToolTip(
            "Copy selected elements to clipboard. Drag or Ctrl-click to select multiple cols/rows."
        )
        self.menuTableAction: QMenu = self.menuTable.addMenu("Table Actions")
        self.menuTableAction.setEnabled(False)
        self.menuTableAction.setToolTipsVisible(True)
        self.actionResetSort: QAction = self.menuTableAction.addAction(
            "Reset Sort Order"
        )
        self.actionResetSort.setEnabled(False)
        self.actionResetSort.setToolTip("Reset the current sort order to default.")
        self.actionResetView: QAction = self.menuTableAction.addAction("Reset View")
        self.actionResetView.setEnabled(False)
        self.actionResetView.setToolTip("Clear filter and reset sort order.")
        self.actionClearTable: QAction = self.menuTableAction.addAction("Clear Table")
        self.actionClearTable.setEnabled(False)
        self.actionClearTable.setToolTip("Clear the current data in table.")

        self.actionImport: QAction = self.menuTable.addAction("Import..")
        self.actionImport.setEnabled(False)
        self.actionImport.setToolTip("Import existing .CSV file.")
        self.actionExport: QAction = self.menuTable.addAction("Export..")
        self.actionExport.setEnabled(False)
        self.actionExport.setToolTip("Export current table as .CSV file.")

        # pools
        self.actionShowConfigurator: QAction = self.menuConfigurator.addAction(
            "Show Configurator"
        )
        self.actionShowConfigurator.setEnabled(False)
        self.actionShowConfigurator.setCheckable(True)
        self.actionShowConfigurator.setToolTip("Edit miner configuration")
        self.actionConfiguratorGetPoolConfig: QAction = self.menuConfigurator.addAction(
            "Get Miner Pool Configuration"
        )
        self.actionConfiguratorGetPoolConfig.setEnabled(False)
        self.actionConfiguratorGetPoolConfig.setToolTip(
            "Retrieve miner pool configuration."
        )
        self.actionConfiguratorSetPoolFromPreset: QAction = (
            self.menuConfigurator.addAction("Set Pool From Current Preset")
        )
        self.actionConfiguratorSetPoolFromPreset.setEnabled(False)
        self.actionConfiguratorSetPoolFromPreset.setToolTip(
            "Set pool from current preset to selected miners."
        )

        # settings
        self.actionSettings: QAction = self.menuSettings.addAction("Settings...")
        self.actionSettings.setToolTip("Change application settings.")

        # quit
        self.actionKillAllConfirmations: QAction = self.menuQuit.addAction(
            "Kill All Confirmations"
        )
        self.actionKillAllConfirmations.setToolTip("Kills all IP confirmation windows.")
        self.actionQuit: QAction = self.menuQuit.addAction("Quit")
        self.actionQuit.setToolTip("Quits app.")
