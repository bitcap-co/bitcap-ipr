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
        self.iprCustomListener = QtWidgets.QWidget()
        self.iprCustomListener.setObjectName("iprCustomListener")
        self.machines = QtWidgets.QWidget(parent=self.iprCustomListener)
        self.machines.setGeometry(QtCore.QRect(10, 50, 450, 35))
        self.machines.setObjectName("machines")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.machines)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.checkBox_3 = QtWidgets.QCheckBox(parent=self.machines)
        self.checkBox_3.setObjectName("checkBox_3")
        self.horizontalLayout_6.addWidget(self.checkBox_3)
        self.checkBox_2 = QtWidgets.QCheckBox(parent=self.machines)
        self.checkBox_2.setObjectName("checkBox_2")
        self.horizontalLayout_6.addWidget(self.checkBox_2)
        self.checkBox = QtWidgets.QCheckBox(parent=self.machines)
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout_6.addWidget(self.checkBox)
        self.header1 = QtWidgets.QWidget(parent=self.iprCustomListener)
        self.header1.setGeometry(QtCore.QRect(10, 0, 450, 50))
        self.header1.setObjectName("header1")
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout(self.header1)
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label = QtWidgets.QLabel(parent=self.header1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QtCore.QSize(260, 30))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_7.addWidget(self.label)
        self.checkBox_4 = QtWidgets.QCheckBox(parent=self.header1)
        self.checkBox_4.setObjectName("checkBox_4")
        self.horizontalLayout_7.addWidget(self.checkBox_4)
        self.header2 = QtWidgets.QWidget(parent=self.iprCustomListener)
        self.header2.setGeometry(QtCore.QRect(10, 85, 450, 50))
        self.header2.setObjectName("header2")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout(self.header2)
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_4 = QtWidgets.QLabel(parent=self.header2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setMinimumSize(QtCore.QSize(260, 30))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_8.addWidget(self.label_4)
        self.pushButton = QtWidgets.QPushButton(parent=self.header2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_8.addWidget(self.pushButton)
        self.listWidget = QtWidgets.QListWidget(parent=self.iprCustomListener)
        self.listWidget.setGeometry(QtCore.QRect(10, 130, 450, 100))
        self.listWidget.setObjectName("listWidget")
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.iprCustomListener)
        self.pushButton_2.setGeometry(QtCore.QRect(140, 240, 181, 24))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.pushButton_2.setFont(font)
        self.pushButton_2.setObjectName("pushButton_2")
        self.stackedWidget.addWidget(self.iprCustomListener)
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
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "BitCap IPReporter"))
        self.label_3.setText(_translate("MainWindow", "Authentication Password:"))
        self.label_3.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.actionIPRSetPasswd.setToolTip(_translate("MainWindow", "Set default Bitmain authentication password"))
        self.actionIPRSetPasswd.setText(_translate("MainWindow", "Set Password"))
        self.checkBox_3.setText(_translate("MainWindow", "antminer"))
        self.checkBox_2.setText(_translate("MainWindow", "iceriver"))
        self.checkBox.setText(_translate("MainWindow", "whatsminer"))
        self.label.setText(_translate("MainWindow", "Listen For Machines:"))
        self.label.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.checkBox_4.setText(_translate("MainWindow", "Select All"))
        self.label_4.setText(_translate("MainWindow", "Saved Networks:"))
        self.label_4.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.pushButton.setText(_translate("MainWindow", "Create New Network"))
        self.pushButton_2.setText(_translate("MainWindow", "Start Custom Listener"))
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
