# Form implementation generated from reading ui file '.\ui\MainWindow.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(501, 500)
        MainWindow.setStyleSheet("QWidget[StyleClass=\"setText\"] {\n"
"    color: rgb(238, 238, 238);\n"
"}")
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setStyleSheet("QWidget#centralwidget {\n"
"    background-color:qlineargradient(spread:pad, x1:0.500, y1:0, x2:0.500, y2:1, stop:0.5 rgba(6, 16, 31, 255), stop:1 rgba(0, 0, 0, 255));\n"
"}")
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.vwrapper = QtWidgets.QWidget(parent=self.centralwidget)
        self.vwrapper.setObjectName("vwrapper")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.vwrapper)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(parent=self.vwrapper)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.vwrapper)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy)
        self.stackedWidget.setMinimumSize(QtCore.QSize(465, 280))
        self.stackedWidget.setObjectName("stackedWidget")
        self.iprIDTable = QtWidgets.QWidget()
        self.iprIDTable.setObjectName("iprIDTable")
        self.tableWidget = QtWidgets.QTableWidget(parent=self.iprIDTable)
        self.tableWidget.setEnabled(True)
        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 465, 280))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setCornerButtonEnabled(True)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(105)
        self.stackedWidget.addWidget(self.iprIDTable)
        self.iprLogo = QtWidgets.QWidget()
        self.iprLogo.setObjectName("iprLogo")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.iprLogo)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_2 = QtWidgets.QLabel(parent=self.iprLogo)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QtCore.QSize(256, 256))
        self.label_2.setText("")
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.stackedWidget.addWidget(self.iprLogo)
        self.iprConfig = QtWidgets.QWidget()
        self.iprConfig.setObjectName("iprConfig")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.iprConfig)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_3 = QtWidgets.QLabel(parent=self.iprConfig)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setMinimumSize(QtCore.QSize(260, 30))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_3.addWidget(self.label_3)
        self.hwrapper = QtWidgets.QWidget(parent=self.iprConfig)
        self.hwrapper.setObjectName("hwrapper")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.hwrapper)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.inputIPRConfig = QtWidgets.QWidget(parent=self.hwrapper)
        self.inputIPRConfig.setObjectName("inputIPRConfig")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.inputIPRConfig)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.linePasswdField = QtWidgets.QLineEdit(parent=self.inputIPRConfig)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.linePasswdField.sizePolicy().hasHeightForWidth())
        self.linePasswdField.setSizePolicy(sizePolicy)
        self.linePasswdField.setMinimumSize(QtCore.QSize(180, 25))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.linePasswdField.setFont(font)
        self.linePasswdField.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.linePasswdField.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.linePasswdField.setObjectName("linePasswdField")
        self.verticalLayout_4.addWidget(self.linePasswdField)
        self.actionIPRSetPasswd = QtWidgets.QPushButton(parent=self.inputIPRConfig)
        self.actionIPRSetPasswd.setMinimumSize(QtCore.QSize(120, 25))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.actionIPRSetPasswd.setFont(font)
        self.actionIPRSetPasswd.setObjectName("actionIPRSetPasswd")
        self.verticalLayout_4.addWidget(self.actionIPRSetPasswd)
        self.horizontalLayout.addWidget(self.inputIPRConfig)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.verticalLayout_3.addWidget(self.hwrapper)
        self.stackedWidget.addWidget(self.iprConfig)
        self.verticalLayout.addWidget(self.stackedWidget)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.inputIPRButtons = QtWidgets.QWidget(parent=self.vwrapper)
        self.inputIPRButtons.setObjectName("inputIPRButtons")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.inputIPRButtons)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.actionIPRStart = QtWidgets.QPushButton(parent=self.inputIPRButtons)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.actionIPRStart.setFont(font)
        self.actionIPRStart.setDefault(True)
        self.actionIPRStart.setObjectName("actionIPRStart")
        self.horizontalLayout_2.addWidget(self.actionIPRStart)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.actionIPRStop = QtWidgets.QPushButton(parent=self.inputIPRButtons)
        self.actionIPRStop.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.actionIPRStop.setFont(font)
        self.actionIPRStop.setObjectName("actionIPRStop")
        self.horizontalLayout_2.addWidget(self.actionIPRStop)
        self.verticalLayout.addWidget(self.inputIPRButtons)
        self.verticalLayout_2.addWidget(self.vwrapper)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 501, 22))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QtWidgets.QMenu(parent=self.menubar)
        self.menuHelp.setToolTipsVisible(True)
        self.menuHelp.setObjectName("menuHelp")
        self.menuOptions = QtWidgets.QMenu(parent=self.menubar)
        self.menuOptions.setToolTipsVisible(True)
        self.menuOptions.setObjectName("menuOptions")
        self.menuQuit = QtWidgets.QMenu(parent=self.menubar)
        self.menuQuit.setToolTipsVisible(True)
        self.menuQuit.setObjectName("menuQuit")
        self.menuTable = QtWidgets.QMenu(parent=self.menubar)
        self.menuTable.setToolTipsVisible(True)
        self.menuTable.setObjectName("menuTable")
        self.menuTableSettings = QtWidgets.QMenu(parent=self.menuTable)
        self.menuTableSettings.setToolTipsVisible(True)
        self.menuTableSettings.setObjectName("menuTableSettings")
        MainWindow.setMenuBar(self.menubar)
        self.actionVersion = QtGui.QAction(parent=MainWindow)
        self.actionVersion.setEnabled(False)
        self.actionVersion.setObjectName("actionVersion")
        self.actionAlwaysOpenIPInBrowser = QtGui.QAction(parent=MainWindow)
        self.actionAlwaysOpenIPInBrowser.setCheckable(True)
        self.actionAlwaysOpenIPInBrowser.setObjectName("actionAlwaysOpenIPInBrowser")
        self.actionQuit = QtGui.QAction(parent=MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionDisableInactiveTimer = QtGui.QAction(parent=MainWindow)
        self.actionDisableInactiveTimer.setCheckable(True)
        self.actionDisableInactiveTimer.setObjectName("actionDisableInactiveTimer")
        self.actionDisableWarningDialog = QtGui.QAction(parent=MainWindow)
        self.actionDisableWarningDialog.setCheckable(True)
        self.actionDisableWarningDialog.setObjectName("actionDisableWarningDialog")
        self.actionAutoStartOnLaunch = QtGui.QAction(parent=MainWindow)
        self.actionAutoStartOnLaunch.setCheckable(True)
        self.actionAutoStartOnLaunch.setObjectName("actionAutoStartOnLaunch")
        self.actionKillAllConfirmations = QtGui.QAction(parent=MainWindow)
        self.actionKillAllConfirmations.setObjectName("actionKillAllConfirmations")
        self.actionEnableIDTable = QtGui.QAction(parent=MainWindow)
        self.actionEnableIDTable.setCheckable(True)
        self.actionEnableIDTable.setObjectName("actionEnableIDTable")
        self.actionExport = QtGui.QAction(parent=MainWindow)
        self.actionExport.setObjectName("actionExport")
        self.actionCopySelectedElements = QtGui.QAction(parent=MainWindow)
        self.actionCopySelectedElements.setObjectName("actionCopySelectedElements")
        self.actionSetDefaultAPIPassword = QtGui.QAction(parent=MainWindow)
        self.actionSetDefaultAPIPassword.setObjectName("actionSetDefaultAPIPassword")
        self.actionAbout = QtGui.QAction(parent=MainWindow)
        self.actionAbout.setObjectName("actionAbout")
        self.actionReportIssue = QtGui.QAction(parent=MainWindow)
        self.actionReportIssue.setObjectName("actionReportIssue")
        self.actionSourceCode = QtGui.QAction(parent=MainWindow)
        self.actionSourceCode.setObjectName("actionSourceCode")
        self.menuHelp.addAction(self.actionAbout)
        self.menuHelp.addAction(self.actionReportIssue)
        self.menuHelp.addAction(self.actionSourceCode)
        self.menuHelp.addAction(self.actionVersion)
        self.menuOptions.addAction(self.actionAlwaysOpenIPInBrowser)
        self.menuOptions.addAction(self.actionDisableInactiveTimer)
        self.menuOptions.addAction(self.actionDisableWarningDialog)
        self.menuOptions.addAction(self.actionAutoStartOnLaunch)
        self.menuQuit.addAction(self.actionKillAllConfirmations)
        self.menuQuit.addAction(self.actionQuit)
        self.menuTableSettings.addAction(self.actionSetDefaultAPIPassword)
        self.menuTable.addAction(self.actionEnableIDTable)
        self.menuTable.addAction(self.menuTableSettings.menuAction())
        self.menuTable.addAction(self.actionCopySelectedElements)
        self.menuTable.addAction(self.actionExport)
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menubar.addAction(self.menuOptions.menuAction())
        self.menubar.addAction(self.menuTable.menuAction())
        self.menubar.addAction(self.menuQuit.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "BitCap IPReporter"))
        self.label.setText(_translate("MainWindow", "BitCap IPReporter"))
        self.label.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.label_3.setText(_translate("MainWindow", "Authentication Password:"))
        self.label_3.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.actionIPRSetPasswd.setToolTip(_translate("MainWindow", "Set default Bitmain authentication password"))
        self.actionIPRSetPasswd.setText(_translate("MainWindow", "Set Password"))
        self.actionIPRStart.setText(_translate("MainWindow", "Start"))
        self.actionIPRStop.setText(_translate("MainWindow", "Stop"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.menuOptions.setTitle(_translate("MainWindow", "Options"))
        self.menuQuit.setTitle(_translate("MainWindow", "Quit"))
        self.menuTable.setTitle(_translate("MainWindow", "Table"))
        self.menuTableSettings.setTitle(_translate("MainWindow", "Table Settings"))
        self.actionVersion.setText(_translate("MainWindow", "Version"))
        self.actionAlwaysOpenIPInBrowser.setText(_translate("MainWindow", "Always Open IP in Browser"))
        self.actionAlwaysOpenIPInBrowser.setToolTip(_translate("MainWindow", "Always opens IPs in browser (No IP confirmation)"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))
        self.actionQuit.setToolTip(_translate("MainWindow", "Quits app"))
        self.actionDisableInactiveTimer.setText(_translate("MainWindow", "Disable Inactive Timer"))
        self.actionDisableInactiveTimer.setToolTip(_translate("MainWindow", "Disables inactive timer of 15 minutes (Listens until stopped)"))
        self.actionDisableWarningDialog.setText(_translate("MainWindow", "Disable Warning Dialog"))
        self.actionDisableWarningDialog.setToolTip(_translate("MainWindow", "Disables warning dialog when starting listeners"))
        self.actionAutoStartOnLaunch.setText(_translate("MainWindow", "Auto Start on Launch"))
        self.actionAutoStartOnLaunch.setToolTip(_translate("MainWindow", "Automatically start listeners on launch"))
        self.actionKillAllConfirmations.setText(_translate("MainWindow", "Kill All Confirmations"))
        self.actionKillAllConfirmations.setToolTip(_translate("MainWindow", "Kills all IP confirmation windows"))
        self.actionEnableIDTable.setText(_translate("MainWindow", "Enable ID Table"))
        self.actionEnableIDTable.setToolTip(_translate("MainWindow", "Stores IP, MAC, TYPE in a table on confirmation"))
        self.actionExport.setText(_translate("MainWindow", "Export"))
        self.actionExport.setToolTip(_translate("MainWindow", "Export current table as .CSV file"))
        self.actionCopySelectedElements.setText(_translate("MainWindow", "Copy Selected Elements"))
        self.actionCopySelectedElements.setToolTip(_translate("MainWindow", "Copy selected elements to clipboard. Drag or Ctrl-click to select multiple cols/rows"))
        self.actionSetDefaultAPIPassword.setText(_translate("MainWindow", "Set Default API Password"))
        self.actionSetDefaultAPIPassword.setToolTip(_translate("MainWindow", "Set default API password to config. Used to get data from the miner"))
        self.actionAbout.setText(_translate("MainWindow", "About"))
        self.actionAbout.setToolTip(_translate("MainWindow", "Opens the about dialog"))
        self.actionReportIssue.setText(_translate("MainWindow", "Report Issue"))
        self.actionReportIssue.setToolTip(_translate("MainWindow", "Report a new issue on GitHub"))
        self.actionSourceCode.setText(_translate("MainWindow", "Source Code"))
        self.actionSourceCode.setToolTip(_translate("MainWindow", "Opens the GitHub repo in browser"))


class Ui_IPRConfirmation(object):
    def setupUi(self, IPRConfirmation):
        IPRConfirmation.setObjectName("IPRConfirmation")
        IPRConfirmation.resize(350, 260)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(IPRConfirmation.sizePolicy().hasHeightForWidth())
        IPRConfirmation.setSizePolicy(sizePolicy)
        IPRConfirmation.setStyleSheet("QWidget#IPRConfirmation {\n"
"    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0.5 rgba(6, 16, 31, 255), stop:1 rgba(0, 0, 0, 255));\n"
"}\n"
"QWidget[StyleClass=\"setText\"] {\n"
"    color: rgb(238, 238, 238);\n"
"}\n"
"QLineEdit {\n"
"    background-color: rgb(145, 149, 155);\n"
"    color: rgb(238, 238, 238);\n"
"}")
        self.gridLayout = QtWidgets.QGridLayout(IPRConfirmation)
        self.gridLayout.setContentsMargins(16, -1, 16, -1)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(parent=IPRConfirmation)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.lineMACField = QtWidgets.QLineEdit(parent=IPRConfirmation)
        self.lineMACField.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        self.lineMACField.setFont(font)
        self.lineMACField.setText("")
        self.lineMACField.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lineMACField.setReadOnly(True)
        self.lineMACField.setObjectName("lineMACField")
        self.gridLayout.addWidget(self.lineMACField, 4, 0, 1, 1)
        self.lineIPField = QtWidgets.QLineEdit(parent=IPRConfirmation)
        self.lineIPField.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lineIPField.setFont(font)
        self.lineIPField.setText("")
        self.lineIPField.setFrame(True)
        self.lineIPField.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lineIPField.setReadOnly(True)
        self.lineIPField.setObjectName("lineIPField")
        self.gridLayout.addWidget(self.lineIPField, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(parent=IPRConfirmation)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.accept = QtWidgets.QPushButton(parent=IPRConfirmation)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.accept.sizePolicy().hasHeightForWidth())
        self.accept.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.accept.setFont(font)
        self.accept.setDefault(True)
        self.accept.setObjectName("accept")
        self.gridLayout.addWidget(self.accept, 5, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.actionOpenBrowser = QtWidgets.QPushButton(parent=IPRConfirmation)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.actionOpenBrowser.sizePolicy().hasHeightForWidth())
        self.actionOpenBrowser.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.actionOpenBrowser.setFont(font)
        self.actionOpenBrowser.setObjectName("actionOpenBrowser")
        self.gridLayout.addWidget(self.actionOpenBrowser, 2, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.retranslateUi(IPRConfirmation)
        QtCore.QMetaObject.connectSlotsByName(IPRConfirmation)

    def retranslateUi(self, IPRConfirmation):
        _translate = QtCore.QCoreApplication.translate
        IPRConfirmation.setWindowTitle(_translate("IPRConfirmation", "IPR Confirmation"))
        self.label_2.setText(_translate("IPRConfirmation", "MAC Address"))
        self.label_2.setProperty("StyleClass", _translate("IPRConfirmation", "setText"))
        self.label.setText(_translate("IPRConfirmation", "IP Address"))
        self.label.setProperty("StyleClass", _translate("IPRConfirmation", "setText"))
        self.actionOpenBrowser.setText(_translate("IPRConfirmation", "Open Browser"))
        self.accept.setText(_translate("IPRConfirmation", "OK"))
