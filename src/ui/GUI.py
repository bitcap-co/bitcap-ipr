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
        MainWindow.resize(500, 500)
        MainWindow.setStyleSheet("QWidget[StyleClass=\"setText\"] {\n"
"    color: rgb(238, 238, 238);\n"
"}")
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setStyleSheet("QWidget#centralwidget {\n"
"    background-color:qlineargradient(spread:pad, x1:0.500, y1:0, x2:0.500, y2:1, stop:0.5 rgba(6, 16, 31, 255), stop:1 rgba(0, 0, 0, 255));\n"
"}")
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.actionIPRStop = QtWidgets.QPushButton(parent=self.centralwidget)
        self.actionIPRStop.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.actionIPRStop.setFont(font)
        self.actionIPRStop.setObjectName("actionIPRStop")
        self.gridLayout.addWidget(self.actionIPRStop, 3, 3, 1, 1)
        self.actionIPRStart = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.actionIPRStart.setFont(font)
        self.actionIPRStart.setDefault(True)
        self.actionIPRStart.setObjectName("actionIPRStart")
        self.gridLayout.addWidget(self.actionIPRStart, 3, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.gridLayout.addItem(spacerItem, 1, 2, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout.addItem(spacerItem1, 2, 4, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignTop)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.gridLayout.addItem(spacerItem2, 3, 2, 1, 1)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout.addItem(spacerItem3, 2, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setMinimumSize(QtCore.QSize(256, 256))
        self.label_2.setText("")
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 2, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 500, 22))
        self.menubar.setObjectName("menubar")
        self.menuAbout = QtWidgets.QMenu(parent=self.menubar)
        self.menuAbout.setObjectName("menuAbout")
        self.menuOptions = QtWidgets.QMenu(parent=self.menubar)
        self.menuOptions.setObjectName("menuOptions")
        self.menuQuit = QtWidgets.QMenu(parent=self.menubar)
        self.menuQuit.setObjectName("menuQuit")
        MainWindow.setMenuBar(self.menubar)
        self.actionHelp = QtGui.QAction(parent=MainWindow)
        self.actionHelp.setObjectName("actionHelp")
        self.actionVersion = QtGui.QAction(parent=MainWindow)
        self.actionVersion.setEnabled(False)
        self.actionVersion.setObjectName("actionVersion")
        self.actionAutoOpenIPInBrowser = QtGui.QAction(parent=MainWindow)
        self.actionAutoOpenIPInBrowser.setCheckable(True)
        self.actionAutoOpenIPInBrowser.setObjectName("actionAutoOpenIPInBrowser")
        self.actionQuit = QtGui.QAction(parent=MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.actionDisableInactiveTimer = QtGui.QAction(parent=MainWindow)
        self.actionDisableInactiveTimer.setCheckable(True)
        self.actionDisableInactiveTimer.setObjectName("actionDisableInactiveTimer")
        self.menuAbout.addAction(self.actionHelp)
        self.menuAbout.addAction(self.actionVersion)
        self.menuOptions.addAction(self.actionAutoOpenIPInBrowser)
        self.menuOptions.addAction(self.actionDisableInactiveTimer)
        self.menuQuit.addAction(self.actionQuit)
        self.menubar.addAction(self.menuAbout.menuAction())
        self.menubar.addAction(self.menuOptions.menuAction())
        self.menubar.addAction(self.menuQuit.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "BitCap IPReporter"))
        self.actionIPRStop.setText(_translate("MainWindow", "Stop"))
        self.actionIPRStart.setText(_translate("MainWindow", "Start"))
        self.label.setText(_translate("MainWindow", "BitCap IPReporter"))
        self.label.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.label_2.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.menuAbout.setTitle(_translate("MainWindow", "About"))
        self.menuOptions.setTitle(_translate("MainWindow", "Options"))
        self.menuQuit.setTitle(_translate("MainWindow", "Quit"))
        self.actionHelp.setText(_translate("MainWindow", "Help"))
        self.actionVersion.setText(_translate("MainWindow", "Version"))
        self.actionAutoOpenIPInBrowser.setText(_translate("MainWindow", "Auto Open IP in Browser"))
        self.actionQuit.setText(_translate("MainWindow", "Quit"))
        self.actionDisableInactiveTimer.setText(_translate("MainWindow", "Disable Inactive Timer"))


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
