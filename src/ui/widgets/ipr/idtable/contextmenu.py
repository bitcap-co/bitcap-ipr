# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QWidget


class IPRTableContextMenu(QMenu):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._init_context()

    def _init_context(self):
        self.setToolTipsVisible(True)

        self.contextActionOpenSelectedIPs: QAction = self.addAction("Open Selected IPs")
        self.contextActionOpenSelectedIPs.setToolTip(
            "Open all selected IPs in a new tab."
        )
        self.contextActionCopySelected: QAction = self.addAction("Copy selected")
        self.contextActionCopySelected.setToolTip(
            "Copy all selected cells to clipboard."
        )
        self.contextActionClearTable: QAction = self.addAction("Clear Table")
        self.contextActionClearTable.setToolTip("Clear the current data in table.")

        # miner actions
        _ = self.addSeparator()
        self.contextActionRefreshMiners: QAction = self.addAction("Refresh Miners")
        self.contextActionRefreshMiners.setToolTip(
            "Refresh data for the selected miners, or all miners when none are selected."
        )
        self.contextActionLocateMiners: QAction = self.addAction("Locate Miners")
        self.contextActionLocateMiners.setToolTip(
            "Blink the fault light on the selected miners, or all miners when none are selected."
        )
        self.menuConf: QMenu = self.addMenu("Configurator")
        self.menuConf.setToolTipsVisible(True)
        self.contextActionConfiguratorShowHide: QAction = self.menuConf.addAction(
            "Show/Hide Configurator"
        )
        self.contextActionConfiguratorShowHide.setCheckable(True)
        self.contextActionConfiguratorShowHide.setToolTip(
            "Toggle visibility of the Configurator."
        )
        self.contextActionConfigutorGetPool: QAction = self.menuConf.addAction(
            "Get Pool Configuration From Selected Miner"
        )
        self.contextActionConfigutorGetPool.setEnabled(False)
        self.contextActionConfigutorGetPool.setToolTip(
            "Retreive current pool configuration from the selected miner\n and store in selected preset."
        )
        self.contextActionConfiguratorSetPools: QAction = self.menuConf.addAction(
            "Update Pool Config From Current Preset"
        )
        self.contextActionConfiguratorSetPools.setEnabled(False)
        self.contextActionConfiguratorSetPools.setToolTip(
            "Update miner pool config from the currently selected preset."
        )

        # table actions
        _ = self.addSeparator()
        self.menuTable: QMenu = self.addMenu("Table Actions")
        self.menuTable.setToolTipsVisible(True)

        self.contextActionTableImport: QAction = self.menuTable.addAction(
            "Import Table.."
        )
        self.contextActionTableImport.setToolTip("Import existing .CSV file.")
        self.contextActionTableExport: QAction = self.menuTable.addAction(
            "Export Table.."
        )
        self.contextActionTableExport.setToolTip("Export the table to a .CSV file.")
        self.contextActionTableResetSortOrder: QAction = self.menuTable.addAction(
            "Reset Sort Order"
        )
        self.contextActionTableResetSortOrder.setToolTip(
            "Reset the current sort order to default."
        )
        self.contextActionTableResetView: QAction = self.menuTable.addAction(
            "Reset View"
        )
        self.contextActionTableResetView.setToolTip(
            "Clear filter and reset sort order."
        )
