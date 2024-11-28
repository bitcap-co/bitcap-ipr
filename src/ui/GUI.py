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
        self.machines.setGeometry(QtCore.QRect(20, 50, 450, 35))
        self.machines.setObjectName("machines")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.machines)
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.checkAntminer = QtWidgets.QCheckBox(parent=self.machines)
        self.checkAntminer.setObjectName("checkAntminer")
        self.horizontalLayout_6.addWidget(self.checkAntminer)
        self.checkIceRiver = QtWidgets.QCheckBox(parent=self.machines)
        self.checkIceRiver.setObjectName("checkIceRiver")
        self.horizontalLayout_6.addWidget(self.checkIceRiver)
        self.checkWhatsminer = QtWidgets.QCheckBox(parent=self.machines)
        self.checkWhatsminer.setObjectName("checkWhatsminer")
        self.horizontalLayout_6.addWidget(self.checkWhatsminer)
        self.header1 = QtWidgets.QWidget(parent=self.iprCustomListener)
        self.header1.setGeometry(QtCore.QRect(20, 0, 450, 50))
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
        self.checkSelectAll = QtWidgets.QCheckBox(parent=self.header1)
        self.checkSelectAll.setObjectName("checkSelectAll")
        self.horizontalLayout_7.addWidget(self.checkSelectAll)
        self.header2 = QtWidgets.QWidget(parent=self.iprCustomListener)
        self.header2.setGeometry(QtCore.QRect(20, 90, 450, 50))
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
        self.actionShowCreateNetwork = QtWidgets.QPushButton(parent=self.header2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.actionShowCreateNetwork.sizePolicy().hasHeightForWidth())
        self.actionShowCreateNetwork.setSizePolicy(sizePolicy)
        self.actionShowCreateNetwork.setObjectName("actionShowCreateNetwork")
        self.horizontalLayout_8.addWidget(self.actionShowCreateNetwork)
        self.actionCreateListener = QtWidgets.QPushButton(parent=self.iprCustomListener)
        self.actionCreateListener.setGeometry(QtCore.QRect(150, 250, 181, 24))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.actionCreateListener.setFont(font)
        self.actionCreateListener.setObjectName("actionCreateListener")
        self.tableNetworks = QtWidgets.QTableWidget(parent=self.iprCustomListener)
        self.tableNetworks.setGeometry(QtCore.QRect(20, 140, 451, 101))
        self.tableNetworks.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.tableNetworks.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableNetworks.setColumnCount(3)
        self.tableNetworks.setObjectName("tableNetworks")
        self.tableNetworks.setRowCount(0)
        self.tableNetworks.horizontalHeader().setVisible(False)
        self.tableNetworks.horizontalHeader().setDefaultSectionSize(145)
        self.tableNetworks.verticalHeader().setVisible(False)
        self.stackedWidget.addWidget(self.iprCustomListener)
        self.iprCreateNetwork = QtWidgets.QWidget()
        self.iprCreateNetwork.setObjectName("iprCreateNetwork")
        self.label_5 = QtWidgets.QLabel(parent=self.iprCreateNetwork)
        self.label_5.setGeometry(QtCore.QRect(9, 9, 451, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setMinimumSize(QtCore.QSize(260, 30))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label_5.setFont(font)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.widget_5 = QtWidgets.QWidget(parent=self.iprCreateNetwork)
        self.widget_5.setGeometry(QtCore.QRect(10, 60, 451, 22))
        self.widget_5.setObjectName("widget_5")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.widget_5)
        self.horizontalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem3)
        self.label_6 = QtWidgets.QLabel(parent=self.widget_5)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_12.addWidget(self.label_6)
        self.lineNetworkName = QtWidgets.QLineEdit(parent=self.widget_5)
        self.lineNetworkName.setObjectName("lineNetworkName")
        self.horizontalLayout_12.addWidget(self.lineNetworkName)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem4)
        self.actionCreateNetwork = QtWidgets.QPushButton(parent=self.iprCreateNetwork)
        self.actionCreateNetwork.setGeometry(QtCore.QRect(170, 250, 141, 24))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.actionCreateNetwork.setFont(font)
        self.actionCreateNetwork.setObjectName("actionCreateNetwork")
        self.widget_6 = QtWidgets.QWidget(parent=self.iprCreateNetwork)
        self.widget_6.setGeometry(QtCore.QRect(10, 190, 451, 22))
        self.widget_6.setObjectName("widget_6")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.widget_6)
        self.horizontalLayout_13.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem5)
        self.label_8 = QtWidgets.QLabel(parent=self.widget_6)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_13.addWidget(self.label_8)
        self.lineNetworkLoc = QtWidgets.QLineEdit(parent=self.widget_6)
        self.lineNetworkLoc.setObjectName("lineNetworkLoc")
        self.horizontalLayout_13.addWidget(self.lineNetworkLoc)
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem6)
        self.widget_2 = QtWidgets.QWidget(parent=self.iprCreateNetwork)
        self.widget_2.setGeometry(QtCore.QRect(100, 80, 311, 101))
        self.widget_2.setObjectName("widget_2")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.widget_2)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_7 = QtWidgets.QLabel(parent=self.widget_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_5.addWidget(self.label_7)
        self.rangeStart = QtWidgets.QWidget(parent=self.widget_2)
        self.rangeStart.setObjectName("rangeStart")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.rangeStart)
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.octlet1_start = QtWidgets.QSpinBox(parent=self.rangeStart)
        self.octlet1_start.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.octlet1_start.setAccelerated(True)
        self.octlet1_start.setMinimum(1)
        self.octlet1_start.setMaximum(255)
        self.octlet1_start.setProperty("value", 1)
        self.octlet1_start.setObjectName("octlet1_start")
        self.horizontalLayout_10.addWidget(self.octlet1_start)
        self.octlet2_start = QtWidgets.QSpinBox(parent=self.rangeStart)
        self.octlet2_start.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.octlet2_start.setAccelerated(True)
        self.octlet2_start.setMinimum(1)
        self.octlet2_start.setMaximum(255)
        self.octlet2_start.setProperty("value", 1)
        self.octlet2_start.setObjectName("octlet2_start")
        self.horizontalLayout_10.addWidget(self.octlet2_start)
        self.octlet3_start = QtWidgets.QSpinBox(parent=self.rangeStart)
        self.octlet3_start.setAccelerated(True)
        self.octlet3_start.setMinimum(1)
        self.octlet3_start.setMaximum(255)
        self.octlet3_start.setProperty("value", 1)
        self.octlet3_start.setObjectName("octlet3_start")
        self.horizontalLayout_10.addWidget(self.octlet3_start)
        self.label_9 = QtWidgets.QLabel(parent=self.rangeStart)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy)
        self.label_9.setMinimumSize(QtCore.QSize(25, 0))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_10.addWidget(self.label_9)
        self.verticalLayout_5.addWidget(self.rangeStart)
        self.rangeEnd = QtWidgets.QWidget(parent=self.widget_2)
        self.rangeEnd.setObjectName("rangeEnd")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.rangeEnd)
        self.horizontalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.octlet1_end = QtWidgets.QSpinBox(parent=self.rangeEnd)
        self.octlet1_end.setEnabled(False)
        self.octlet1_end.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.octlet1_end.setAccelerated(True)
        self.octlet1_end.setMinimum(1)
        self.octlet1_end.setMaximum(255)
        self.octlet1_end.setObjectName("octlet1_end")
        self.horizontalLayout_11.addWidget(self.octlet1_end)
        self.octlet2_end = QtWidgets.QSpinBox(parent=self.rangeEnd)
        self.octlet2_end.setEnabled(False)
        self.octlet2_end.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.octlet2_end.setAccelerated(True)
        self.octlet2_end.setMaximum(255)
        self.octlet2_end.setProperty("value", 1)
        self.octlet2_end.setObjectName("octlet2_end")
        self.horizontalLayout_11.addWidget(self.octlet2_end)
        self.octlet3_end = QtWidgets.QSpinBox(parent=self.rangeEnd)
        self.octlet3_end.setAccelerated(True)
        self.octlet3_end.setMinimum(1)
        self.octlet3_end.setMaximum(255)
        self.octlet3_end.setProperty("value", 1)
        self.octlet3_end.setObjectName("octlet3_end")
        self.horizontalLayout_11.addWidget(self.octlet3_end)
        self.label_10 = QtWidgets.QLabel(parent=self.rangeEnd)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy)
        self.label_10.setMinimumSize(QtCore.QSize(25, 0))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_11.addWidget(self.label_10)
        self.verticalLayout_5.addWidget(self.rangeEnd)
        self.stackedWidget.addWidget(self.iprCreateNetwork)
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
        self.checkAntminer.setText(_translate("MainWindow", "antminer"))
        self.checkIceRiver.setText(_translate("MainWindow", "iceriver"))
        self.checkWhatsminer.setText(_translate("MainWindow", "whatsminer"))
        self.label.setText(_translate("MainWindow", "Listen For Machines:"))
        self.label.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.checkSelectAll.setText(_translate("MainWindow", "Select All"))
        self.label_4.setText(_translate("MainWindow", "Saved Networks:"))
        self.label_4.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.actionShowCreateNetwork.setText(_translate("MainWindow", "Create New Network"))
        self.actionCreateListener.setText(_translate("MainWindow", "Start Custom Listener"))
        self.label_5.setText(_translate("MainWindow", "Create New Network"))
        self.label_5.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.label_6.setText(_translate("MainWindow", "Name:"))
        self.label_6.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.actionCreateNetwork.setText(_translate("MainWindow", "Create Network"))
        self.label_8.setText(_translate("MainWindow", "Location:"))
        self.label_8.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.label_7.setText(_translate("MainWindow", "IP Range:"))
        self.label_7.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.label_9.setText(_translate("MainWindow", ".255"))
        self.label_9.setProperty("StyleClass", _translate("MainWindow", "setText"))
        self.label_10.setText(_translate("MainWindow", ".255"))
        self.label_10.setProperty("StyleClass", _translate("MainWindow", "setText"))
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
