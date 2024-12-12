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
        MainWindow.setFixedSize(QtCore.QSize(500, 500))
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setStyleSheet("QWidget#centralwidget {\n"
"    background-color:qlineargradient(spread:pad, x1:0.500, y1:0, x2:0.500, y2:1, stop:0.5 rgba(6, 16, 31, 255), stop:1 rgba(0, 0, 0, 255));\n"
"}")
        self.centralwidget.setObjectName("centralwidget")
        self.titlebarwidget = QtWidgets.QWidget(parent=self.centralwidget)
        self.titlebarwidget.setGeometry(QtCore.QRect(0, 0, 500, 30))
        self.titlebarwidget.setObjectName("titlebarwidget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.titlebarwidget)
        self.horizontalLayout_4.setContentsMargins(5, 0, 0, 0)
        self.horizontalLayout_4.setSpacing(10)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.menubarwidget = QtWidgets.QWidget(parent=self.centralwidget)
        self.menubarwidget.setGeometry(QtCore.QRect(0, 30, 500, 26))
        self.menubarwidget.setMinimumSize(QtCore.QSize(0, 0))
        self.menubarwidget.setObjectName("menubarwidget")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.menubarwidget)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.vwrapper = QtWidgets.QWidget(parent=self.centralwidget)
        self.vwrapper.setGeometry(QtCore.QRect(9, 60, 483, 431))
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
        self.tableWidget.setGeometry(QtCore.QRect(0, 0, 483, 280))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.tableWidget.setAlternatingRowColors(False)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setCornerButtonEnabled(True)
        self.tableWidget.setColumnCount(5)
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
        self.groupBox = QtWidgets.QGroupBox(parent=self.iprConfig)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.checkEnableSysTray = QtWidgets.QCheckBox(parent=self.groupBox)
        self.checkEnableSysTray.setObjectName("checkEnableSysTray")
        self.verticalLayout_5.addWidget(self.checkEnableSysTray)
        self.hwrapper_2 = QtWidgets.QWidget(parent=self.groupBox)
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
        self.verticalLayout_2.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(parent=self.iprConfig)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_3 = QtWidgets.QLabel(parent=self.groupBox_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.linePasswdField = QtWidgets.QLineEdit(parent=self.groupBox_2)
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
        self.horizontalLayout.addWidget(self.linePasswdField)
        self.verticalLayout_2.addWidget(self.groupBox_2)
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
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
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
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
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

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(1)
        self.comboOnWindowClose.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "BitCap IPReporter"))
        self.label.setText(_translate("MainWindow", "Configuration"))
        self.label.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.groupBox.setTitle(_translate("MainWindow", "General"))
        self.checkEnableSysTray.setText(_translate("MainWindow", "Enable System Tray"))
        self.label_4.setText(_translate("MainWindow", "On Window Close:"))
        self.label_4.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.comboOnWindowClose.setItemText(0, _translate("MainWindow", "Close"))
        self.comboOnWindowClose.setItemText(1, _translate("MainWindow", "Minimize To Tray"))
        self.groupBox_2.setTitle(_translate("MainWindow", "API Settings"))
        self.label_3.setText(_translate("MainWindow", "Set API Password:"))
        self.label_3.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.actionIPRCancelConfig.setText(_translate("MainWindow", "Cancel"))
        self.actionIPRSaveConfig.setText(_translate("MainWindow", "Save"))
        self.actionIPRStart.setText(_translate("MainWindow", "Start"))
        self.actionIPRStop.setText(_translate("MainWindow", "Stop"))


class Ui_IPRConfirmation(object):
    def setupUi(self, IPRConfirmation):
        IPRConfirmation.setObjectName("IPRConfirmation")
        IPRConfirmation.resize(350, 260)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(IPRConfirmation.sizePolicy().hasHeightForWidth())
        IPRConfirmation.setSizePolicy(sizePolicy)
        self.titlebarwidget = QtWidgets.QWidget(parent=IPRConfirmation)
        self.titlebarwidget.setGeometry(QtCore.QRect(0, 0, 350, 30))
        self.titlebarwidget.setObjectName("titlebarwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.titlebarwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_2 = QtWidgets.QWidget(parent=IPRConfirmation)
        self.widget_2.setGeometry(QtCore.QRect(0, 30, 350, 230))
        self.widget_2.setObjectName("widget_2")
        self.gridLayout = QtWidgets.QGridLayout(self.widget_2)
        self.gridLayout.setContentsMargins(9, 0, 9, 9)
        self.gridLayout.setObjectName("gridLayout")
        self.lineIPField = QtWidgets.QLineEdit(parent=self.widget_2)
        self.lineIPField.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lineIPField.setFont(font)
        self.lineIPField.setText("")
        self.lineIPField.setFrame(True)
        self.lineIPField.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lineIPField.setReadOnly(True)
        self.lineIPField.setObjectName("lineIPField")
        self.gridLayout.addWidget(self.lineIPField, 2, 0, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.widget_2)
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
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.accept = QtWidgets.QPushButton(parent=self.widget_2)
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
        self.gridLayout.addWidget(self.accept, 7, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.actionOpenBrowser = QtWidgets.QPushButton(parent=self.widget_2)
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
        self.gridLayout.addWidget(self.actionOpenBrowser, 4, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.label_2 = QtWidgets.QLabel(parent=self.widget_2)
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
        self.gridLayout.addWidget(self.label_2, 5, 0, 1, 1)
        self.lineMACField = QtWidgets.QLineEdit(parent=self.widget_2)
        self.lineMACField.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        self.lineMACField.setFont(font)
        self.lineMACField.setText("")
        self.lineMACField.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lineMACField.setReadOnly(True)
        self.lineMACField.setObjectName("lineMACField")
        self.gridLayout.addWidget(self.lineMACField, 6, 0, 1, 1)
        self.line = QtWidgets.QFrame(parent=self.widget_2)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 0, 0, 1, 1)

        self.retranslateUi(IPRConfirmation)
        QtCore.QMetaObject.connectSlotsByName(IPRConfirmation)

    def retranslateUi(self, IPRConfirmation):
        _translate = QtCore.QCoreApplication.translate
        IPRConfirmation.setWindowTitle(_translate("IPRConfirmation", "IPR Confirmation"))
        self.label.setText(_translate("IPRConfirmation", "IP Address"))
        self.label.setProperty("StyleClass", _translate("IPRConfirmation", "setText"))
        self.accept.setText(_translate("IPRConfirmation", "OK"))
        self.actionOpenBrowser.setText(_translate("IPRConfirmation", "Open Browser"))
        self.label_2.setText(_translate("IPRConfirmation", "MAC Address"))
        self.label_2.setProperty("StyleClass", _translate("IPRConfirmation", "setText"))


class Ui_IPRAbout(object):
    def setupUi(self, IPRAbout):
        IPRAbout.setObjectName("IPRAbout")
        IPRAbout.resize(400, 250)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(IPRAbout.sizePolicy().hasHeightForWidth())
        IPRAbout.setSizePolicy(sizePolicy)
        self.titlebarwidget = QtWidgets.QWidget(parent=IPRAbout)
        self.titlebarwidget.setGeometry(QtCore.QRect(0, 0, 400, 30))
        self.titlebarwidget.setObjectName("titlebarwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.titlebarwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.centralwidget = QtWidgets.QWidget(parent=IPRAbout)
        self.centralwidget.setGeometry(QtCore.QRect(0, 35, 400, 180))
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.buttons = QtWidgets.QWidget(parent=IPRAbout)
        self.buttons.setGeometry(QtCore.QRect(0, 200, 400, 50))
        self.buttons.setObjectName("buttons")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.buttons)
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.line = QtWidgets.QFrame(parent=IPRAbout)
        self.line.setGeometry(QtCore.QRect(9, 30, 380, 4))
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setObjectName("line")

        self.retranslateUi(IPRAbout)
        QtCore.QMetaObject.connectSlotsByName(IPRAbout)

    def retranslateUi(self, IPRAbout):
        _translate = QtCore.QCoreApplication.translate
        IPRAbout.setWindowTitle(_translate("IPRAbout", "Dialog"))
