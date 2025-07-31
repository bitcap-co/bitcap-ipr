from PySide6.QtWidgets import (
    QWidget,
    QMenuBar,
)

from utils import APP_INFO


class IPR_Menubar(QMenuBar):
    def __init__(
        self,
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.__initObj()

    def __initObj(self):
        self.menuHelp = self.addMenu("Help")
        self.menuHelp.setToolTipsVisible(True)
        self.menuOptions = self.addMenu("Options")
        self.menuOptions.setToolTipsVisible(True)
        self.menuTable = self.addMenu("ID Table")
        self.menuTable.setToolTipsVisible(True)
        self.menuSettings = self.addMenu("Settings")
        self.menuSettings.setToolTipsVisible(True)
        self.menuQuit = self.addMenu("Quit")
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
            "Always open received IPs in browser"
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
        self.actionImport = self.menuTable.addAction("Import")
        self.actionImport.setEnabled(False)
        self.actionImport.setToolTip("Import existing .CSV file into the ID Table")
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
