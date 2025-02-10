# Form implementation generated from reading ui file '.\MainWindow.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 600)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setStyleSheet("QWidget#centralwidget {\n"
"    background-color:qlineargradient(spread:pad, x1:0.500, y1:0, x2:0.500, y2:1, stop:0.5 rgba(6, 16, 31, 255), stop:1 rgba(0, 0, 0, 255));\n"
"}")
        self.centralwidget.setObjectName("centralwidget")
        self.titlebarwidget = QtWidgets.QWidget(parent=self.centralwidget)
        self.titlebarwidget.setGeometry(QtCore.QRect(0, 0, 600, 30))
        self.titlebarwidget.setObjectName("titlebarwidget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.titlebarwidget)
        self.horizontalLayout_4.setContentsMargins(5, 0, 0, 0)
        self.horizontalLayout_4.setSpacing(10)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.menubarwidget = QtWidgets.QWidget(parent=self.centralwidget)
        self.menubarwidget.setGeometry(QtCore.QRect(0, 30, 600, 26))
        self.menubarwidget.setMinimumSize(QtCore.QSize(0, 0))
        self.menubarwidget.setObjectName("menubarwidget")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.menubarwidget)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.vwrapper = QtWidgets.QWidget(parent=self.centralwidget)
        self.vwrapper.setGeometry(QtCore.QRect(9, 60, 581, 511))
        self.vwrapper.setObjectName("vwrapper")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.vwrapper)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.stackedWidget = QtWidgets.QStackedWidget(parent=self.vwrapper)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
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
        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 581, 349))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.setProperty("showDropIndicator", False)
        self.tableWidget.setAlternatingRowColors(False)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setCornerButtonEnabled(True)
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(105)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(15)
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
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.iprConfig)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(parent=self.iprConfig)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QtCore.QSize(0, 30))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.tabWidget = QtWidgets.QTabWidget(parent=self.iprConfig)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setMinimumSize(QtCore.QSize(0, 0))
        self.tabWidget.setObjectName("tabWidget")
        self.general = QtWidgets.QWidget()
        self.general.setObjectName("general")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.general)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.iprSystemTray = QtWidgets.QGroupBox(parent=self.general)
        self.iprSystemTray.setObjectName("iprSystemTray")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.iprSystemTray)
        self.verticalLayout_5.setContentsMargins(9, 6, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.checkEnableSysTray = QtWidgets.QCheckBox(parent=self.iprSystemTray)
        self.checkEnableSysTray.setObjectName("checkEnableSysTray")
        self.verticalLayout_5.addWidget(self.checkEnableSysTray)
        self.hwrapper_2 = QtWidgets.QWidget(parent=self.iprSystemTray)
        self.hwrapper_2.setObjectName("hwrapper_2")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.hwrapper_2)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_4 = QtWidgets.QLabel(parent=self.hwrapper_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_6.addWidget(self.label_4)
        self.comboOnWindowClose = QtWidgets.QComboBox(parent=self.hwrapper_2)
        self.comboOnWindowClose.setEnabled(False)
        self.comboOnWindowClose.setObjectName("comboOnWindowClose")
        self.comboOnWindowClose.addItem("")
        self.comboOnWindowClose.addItem("")
        self.horizontalLayout_6.addWidget(self.comboOnWindowClose)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem1)
        self.verticalLayout_5.addWidget(self.hwrapper_2)
        self.verticalLayout_3.addWidget(self.iprSystemTray)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_3.addItem(spacerItem2)
        self.tabWidget.addTab(self.general, "")
        self.api = QtWidgets.QWidget()
        self.api.setObjectName("api")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.api)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.iprBitmain = QtWidgets.QGroupBox(parent=self.api)
        self.iprBitmain.setObjectName("iprBitmain")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.iprBitmain)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.label_10 = QtWidgets.QLabel(parent=self.iprBitmain)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_12.addWidget(self.label_10)
        self.lineBitmainPasswd = QtWidgets.QLineEdit(parent=self.iprBitmain)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineBitmainPasswd.sizePolicy().hasHeightForWidth())
        self.lineBitmainPasswd.setSizePolicy(sizePolicy)
        self.lineBitmainPasswd.setMinimumSize(QtCore.QSize(180, 25))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lineBitmainPasswd.setFont(font)
        self.lineBitmainPasswd.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineBitmainPasswd.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lineBitmainPasswd.setObjectName("lineBitmainPasswd")
        self.horizontalLayout_12.addWidget(self.lineBitmainPasswd)
        self.verticalLayout_6.addWidget(self.iprBitmain)
        self.iprWhatsminer = QtWidgets.QGroupBox(parent=self.api)
        self.iprWhatsminer.setObjectName("iprWhatsminer")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.iprWhatsminer)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_11 = QtWidgets.QLabel(parent=self.iprWhatsminer)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_11.setFont(font)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout.addWidget(self.label_11)
        self.lineWhatsminerPasswd = QtWidgets.QLineEdit(parent=self.iprWhatsminer)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineWhatsminerPasswd.sizePolicy().hasHeightForWidth())
        self.lineWhatsminerPasswd.setSizePolicy(sizePolicy)
        self.lineWhatsminerPasswd.setMinimumSize(QtCore.QSize(180, 25))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lineWhatsminerPasswd.setFont(font)
        self.lineWhatsminerPasswd.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineWhatsminerPasswd.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lineWhatsminerPasswd.setObjectName("lineWhatsminerPasswd")
        self.horizontalLayout.addWidget(self.lineWhatsminerPasswd)
        self.verticalLayout_6.addWidget(self.iprWhatsminer)
        self.iprPbfarmer = QtWidgets.QGroupBox(parent=self.api)
        self.iprPbfarmer.setObjectName("iprPbfarmer")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.iprPbfarmer)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_12 = QtWidgets.QLabel(parent=self.iprPbfarmer)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_13.addWidget(self.label_12)
        self.linePbfarmerKey = QtWidgets.QLineEdit(parent=self.iprPbfarmer)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.linePbfarmerKey.sizePolicy().hasHeightForWidth())
        self.linePbfarmerKey.setSizePolicy(sizePolicy)
        self.linePbfarmerKey.setMinimumSize(QtCore.QSize(180, 25))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.linePbfarmerKey.setFont(font)
        self.linePbfarmerKey.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.linePbfarmerKey.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.linePbfarmerKey.setObjectName("linePbfarmerKey")
        self.horizontalLayout_13.addWidget(self.linePbfarmerKey)
        self.verticalLayout_6.addWidget(self.iprPbfarmer)
        self.tabWidget.addTab(self.api, "")
        self.logs = QtWidgets.QWidget()
        self.logs.setObjectName("logs")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.logs)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.iprLog = QtWidgets.QGroupBox(parent=self.logs)
        self.iprLog.setObjectName("iprLog")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.iprLog)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.hwrapper = QtWidgets.QWidget(parent=self.iprLog)
        self.hwrapper.setObjectName("hwrapper")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.hwrapper)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_5 = QtWidgets.QLabel(parent=self.hwrapper)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_7.addWidget(self.label_5)
        self.comboLogLevel = QtWidgets.QComboBox(parent=self.hwrapper)
        self.comboLogLevel.setObjectName("comboLogLevel")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.horizontalLayout_7.addWidget(self.comboLogLevel)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem3)
        self.verticalLayout_7.addWidget(self.hwrapper)
        self.hwrapper_5 = QtWidgets.QWidget(parent=self.iprLog)
        self.hwrapper_5.setObjectName("hwrapper_5")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.hwrapper_5)
        self.horizontalLayout_10.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_7 = QtWidgets.QLabel(parent=self.hwrapper_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_10.addWidget(self.label_7)
        self.lineMaxLogSize = QtWidgets.QLineEdit(parent=self.hwrapper_5)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineMaxLogSize.sizePolicy().hasHeightForWidth())
        self.lineMaxLogSize.setSizePolicy(sizePolicy)
        self.lineMaxLogSize.setMinimumSize(QtCore.QSize(70, 0))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.lineMaxLogSize.setFont(font)
        self.lineMaxLogSize.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        self.lineMaxLogSize.setCursorPosition(0)
        self.lineMaxLogSize.setObjectName("lineMaxLogSize")
        self.horizontalLayout_10.addWidget(self.lineMaxLogSize)
        self.label_9 = QtWidgets.QLabel(parent=self.hwrapper_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_10.addWidget(self.label_9)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_10.addItem(spacerItem4)
        self.verticalLayout_7.addWidget(self.hwrapper_5)
        self.hwrapper_6 = QtWidgets.QWidget(parent=self.iprLog)
        self.hwrapper_6.setObjectName("hwrapper_6")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.hwrapper_6)
        self.horizontalLayout_11.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_8 = QtWidgets.QLabel(parent=self.hwrapper_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_11.addWidget(self.label_8)
        self.comboOnMaxLogSize = QtWidgets.QComboBox(parent=self.hwrapper_6)
        self.comboOnMaxLogSize.setObjectName("comboOnMaxLogSize")
        self.comboOnMaxLogSize.addItem("")
        self.comboOnMaxLogSize.addItem("")
        self.horizontalLayout_11.addWidget(self.comboOnMaxLogSize)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_11.addItem(spacerItem5)
        self.verticalLayout_7.addWidget(self.hwrapper_6)
        self.hwrapper_4 = QtWidgets.QWidget(parent=self.iprLog)
        self.hwrapper_4.setObjectName("hwrapper_4")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout(self.hwrapper_4)
        self.horizontalLayout_9.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_6 = QtWidgets.QLabel(parent=self.hwrapper_4)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_9.addWidget(self.label_6)
        self.comboFlushInterval = QtWidgets.QComboBox(parent=self.hwrapper_4)
        self.comboFlushInterval.setEnabled(True)
        self.comboFlushInterval.setObjectName("comboFlushInterval")
        self.comboFlushInterval.addItem("")
        self.comboFlushInterval.addItem("")
        self.horizontalLayout_9.addWidget(self.comboFlushInterval)
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem6)
        self.verticalLayout_7.addWidget(self.hwrapper_4)
        self.verticalLayout_4.addWidget(self.iprLog)
        self.tabWidget.addTab(self.logs, "")
        self.verticalLayout_2.addWidget(self.tabWidget)
        self.hwrapper_3 = QtWidgets.QWidget(parent=self.iprConfig)
        self.hwrapper_3.setObjectName("hwrapper_3")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.hwrapper_3)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.actionIPRCancelConfig = QtWidgets.QPushButton(parent=self.hwrapper_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.actionIPRCancelConfig.setFont(font)
        self.actionIPRCancelConfig.setObjectName("actionIPRCancelConfig")
        self.horizontalLayout_8.addWidget(self.actionIPRCancelConfig)
        self.actionIPRSaveConfig = QtWidgets.QPushButton(parent=self.hwrapper_3)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.actionIPRSaveConfig.setFont(font)
        self.actionIPRSaveConfig.setObjectName("actionIPRSaveConfig")
        self.horizontalLayout_8.addWidget(self.actionIPRSaveConfig)
        self.verticalLayout_2.addWidget(self.hwrapper_3)
        self.stackedWidget.addWidget(self.iprConfig)
        self.verticalLayout.addWidget(self.stackedWidget)
        spacerItem7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem7)
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
        spacerItem8 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem8)
        self.actionIPRStop = QtWidgets.QPushButton(parent=self.inputIPRButtons)
        self.actionIPRStop.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.actionIPRStop.setFont(font)
        self.actionIPRStop.setObjectName("actionIPRStop")
        self.horizontalLayout_2.addWidget(self.actionIPRStop)
        self.verticalLayout.addWidget(self.inputIPRButtons)
        MainWindow.setCentralWidget(self.centralwidget)
        self.iprStatus = QtWidgets.QStatusBar(parent=MainWindow)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.iprStatus.setFont(font)
        self.iprStatus.setSizeGripEnabled(False)
        self.iprStatus.setObjectName("iprStatus")
        MainWindow.setStatusBar(self.iprStatus)

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(2)
        self.tabWidget.setCurrentIndex(1)
        self.comboOnWindowClose.setCurrentIndex(0)
        self.comboLogLevel.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "BitCap IPReporter"))
        self.label.setText(_translate("MainWindow", "Configuration"))
        self.label.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.iprSystemTray.setTitle(_translate("MainWindow", "System Tray"))
        self.checkEnableSysTray.setText(_translate("MainWindow", "Enable System Tray"))
        self.label_4.setText(_translate("MainWindow", "On Window Close:"))
        self.label_4.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.comboOnWindowClose.setItemText(0, _translate("MainWindow", "Close"))
        self.comboOnWindowClose.setItemText(1, _translate("MainWindow", "Minimize To Tray"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.general), _translate("MainWindow", "General"))
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.general), _translate("MainWindow", "General Settings"))
        self.iprBitmain.setTitle(_translate("MainWindow", "Bitmain/Antminer"))
        self.label_10.setText(_translate("MainWindow", "Set Login Password:"))
        self.label_10.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.lineBitmainPasswd.setToolTip(_translate("MainWindow", "Set alternative login password for Antminers. Default: \"root\""))
        self.iprWhatsminer.setTitle(_translate("MainWindow", "Whatsminer"))
        self.label_11.setText(_translate("MainWindow", "Set Login Password:"))
        self.label_11.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.lineWhatsminerPasswd.setToolTip(_translate("MainWindow", "Set alternative login password for Whatsminer. Default: \"admin\""))
        self.iprPbfarmer.setTitle(_translate("MainWindow", "pbfarmer"))
        self.label_12.setText(_translate("MainWindow", "Set API Key:"))
        self.label_12.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.linePbfarmerKey.setToolTip(_translate("MainWindow", "Set alternative API Key for pbfarmer. Default API key is supplied if blank"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.api), _translate("MainWindow", "API"))
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.api), _translate("MainWindow", "API Settings"))
        self.iprLog.setTitle(_translate("MainWindow", "Log Settings"))
        self.label_5.setText(_translate("MainWindow", "Log Level: "))
        self.label_5.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.comboLogLevel.setToolTip(_translate("MainWindow", "Change minimum output level"))
        self.comboLogLevel.setItemText(0, _translate("MainWindow", "DEBUG"))
        self.comboLogLevel.setItemText(1, _translate("MainWindow", "INFO"))
        self.comboLogLevel.setItemText(2, _translate("MainWindow", "WARNING"))
        self.comboLogLevel.setItemText(3, _translate("MainWindow", "ERROR"))
        self.comboLogLevel.setItemText(4, _translate("MainWindow", "CRITICAL"))
        self.label_7.setText(_translate("MainWindow", "Max Log Size:"))
        self.lineMaxLogSize.setToolTip(_translate("MainWindow", "Set maximum log file size (Max limit 4096kb)"))
        self.lineMaxLogSize.setInputMask(_translate("MainWindow", "9999"))
        self.lineMaxLogSize.setText(_translate("MainWindow", "1024"))
        self.label_9.setText(_translate("MainWindow", "KB"))
        self.label_8.setText(_translate("MainWindow", "On Max Log Size:"))
        self.comboOnMaxLogSize.setToolTip(_translate("MainWindow", "Choose behavior for when log file reaches set max size"))
        self.comboOnMaxLogSize.setItemText(0, _translate("MainWindow", "Flush"))
        self.comboOnMaxLogSize.setItemText(1, _translate("MainWindow", "Rotate"))
        self.label_6.setText(_translate("MainWindow", "Flush Interval: "))
        self.label_6.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.comboFlushInterval.setToolTip(_translate("MainWindow", "Choose when to flush log file"))
        self.comboFlushInterval.setItemText(0, _translate("MainWindow", "On Log Size"))
        self.comboFlushInterval.setItemText(1, _translate("MainWindow", "Close"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.logs), _translate("MainWindow", "Logs"))
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.logs), _translate("MainWindow", "Log Settings"))
        self.actionIPRCancelConfig.setText(_translate("MainWindow", "Cancel"))
        self.actionIPRSaveConfig.setText(_translate("MainWindow", "Save"))
        self.actionIPRStart.setText(_translate("MainWindow", "Start"))
        self.actionIPRStop.setText(_translate("MainWindow", "Stop"))
        self.iprStatus.setToolTip(_translate("MainWindow", "Current IPR Status"))
