# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox,
    QComboBox, QFrame, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QSpinBox, QStackedWidget, QStatusBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(550, 550)
        MainWindow.setMinimumSize(QSize(550, 550))
        MainWindow.setMaximumSize(QSize(1200, 800))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"QWidget#centralwidget {\n"
"	background-color:qlineargradient(spread:pad, x1:0.500, y1:0, x2:0.500, y2:1, stop:0.5 rgba(6, 16, 31, 255), stop:1 rgba(0, 0, 0, 255));\n"
"}")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.topbar = QWidget(self.centralwidget)
        self.topbar.setObjectName(u"topbar")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.topbar.sizePolicy().hasHeightForWidth())
        self.topbar.setSizePolicy(sizePolicy)
        self.topbar.setMinimumSize(QSize(550, 58))
        self.verticalLayout_2 = QVBoxLayout(self.topbar)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.titlebar = QWidget(self.topbar)
        self.titlebar.setObjectName(u"titlebar")
        sizePolicy.setHeightForWidth(self.titlebar.sizePolicy().hasHeightForWidth())
        self.titlebar.setSizePolicy(sizePolicy)
        self.titlebar.setMinimumSize(QSize(550, 30))
        self.horizontalLayout = QHBoxLayout(self.titlebar)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_2.addWidget(self.titlebar)

        self.menubar = QWidget(self.topbar)
        self.menubar.setObjectName(u"menubar")
        sizePolicy.setHeightForWidth(self.menubar.sizePolicy().hasHeightForWidth())
        self.menubar.setSizePolicy(sizePolicy)
        self.menubar.setMinimumSize(QSize(550, 26))
        self.horizontalLayout_2 = QHBoxLayout(self.menubar)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_2.addWidget(self.menubar)


        self.verticalLayout.addWidget(self.topbar)

        self.hwrapper = QWidget(self.centralwidget)
        self.hwrapper.setObjectName(u"hwrapper")
        self.horizontalLayout_3 = QHBoxLayout(self.hwrapper)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.vwrapper = QWidget(self.hwrapper)
        self.vwrapper.setObjectName(u"vwrapper")
        self.vwrapper.setMinimumSize(QSize(531, 471))
        self.vwrapper.setMaximumSize(QSize(1120, 720))
        self.verticalLayout_9 = QVBoxLayout(self.vwrapper)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        self.verticalLayout_9.addItem(self.verticalSpacer)

        self.stackedWidget = QStackedWidget(self.vwrapper)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy1)
        self.stackedWidget.setMinimumSize(QSize(531, 370))
        self.tableView = QWidget()
        self.tableView.setObjectName(u"tableView")
        self.verticalLayout_10 = QVBoxLayout(self.tableView)
        self.verticalLayout_10.setSpacing(0)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.idTable = QTableWidget(self.tableView)
        if (self.idTable.columnCount() < 9):
            self.idTable.setColumnCount(9)
        self.idTable.setObjectName(u"idTable")
        self.idTable.setEnabled(True)
        sizePolicy1.setHeightForWidth(self.idTable.sizePolicy().hasHeightForWidth())
        self.idTable.setSizePolicy(sizePolicy1)
        self.idTable.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.idTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.idTable.setProperty(u"showDropIndicator", False)
        self.idTable.setAlternatingRowColors(False)
        self.idTable.setShowGrid(False)
        self.idTable.setCornerButtonEnabled(True)
        self.idTable.setColumnCount(9)
        self.idTable.horizontalHeader().setMinimumSectionSize(15)
        self.idTable.horizontalHeader().setDefaultSectionSize(105)

        self.verticalLayout_10.addWidget(self.idTable)

        self.stackedWidget.addWidget(self.tableView)
        self.logoView = QWidget()
        self.logoView.setObjectName(u"logoView")
        self.horizontalLayout_6 = QHBoxLayout(self.logoView)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.labelLogo = QLabel(self.logoView)
        self.labelLogo.setObjectName(u"labelLogo")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.labelLogo.sizePolicy().hasHeightForWidth())
        self.labelLogo.setSizePolicy(sizePolicy2)
        self.labelLogo.setMinimumSize(QSize(256, 256))
        self.labelLogo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_6.addWidget(self.labelLogo)

        self.stackedWidget.addWidget(self.logoView)
        self.configView = QWidget()
        self.configView.setObjectName(u"configView")
        self.verticalLayout_3 = QVBoxLayout(self.configView)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label = QLabel(self.configView)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QSize(0, 30))
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.label)

        self.configTabs = QTabWidget(self.configView)
        self.configTabs.setObjectName(u"configTabs")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.configTabs.sizePolicy().hasHeightForWidth())
        self.configTabs.setSizePolicy(sizePolicy3)
        self.configTabs.setMinimumSize(QSize(0, 0))
        self.tabGeneral = QWidget()
        self.tabGeneral.setObjectName(u"tabGeneral")
        self.verticalLayout_4 = QVBoxLayout(self.tabGeneral)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupSystemTray = QGroupBox(self.tabGeneral)
        self.groupSystemTray.setObjectName(u"groupSystemTray")
        self.verticalLayout_5 = QVBoxLayout(self.groupSystemTray)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(9, 6, 0, 0)
        self.checkEnableSysTray = QCheckBox(self.groupSystemTray)
        self.checkEnableSysTray.setObjectName(u"checkEnableSysTray")

        self.verticalLayout_5.addWidget(self.checkEnableSysTray)

        self.hwrapper_2 = QWidget(self.groupSystemTray)
        self.hwrapper_2.setObjectName(u"hwrapper_2")
        self.horizontalLayout_7 = QHBoxLayout(self.hwrapper_2)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_4 = QLabel(self.hwrapper_2)
        self.label_4.setObjectName(u"label_4")
        font1 = QFont()
        font1.setPointSize(10)
        self.label_4.setFont(font1)

        self.horizontalLayout_7.addWidget(self.label_4)

        self.splitter_5 = QWidget(self.hwrapper_2)
        self.splitter_5.setObjectName(u"splitter_5")
        self.horizontalLayout_19 = QHBoxLayout(self.splitter_5)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalLayout_19.setContentsMargins(-1, 0, -1, 0)
        self.comboOnWindowClose = QComboBox(self.splitter_5)
        self.comboOnWindowClose.addItem("")
        self.comboOnWindowClose.addItem("")
        self.comboOnWindowClose.setObjectName(u"comboOnWindowClose")
        self.comboOnWindowClose.setEnabled(False)
        self.comboOnWindowClose.setMinimumSize(QSize(180, 0))
        self.comboOnWindowClose.setMaximumSize(QSize(250, 16777215))

        self.horizontalLayout_19.addWidget(self.comboOnWindowClose)

        self.horizontalSpacer_8 = QSpacerItem(80, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_19.addItem(self.horizontalSpacer_8)


        self.horizontalLayout_7.addWidget(self.splitter_5)


        self.verticalLayout_5.addWidget(self.hwrapper_2)


        self.verticalLayout_4.addWidget(self.groupSystemTray)

        self.groupListeners = QGroupBox(self.tabGeneral)
        self.groupListeners.setObjectName(u"groupListeners")
        self.verticalLayout_11 = QVBoxLayout(self.groupListeners)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.hwrapper_9 = QWidget(self.groupListeners)
        self.hwrapper_9.setObjectName(u"hwrapper_9")
        self.horizontalLayout_20 = QHBoxLayout(self.hwrapper_9)
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalLayout_20.setContentsMargins(9, 9, 9, 9)
        self.checkListenAntminer = QCheckBox(self.hwrapper_9)
        self.checkListenAntminer.setObjectName(u"checkListenAntminer")
        self.checkListenAntminer.setChecked(True)

        self.horizontalLayout_20.addWidget(self.checkListenAntminer)

        self.checkListenWhatsminer = QCheckBox(self.hwrapper_9)
        self.checkListenWhatsminer.setObjectName(u"checkListenWhatsminer")
        self.checkListenWhatsminer.setChecked(True)

        self.horizontalLayout_20.addWidget(self.checkListenWhatsminer)

        self.checkListenIceRiver = QCheckBox(self.hwrapper_9)
        self.checkListenIceRiver.setObjectName(u"checkListenIceRiver")
        self.checkListenIceRiver.setChecked(True)

        self.horizontalLayout_20.addWidget(self.checkListenIceRiver)


        self.verticalLayout_11.addWidget(self.hwrapper_9)

        self.groupAdditional = QGroupBox(self.groupListeners)
        self.groupAdditional.setObjectName(u"groupAdditional")
        self.verticalLayout_12 = QVBoxLayout(self.groupAdditional)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(0, 0, 0, 0)
        self.hwrapper_8 = QWidget(self.groupAdditional)
        self.hwrapper_8.setObjectName(u"hwrapper_8")
        self.horizontalLayout_22 = QHBoxLayout(self.hwrapper_8)
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.checkListenVolcminer = QCheckBox(self.hwrapper_8)
        self.checkListenVolcminer.setObjectName(u"checkListenVolcminer")

        self.horizontalLayout_22.addWidget(self.checkListenVolcminer)


        self.verticalLayout_12.addWidget(self.hwrapper_8)


        self.verticalLayout_11.addWidget(self.groupAdditional)


        self.verticalLayout_4.addWidget(self.groupListeners)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_3)

        self.configTabs.addTab(self.tabGeneral, "")
        self.tabAPI = QWidget()
        self.tabAPI.setObjectName(u"tabAPI")
        self.verticalLayout_6 = QVBoxLayout(self.tabAPI)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.scrollArea = QScrollArea(self.tabAPI)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setAutoFillBackground(True)
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 344, 302))
        self.verticalLayout_13 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(9, 9, 9, 9)
        self.groupBitmain = QGroupBox(self.scrollAreaWidgetContents)
        self.groupBitmain.setObjectName(u"groupBitmain")
        self.horizontalLayout_12 = QHBoxLayout(self.groupBitmain)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_10 = QLabel(self.groupBitmain)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font1)

        self.horizontalLayout_12.addWidget(self.label_10)

        self.lineBitmainPasswd = QLineEdit(self.groupBitmain)
        self.lineBitmainPasswd.setObjectName(u"lineBitmainPasswd")
        sizePolicy.setHeightForWidth(self.lineBitmainPasswd.sizePolicy().hasHeightForWidth())
        self.lineBitmainPasswd.setSizePolicy(sizePolicy)
        self.lineBitmainPasswd.setFont(font1)
        self.lineBitmainPasswd.setEchoMode(QLineEdit.EchoMode.Password)
        self.lineBitmainPasswd.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_12.addWidget(self.lineBitmainPasswd)


        self.verticalLayout_13.addWidget(self.groupBitmain)

        self.groupWhatsminer = QGroupBox(self.scrollAreaWidgetContents)
        self.groupWhatsminer.setObjectName(u"groupWhatsminer")
        self.horizontalLayout_8 = QHBoxLayout(self.groupWhatsminer)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_11 = QLabel(self.groupWhatsminer)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font1)

        self.horizontalLayout_8.addWidget(self.label_11)

        self.lineWhatsminerPasswd = QLineEdit(self.groupWhatsminer)
        self.lineWhatsminerPasswd.setObjectName(u"lineWhatsminerPasswd")
        sizePolicy.setHeightForWidth(self.lineWhatsminerPasswd.sizePolicy().hasHeightForWidth())
        self.lineWhatsminerPasswd.setSizePolicy(sizePolicy)
        self.lineWhatsminerPasswd.setMinimumSize(QSize(180, 25))
        self.lineWhatsminerPasswd.setFont(font1)
        self.lineWhatsminerPasswd.setEchoMode(QLineEdit.EchoMode.Password)
        self.lineWhatsminerPasswd.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.lineWhatsminerPasswd)


        self.verticalLayout_13.addWidget(self.groupWhatsminer)

        self.groupVolcminer = QGroupBox(self.scrollAreaWidgetContents)
        self.groupVolcminer.setObjectName(u"groupVolcminer")
        self.horizontalLayout_21 = QHBoxLayout(self.groupVolcminer)
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.label_13 = QLabel(self.groupVolcminer)
        self.label_13.setObjectName(u"label_13")
        self.label_13.setFont(font1)

        self.horizontalLayout_21.addWidget(self.label_13)

        self.lineVolcminerPasswd = QLineEdit(self.groupVolcminer)
        self.lineVolcminerPasswd.setObjectName(u"lineVolcminerPasswd")
        sizePolicy.setHeightForWidth(self.lineVolcminerPasswd.sizePolicy().hasHeightForWidth())
        self.lineVolcminerPasswd.setSizePolicy(sizePolicy)
        self.lineVolcminerPasswd.setMinimumSize(QSize(180, 25))
        self.lineVolcminerPasswd.setFont(font1)
        self.lineVolcminerPasswd.setEchoMode(QLineEdit.EchoMode.Password)
        self.lineVolcminerPasswd.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_21.addWidget(self.lineVolcminerPasswd)


        self.verticalLayout_13.addWidget(self.groupVolcminer)

        self.groupPbfarmer = QGroupBox(self.scrollAreaWidgetContents)
        self.groupPbfarmer.setObjectName(u"groupPbfarmer")
        self.horizontalLayout_13 = QHBoxLayout(self.groupPbfarmer)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_12 = QLabel(self.groupPbfarmer)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setFont(font1)

        self.horizontalLayout_13.addWidget(self.label_12)

        self.linePbfarmerKey = QLineEdit(self.groupPbfarmer)
        self.linePbfarmerKey.setObjectName(u"linePbfarmerKey")
        sizePolicy.setHeightForWidth(self.linePbfarmerKey.sizePolicy().hasHeightForWidth())
        self.linePbfarmerKey.setSizePolicy(sizePolicy)
        self.linePbfarmerKey.setMinimumSize(QSize(180, 25))
        self.linePbfarmerKey.setFont(font1)
        self.linePbfarmerKey.setEchoMode(QLineEdit.EchoMode.Password)
        self.linePbfarmerKey.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_13.addWidget(self.linePbfarmerKey)


        self.verticalLayout_13.addWidget(self.groupPbfarmer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_6.addWidget(self.scrollArea)

        self.configTabs.addTab(self.tabAPI, "")
        self.tabLogs = QWidget()
        self.tabLogs.setObjectName(u"tabLogs")
        self.verticalLayout_7 = QVBoxLayout(self.tabLogs)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.groupLog = QGroupBox(self.tabLogs)
        self.groupLog.setObjectName(u"groupLog")
        self.verticalLayout_8 = QVBoxLayout(self.groupLog)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.hwrapper_3 = QWidget(self.groupLog)
        self.hwrapper_3.setObjectName(u"hwrapper_3")
        self.horizontalLayout_9 = QHBoxLayout(self.hwrapper_3)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(6, 6, 6, 6)
        self.label_5 = QLabel(self.hwrapper_3)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font1)

        self.horizontalLayout_9.addWidget(self.label_5)

        self.splitter = QWidget(self.hwrapper_3)
        self.splitter.setObjectName(u"splitter")
        self.horizontalLayout_18 = QHBoxLayout(self.splitter)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.horizontalLayout_18.setContentsMargins(-1, 0, -1, 0)
        self.comboLogLevel = QComboBox(self.splitter)
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.setObjectName(u"comboLogLevel")
        self.comboLogLevel.setMinimumSize(QSize(180, 0))
        self.comboLogLevel.setMaximumSize(QSize(250, 16777215))

        self.horizontalLayout_18.addWidget(self.comboLogLevel)

        self.horizontalSpacer_7 = QSpacerItem(80, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_18.addItem(self.horizontalSpacer_7)


        self.horizontalLayout_9.addWidget(self.splitter)


        self.verticalLayout_8.addWidget(self.hwrapper_3)

        self.hwrapper_5 = QWidget(self.groupLog)
        self.hwrapper_5.setObjectName(u"hwrapper_5")
        self.horizontalLayout_10 = QHBoxLayout(self.hwrapper_5)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(6, 6, 6, 6)
        self.label_7 = QLabel(self.hwrapper_5)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font1)

        self.horizontalLayout_10.addWidget(self.label_7)

        self.splitter_3 = QWidget(self.hwrapper_5)
        self.splitter_3.setObjectName(u"splitter_3")
        self.horizontalLayout_17 = QHBoxLayout(self.splitter_3)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.horizontalLayout_17.setContentsMargins(9, 0, 9, 0)
        self.spinMaxLogSize = QSpinBox(self.splitter_3)
        self.spinMaxLogSize.setObjectName(u"spinMaxLogSize")
        self.spinMaxLogSize.setMinimumSize(QSize(180, 0))
        self.spinMaxLogSize.setMaximumSize(QSize(250, 16777215))
        self.spinMaxLogSize.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinMaxLogSize.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinMaxLogSize.setProperty(u"showGroupSeparator", True)
        self.spinMaxLogSize.setMinimum(1)
        self.spinMaxLogSize.setMaximum(4096)
        self.spinMaxLogSize.setValue(1024)

        self.horizontalLayout_17.addWidget(self.spinMaxLogSize)

        self.horizontalSpacer_6 = QSpacerItem(80, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_17.addItem(self.horizontalSpacer_6)


        self.horizontalLayout_10.addWidget(self.splitter_3)


        self.verticalLayout_8.addWidget(self.hwrapper_5)

        self.hwrapper_6 = QWidget(self.groupLog)
        self.hwrapper_6.setObjectName(u"hwrapper_6")
        self.horizontalLayout_11 = QHBoxLayout(self.hwrapper_6)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(6, 6, 6, 6)
        self.label_8 = QLabel(self.hwrapper_6)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font1)

        self.horizontalLayout_11.addWidget(self.label_8)

        self.splitter_4 = QWidget(self.hwrapper_6)
        self.splitter_4.setObjectName(u"splitter_4")
        self.horizontalLayout_16 = QHBoxLayout(self.splitter_4)
        self.horizontalLayout_16.setSpacing(6)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.horizontalLayout_16.setContentsMargins(9, 0, 9, 0)
        self.comboOnMaxLogSize = QComboBox(self.splitter_4)
        self.comboOnMaxLogSize.addItem("")
        self.comboOnMaxLogSize.addItem("")
        self.comboOnMaxLogSize.setObjectName(u"comboOnMaxLogSize")
        self.comboOnMaxLogSize.setMinimumSize(QSize(180, 0))
        self.comboOnMaxLogSize.setMaximumSize(QSize(250, 16777215))

        self.horizontalLayout_16.addWidget(self.comboOnMaxLogSize)

        self.horizontalSpacer_5 = QSpacerItem(80, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_16.addItem(self.horizontalSpacer_5)


        self.horizontalLayout_11.addWidget(self.splitter_4)


        self.verticalLayout_8.addWidget(self.hwrapper_6)

        self.hwrapper_4 = QWidget(self.groupLog)
        self.hwrapper_4.setObjectName(u"hwrapper_4")
        self.horizontalLayout_14 = QHBoxLayout(self.hwrapper_4)
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.horizontalLayout_14.setContentsMargins(6, 6, 6, 6)
        self.label_6 = QLabel(self.hwrapper_4)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font1)

        self.horizontalLayout_14.addWidget(self.label_6)

        self.splitter_2 = QWidget(self.hwrapper_4)
        self.splitter_2.setObjectName(u"splitter_2")
        self.horizontalLayout_4 = QHBoxLayout(self.splitter_2)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(9, 0, 9, 0)
        self.comboFlushInterval = QComboBox(self.splitter_2)
        self.comboFlushInterval.addItem("")
        self.comboFlushInterval.addItem("")
        self.comboFlushInterval.setObjectName(u"comboFlushInterval")
        self.comboFlushInterval.setEnabled(True)
        self.comboFlushInterval.setMinimumSize(QSize(180, 0))
        self.comboFlushInterval.setMaximumSize(QSize(250, 16777215))

        self.horizontalLayout_4.addWidget(self.comboFlushInterval)

        self.horizontalSpacer_4 = QSpacerItem(80, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)


        self.horizontalLayout_14.addWidget(self.splitter_2)


        self.verticalLayout_8.addWidget(self.hwrapper_4)


        self.verticalLayout_7.addWidget(self.groupLog)

        self.configTabs.addTab(self.tabLogs, "")

        self.verticalLayout_3.addWidget(self.configTabs)

        self.hwrapper_7 = QWidget(self.configView)
        self.hwrapper_7.setObjectName(u"hwrapper_7")
        self.horizontalLayout_15 = QHBoxLayout(self.hwrapper_7)
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.actionIPRCancelConfig = QPushButton(self.hwrapper_7)
        self.actionIPRCancelConfig.setObjectName(u"actionIPRCancelConfig")
        font2 = QFont()
        font2.setPointSize(10)
        font2.setBold(True)
        self.actionIPRCancelConfig.setFont(font2)

        self.horizontalLayout_15.addWidget(self.actionIPRCancelConfig)

        self.actionIPRSaveConfig = QPushButton(self.hwrapper_7)
        self.actionIPRSaveConfig.setObjectName(u"actionIPRSaveConfig")
        self.actionIPRSaveConfig.setFont(font2)

        self.horizontalLayout_15.addWidget(self.actionIPRSaveConfig)


        self.verticalLayout_3.addWidget(self.hwrapper_7)

        self.stackedWidget.addWidget(self.configView)

        self.verticalLayout_9.addWidget(self.stackedWidget)

        self.verticalSpacer_2 = QSpacerItem(20, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)

        self.verticalLayout_9.addItem(self.verticalSpacer_2)

        self.listenControls = QWidget(self.vwrapper)
        self.listenControls.setObjectName(u"listenControls")
        self.horizontalLayout_5 = QHBoxLayout(self.listenControls)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(-1, -1, -1, 20)
        self.actionIPRStart = QPushButton(self.listenControls)
        self.actionIPRStart.setObjectName(u"actionIPRStart")
        self.actionIPRStart.setFont(font)

        self.horizontalLayout_5.addWidget(self.actionIPRStart)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.actionIPRStop = QPushButton(self.listenControls)
        self.actionIPRStop.setObjectName(u"actionIPRStop")
        self.actionIPRStop.setEnabled(False)
        self.actionIPRStop.setFont(font)

        self.horizontalLayout_5.addWidget(self.actionIPRStop)


        self.verticalLayout_9.addWidget(self.listenControls)


        self.horizontalLayout_3.addWidget(self.vwrapper)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addWidget(self.hwrapper)

        MainWindow.setCentralWidget(self.centralwidget)
        self.iprStatus = QStatusBar(MainWindow)
        self.iprStatus.setObjectName(u"iprStatus")
        self.iprStatus.setFont(font1)
        MainWindow.setStatusBar(self.iprStatus)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(1)
        self.configTabs.setCurrentIndex(0)
        self.comboOnWindowClose.setCurrentIndex(0)
        self.comboLogLevel.setCurrentIndex(1)
        self.actionIPRStart.setDefault(True)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"BitCap IPReporter", None))
        self.labelLogo.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Configuration", None))
        self.label.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.groupSystemTray.setTitle(QCoreApplication.translate("MainWindow", u"System Tray", None))
        self.checkEnableSysTray.setText(QCoreApplication.translate("MainWindow", u"Enable System Tray", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"On Window Close:", None))
        self.label_4.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.comboOnWindowClose.setItemText(0, QCoreApplication.translate("MainWindow", u"Close", None))
        self.comboOnWindowClose.setItemText(1, QCoreApplication.translate("MainWindow", u"Minimize To Tray", None))

        self.groupListeners.setTitle(QCoreApplication.translate("MainWindow", u"Listener Configuraion", None))
#if QT_CONFIG(tooltip)
        self.checkListenAntminer.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Antminers", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenAntminer.setText(QCoreApplication.translate("MainWindow", u"Antminer", None))
#if QT_CONFIG(tooltip)
        self.checkListenWhatsminer.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Whatsminers", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenWhatsminer.setText(QCoreApplication.translate("MainWindow", u"Whatsminer", None))
#if QT_CONFIG(tooltip)
        self.checkListenIceRiver.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Icerivers", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenIceRiver.setText(QCoreApplication.translate("MainWindow", u"IceRiver", None))
        self.groupAdditional.setTitle(QCoreApplication.translate("MainWindow", u"Additional Miners", None))
#if QT_CONFIG(tooltip)
        self.checkListenVolcminer.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Volcminers (Experimental)", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenVolcminer.setText(QCoreApplication.translate("MainWindow", u"Volcminer", None))
        self.configTabs.setTabText(self.configTabs.indexOf(self.tabGeneral), QCoreApplication.translate("MainWindow", u"General", None))
#if QT_CONFIG(tooltip)
        self.configTabs.setTabToolTip(self.configTabs.indexOf(self.tabGeneral), QCoreApplication.translate("MainWindow", u"General Settings", None))
#endif // QT_CONFIG(tooltip)
        self.groupBitmain.setTitle(QCoreApplication.translate("MainWindow", u"Bitmain/Antminer", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Set Login Password:", None))
        self.label_10.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineBitmainPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Antminers. Default: \"root\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupWhatsminer.setTitle(QCoreApplication.translate("MainWindow", u"Whatsminer", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Set Login Password:", None))
        self.label_11.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineWhatsminerPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Whatsminer. Default: \"admin\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupVolcminer.setTitle(QCoreApplication.translate("MainWindow", u"Volcminer", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Set Login Password:", None))
        self.label_13.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineVolcminerPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Volcminer. Default: \"ltc@dog\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupPbfarmer.setTitle(QCoreApplication.translate("MainWindow", u"pbfarmer", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Set API Key:", None))
        self.label_12.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.linePbfarmerKey.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative API Key for pbfarmer. Default API key is supplied if blank", None))
#endif // QT_CONFIG(tooltip)
        self.configTabs.setTabText(self.configTabs.indexOf(self.tabAPI), QCoreApplication.translate("MainWindow", u"API", None))
#if QT_CONFIG(tooltip)
        self.configTabs.setTabToolTip(self.configTabs.indexOf(self.tabAPI), QCoreApplication.translate("MainWindow", u"API Settings", None))
#endif // QT_CONFIG(tooltip)
        self.groupLog.setTitle(QCoreApplication.translate("MainWindow", u"Log Settings", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Log Level: ", None))
        self.label_5.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.comboLogLevel.setItemText(0, QCoreApplication.translate("MainWindow", u"DEBUG", None))
        self.comboLogLevel.setItemText(1, QCoreApplication.translate("MainWindow", u"INFO", None))
        self.comboLogLevel.setItemText(2, QCoreApplication.translate("MainWindow", u"WARNING", None))
        self.comboLogLevel.setItemText(3, QCoreApplication.translate("MainWindow", u"ERROR", None))
        self.comboLogLevel.setItemText(4, QCoreApplication.translate("MainWindow", u"CRITICAL", None))

#if QT_CONFIG(tooltip)
        self.comboLogLevel.setToolTip(QCoreApplication.translate("MainWindow", u"Change minimum output level", None))
#endif // QT_CONFIG(tooltip)
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Max Log Size:", None))
#if QT_CONFIG(tooltip)
        self.spinMaxLogSize.setToolTip(QCoreApplication.translate("MainWindow", u"Set maximum log file size (Max limit 4096kb)", None))
#endif // QT_CONFIG(tooltip)
        self.spinMaxLogSize.setSuffix(QCoreApplication.translate("MainWindow", u" KB", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"On Max Log Size:", None))
        self.comboOnMaxLogSize.setItemText(0, QCoreApplication.translate("MainWindow", u"Flush", None))
        self.comboOnMaxLogSize.setItemText(1, QCoreApplication.translate("MainWindow", u"Rotate", None))

#if QT_CONFIG(tooltip)
        self.comboOnMaxLogSize.setToolTip(QCoreApplication.translate("MainWindow", u"Choose behavior for when log file reaches set max size", None))
#endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Flush Interval: ", None))
        self.label_6.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.comboFlushInterval.setItemText(0, QCoreApplication.translate("MainWindow", u"On Log Size", None))
        self.comboFlushInterval.setItemText(1, QCoreApplication.translate("MainWindow", u"Close", None))

#if QT_CONFIG(tooltip)
        self.comboFlushInterval.setToolTip(QCoreApplication.translate("MainWindow", u"Choose when to flush log file", None))
#endif // QT_CONFIG(tooltip)
        self.configTabs.setTabText(self.configTabs.indexOf(self.tabLogs), QCoreApplication.translate("MainWindow", u"Logs", None))
#if QT_CONFIG(tooltip)
        self.configTabs.setTabToolTip(self.configTabs.indexOf(self.tabLogs), QCoreApplication.translate("MainWindow", u"Log Settings", None))
#endif // QT_CONFIG(tooltip)
        self.actionIPRCancelConfig.setText(QCoreApplication.translate("MainWindow", u"Cancel", None))
        self.actionIPRSaveConfig.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionIPRStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.actionIPRStop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
#if QT_CONFIG(tooltip)
        self.iprStatus.setToolTip(QCoreApplication.translate("MainWindow", u"Current IPR Status", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

