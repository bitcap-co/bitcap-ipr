from typing import Optional
from PySide6.QtWidgets import QMenu, QWidget


class IPRTableContextMenu(QMenu):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.__initObj()

    def __initObj(self):
        self.setToolTipsVisible(True)

        self.contextActionOpenSelectedIPs = self.addAction("Open Selected IPs")
        self.contextActionOpenSelectedIPs.setToolTip(
            "Open all selected IPs in a new tab."
        )
        self.contextActionCopySelected = self.addAction("Copy selected")
        self.contextActionCopySelected.setToolTip(
            "Copy all selected cells to clipboard."
        )
        self.contextActionClearTable = self.addAction("Clear Table")
        self.contextActionClearTable.setToolTip("Clear the current data in table.")

        self.menuTable = self.addMenu("Table Actions")
        self.menuTable.setToolTipsVisible(True)
        self.menuConf = self.addMenu("Configurator")
        self.menuConf.setToolTipsVisible(True)

        self.contextActionTableImport = self.menuTable.addAction("Import Table..")
        self.contextActionTableImport.setToolTip("Import existing .CSV file")
        self.contextActionTableExport = self.menuTable.addAction("Export Table..")
        self.contextActionTableExport.setToolTip("Export the table to a .CSV file")
        self.contextActionTableResetSortOrder = self.menuTable.addAction(
            "Reset Sort Order"
        )
        self.contextActionTableResetSortOrder.setToolTip(
            "Reset the current sort order to default."
        )

        self.contextActionConfiguratorShowHide = self.menuConf.addAction(
            "Show/Hide Pool Configurator"
        )
        self.contextActionConfiguratorShowHide.setCheckable(True)
        self.contextActionConfiguratorShowHide.setToolTip(
            "Toggle visibility of the Pool Configurator"
        )
        self.contextActionConfiguratorGetPool = self.menuConf.addAction(
            "Get Pool Config From Selected Miner"
        )
        self.contextActionConfiguratorGetPool.setEnabled(False)
        self.contextActionConfiguratorGetPool.setToolTip(
            'Retreive current pool config from the selected miner\n and store in "Current Buffer".'
        )
        self.contextActionConfiguratorSetPools = self.menuConf.addAction(
            "Update Pool Config From Current Preset"
        )
        self.contextActionConfiguratorSetPools.setEnabled(False)
        self.contextActionConfiguratorSetPools.setToolTip(
            "Update miner pool config from the currently selected preset."
        )
