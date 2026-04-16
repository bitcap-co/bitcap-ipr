# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
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
    QComboBox, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QSpinBox, QStackedWidget, QStatusBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(550, 550)
        MainWindow.setMinimumSize(QSize(550, 550))
        MainWindow.setMaximumSize(QSize(1280, 800))
        MainWindow.setStyleSheet(u"QWidget#centralwidget {\n"
"	background-color:qlineargradient(spread:pad, x1:0.500, y1:0, x2:0.500, y2:1, stop:0.5 rgba(6, 16, 31, 255), stop:1 rgba(0, 0, 0, 255));\n"
"}")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.topBar = QWidget(self.centralwidget)
        self.topBar.setObjectName(u"topBar")
        self.topBar.setMinimumSize(QSize(550, 58))
        self.topBar.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.verticalLayout_15 = QVBoxLayout(self.topBar)
        self.verticalLayout_15.setSpacing(0)
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(0, 0, 0, 0)
        self.titleBarWidget = QWidget(self.topBar)
        self.titleBarWidget.setObjectName(u"titleBarWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.titleBarWidget.sizePolicy().hasHeightForWidth())
        self.titleBarWidget.setSizePolicy(sizePolicy)
        self.titleBarWidget.setMinimumSize(QSize(550, 30))
        self.horizontalLayout_2 = QHBoxLayout(self.titleBarWidget)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_15.addWidget(self.titleBarWidget)

        self.menuBarWidget = QWidget(self.topBar)
        self.menuBarWidget.setObjectName(u"menuBarWidget")
        sizePolicy.setHeightForWidth(self.menuBarWidget.sizePolicy().hasHeightForWidth())
        self.menuBarWidget.setSizePolicy(sizePolicy)
        self.menuBarWidget.setMinimumSize(QSize(550, 26))
        self.horizontalLayout = QHBoxLayout(self.menuBarWidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_15.addWidget(self.menuBarWidget)

        self.poolConfigurator = QWidget(self.topBar)
        self.poolConfigurator.setObjectName(u"poolConfigurator")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.poolConfigurator.sizePolicy().hasHeightForWidth())
        self.poolConfigurator.setSizePolicy(sizePolicy1)
        self.verticalLayout_14 = QVBoxLayout(self.poolConfigurator)
        self.verticalLayout_14.setSpacing(10)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(-1, 0, -1, -1)
        self.pcwrapper = QFrame(self.poolConfigurator)
        self.pcwrapper.setObjectName(u"pcwrapper")
        self.pcwrapper.setMinimumSize(QSize(532, 171))
        self.pcwrapper.setMaximumSize(QSize(1260, 185))
        self.pcwrapper.setFrameShape(QFrame.Shape.NoFrame)
        self.pcwrapper.setFrameShadow(QFrame.Shadow.Plain)
        self.verticalLayout_13 = QVBoxLayout(self.pcwrapper)
        self.verticalLayout_13.setSpacing(10)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalLayout_13.setContentsMargins(-1, 15, -1, -1)
        self.presetControl = QWidget(self.pcwrapper)
        self.presetControl.setObjectName(u"presetControl")
        self.presetControl.setMinimumSize(QSize(0, 50))
        self.horizontalLayout_4 = QHBoxLayout(self.presetControl)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.presetSet = QWidget(self.presetControl)
        self.presetSet.setObjectName(u"presetSet")
        self.presetSet.setMaximumSize(QSize(450, 16777215))
        self.horizontalLayout_5 = QHBoxLayout(self.presetSet)
        self.horizontalLayout_5.setSpacing(5)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(10, 9, 9, 9)
        self.label_25 = QLabel(self.presetSet)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setMaximumSize(QSize(65, 32))
        self.label_25.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_25)

        self.comboPoolPreset = QComboBox(self.presetSet)
        self.comboPoolPreset.setObjectName(u"comboPoolPreset")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.comboPoolPreset.sizePolicy().hasHeightForWidth())
        self.comboPoolPreset.setSizePolicy(sizePolicy2)
        self.comboPoolPreset.setMinimumSize(QSize(110, 25))
        self.comboPoolPreset.setMaximumSize(QSize(280, 25))
        self.comboPoolPreset.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.comboPoolPreset.setEditable(True)
        self.comboPoolPreset.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.horizontalLayout_5.addWidget(self.comboPoolPreset)

        self.actionIPRCreatePreset = QToolButton(self.presetSet)
        self.actionIPRCreatePreset.setObjectName(u"actionIPRCreatePreset")
        self.actionIPRCreatePreset.setMinimumSize(QSize(25, 22))
        self.actionIPRCreatePreset.setMaximumSize(QSize(25, 22))
        font = QFont()
        font.setBold(True)
        self.actionIPRCreatePreset.setFont(font)

        self.horizontalLayout_5.addWidget(self.actionIPRCreatePreset)

        self.actionIPRRemovePreset = QToolButton(self.presetSet)
        self.actionIPRRemovePreset.setObjectName(u"actionIPRRemovePreset")
        self.actionIPRRemovePreset.setMinimumSize(QSize(25, 22))
        self.actionIPRRemovePreset.setMaximumSize(QSize(25, 22))
        self.actionIPRRemovePreset.setFont(font)

        self.horizontalLayout_5.addWidget(self.actionIPRRemovePreset)


        self.horizontalLayout_4.addWidget(self.presetSet)

        self.horizontalSpacer_2 = QSpacerItem(0, 20, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.presetButtons = QWidget(self.presetControl)
        self.presetButtons.setObjectName(u"presetButtons")
        self.presetButtons.setMaximumSize(QSize(300, 16777215))
        self.horizontalLayout_6 = QHBoxLayout(self.presetButtons)
        self.horizontalLayout_6.setSpacing(5)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.checkAutomaticWorkerNames = QCheckBox(self.presetButtons)
        self.checkAutomaticWorkerNames.setObjectName(u"checkAutomaticWorkerNames")
        self.checkAutomaticWorkerNames.setMinimumSize(QSize(95, 25))
        self.checkAutomaticWorkerNames.setMaximumSize(QSize(130, 25))

        self.horizontalLayout_6.addWidget(self.checkAutomaticWorkerNames)

        self.actionIPRSavePreset = QPushButton(self.presetButtons)
        self.actionIPRSavePreset.setObjectName(u"actionIPRSavePreset")
        self.actionIPRSavePreset.setMaximumSize(QSize(180, 25))

        self.horizontalLayout_6.addWidget(self.actionIPRSavePreset)

        self.actionIPRClearPreset = QPushButton(self.presetButtons)
        self.actionIPRClearPreset.setObjectName(u"actionIPRClearPreset")
        self.actionIPRClearPreset.setMaximumSize(QSize(180, 25))

        self.horizontalLayout_6.addWidget(self.actionIPRClearPreset)


        self.horizontalLayout_4.addWidget(self.presetButtons)


        self.verticalLayout_13.addWidget(self.presetControl)

        self.pool1Config = QWidget(self.pcwrapper)
        self.pool1Config.setObjectName(u"pool1Config")
        self.pool1Config.setMinimumSize(QSize(0, 50))
        self.horizontalLayout_22 = QHBoxLayout(self.pool1Config)
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.label_19 = QLabel(self.pool1Config)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_22.addWidget(self.label_19)

        self.linePoolURL = QLineEdit(self.pool1Config)
        self.linePoolURL.setObjectName(u"linePoolURL")
        self.linePoolURL.setMinimumSize(QSize(130, 25))
        self.linePoolURL.setMaximumSize(QSize(415, 25))

        self.horizontalLayout_22.addWidget(self.linePoolURL)

        self.label_20 = QLabel(self.pool1Config)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_22.addWidget(self.label_20)

        self.linePoolUser = QLineEdit(self.pool1Config)
        self.linePoolUser.setObjectName(u"linePoolUser")
        self.linePoolUser.setMinimumSize(QSize(130, 25))
        self.linePoolUser.setMaximumSize(QSize(415, 25))

        self.horizontalLayout_22.addWidget(self.linePoolUser)

        self.label_21 = QLabel(self.pool1Config)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_22.addWidget(self.label_21)

        self.linePoolPasswd = QLineEdit(self.pool1Config)
        self.linePoolPasswd.setObjectName(u"linePoolPasswd")
        self.linePoolPasswd.setMinimumSize(QSize(0, 25))
        self.linePoolPasswd.setMaximumSize(QSize(150, 25))
        self.linePoolPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.horizontalLayout_22.addWidget(self.linePoolPasswd)


        self.verticalLayout_13.addWidget(self.pool1Config)

        self.pool2Config = QWidget(self.pcwrapper)
        self.pool2Config.setObjectName(u"pool2Config")
        self.pool2Config.setMinimumSize(QSize(0, 50))
        self.horizontalLayout_29 = QHBoxLayout(self.pool2Config)
        self.horizontalLayout_29.setObjectName(u"horizontalLayout_29")
        self.label_24 = QLabel(self.pool2Config)
        self.label_24.setObjectName(u"label_24")
        self.label_24.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_29.addWidget(self.label_24)

        self.linePoolURL_2 = QLineEdit(self.pool2Config)
        self.linePoolURL_2.setObjectName(u"linePoolURL_2")
        self.linePoolURL_2.setMinimumSize(QSize(130, 25))
        self.linePoolURL_2.setMaximumSize(QSize(415, 25))

        self.horizontalLayout_29.addWidget(self.linePoolURL_2)

        self.label_26 = QLabel(self.pool2Config)
        self.label_26.setObjectName(u"label_26")
        self.label_26.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_29.addWidget(self.label_26)

        self.linePoolUser_2 = QLineEdit(self.pool2Config)
        self.linePoolUser_2.setObjectName(u"linePoolUser_2")
        self.linePoolUser_2.setMinimumSize(QSize(130, 25))
        self.linePoolUser_2.setMaximumSize(QSize(415, 25))

        self.horizontalLayout_29.addWidget(self.linePoolUser_2)

        self.label_27 = QLabel(self.pool2Config)
        self.label_27.setObjectName(u"label_27")
        self.label_27.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_29.addWidget(self.label_27)

        self.linePoolPasswd_2 = QLineEdit(self.pool2Config)
        self.linePoolPasswd_2.setObjectName(u"linePoolPasswd_2")
        self.linePoolPasswd_2.setMinimumSize(QSize(0, 25))
        self.linePoolPasswd_2.setMaximumSize(QSize(150, 25))
        self.linePoolPasswd_2.setEchoMode(QLineEdit.EchoMode.Password)

        self.horizontalLayout_29.addWidget(self.linePoolPasswd_2)


        self.verticalLayout_13.addWidget(self.pool2Config)

        self.pool3Config = QWidget(self.pcwrapper)
        self.pool3Config.setObjectName(u"pool3Config")
        self.pool3Config.setMinimumSize(QSize(0, 50))
        self.horizontalLayout_19 = QHBoxLayout(self.pool3Config)
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.label_4 = QLabel(self.pool3Config)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_19.addWidget(self.label_4)

        self.linePoolURL_3 = QLineEdit(self.pool3Config)
        self.linePoolURL_3.setObjectName(u"linePoolURL_3")
        self.linePoolURL_3.setMinimumSize(QSize(130, 0))
        self.linePoolURL_3.setMaximumSize(QSize(415, 16777215))

        self.horizontalLayout_19.addWidget(self.linePoolURL_3)

        self.label_22 = QLabel(self.pool3Config)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_19.addWidget(self.label_22)

        self.linePoolUser_3 = QLineEdit(self.pool3Config)
        self.linePoolUser_3.setObjectName(u"linePoolUser_3")
        self.linePoolUser_3.setMinimumSize(QSize(130, 25))
        self.linePoolUser_3.setMaximumSize(QSize(415, 25))

        self.horizontalLayout_19.addWidget(self.linePoolUser_3)

        self.label_23 = QLabel(self.pool3Config)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_19.addWidget(self.label_23)

        self.linePoolPasswd_3 = QLineEdit(self.pool3Config)
        self.linePoolPasswd_3.setObjectName(u"linePoolPasswd_3")
        self.linePoolPasswd_3.setMinimumSize(QSize(0, 25))
        self.linePoolPasswd_3.setMaximumSize(QSize(150, 25))
        self.linePoolPasswd_3.setEchoMode(QLineEdit.EchoMode.Password)

        self.horizontalLayout_19.addWidget(self.linePoolPasswd_3)


        self.verticalLayout_13.addWidget(self.pool3Config)


        self.verticalLayout_14.addWidget(self.pcwrapper)


        self.verticalLayout_15.addWidget(self.poolConfigurator)


        self.verticalLayout.addWidget(self.topBar)

        self.vwrapper = QVBoxLayout()
        self.vwrapper.setSpacing(0)
        self.vwrapper.setObjectName(u"vwrapper")
        self.vwrapper.setContentsMargins(9, 9, 9, 9)
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Ignored)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy3)
        self.stackedWidget.setMinimumSize(QSize(530, 360))
        self.defaultView = QWidget()
        self.defaultView.setObjectName(u"defaultView")
        self.horizontalLayout_3 = QHBoxLayout(self.defaultView)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.labelIPRLogo = QLabel(self.defaultView)
        self.labelIPRLogo.setObjectName(u"labelIPRLogo")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.labelIPRLogo.sizePolicy().hasHeightForWidth())
        self.labelIPRLogo.setSizePolicy(sizePolicy4)
        self.labelIPRLogo.setMinimumSize(QSize(256, 256))
        self.labelIPRLogo.setMaximumSize(QSize(256, 256))
        self.labelIPRLogo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalLayout_21 = QVBoxLayout(self.labelIPRLogo)
        self.verticalLayout_21.setSpacing(10)
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")

        self.horizontalLayout_3.addWidget(self.labelIPRLogo, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.stackedWidget.addWidget(self.defaultView)
        self.tableView = QWidget()
        self.tableView.setObjectName(u"tableView")
        self.verticalLayout_2 = QVBoxLayout(self.tableView)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tableIPRID = QTableWidget(self.tableView)
        if (self.tableIPRID.columnCount() < 15):
            self.tableIPRID.setColumnCount(15)
        self.tableIPRID.setObjectName(u"tableIPRID")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.tableIPRID.sizePolicy().hasHeightForWidth())
        self.tableIPRID.setSizePolicy(sizePolicy5)
        self.tableIPRID.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.tableIPRID.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableIPRID.setProperty(u"showDropIndicator", False)
        self.tableIPRID.setShowGrid(False)
        self.tableIPRID.setSortingEnabled(True)
        self.tableIPRID.setColumnCount(15)
        self.tableIPRID.horizontalHeader().setMinimumSectionSize(15)
        self.tableIPRID.horizontalHeader().setDefaultSectionSize(105)

        self.verticalLayout_2.addWidget(self.tableIPRID)

        self.stackedWidget.addWidget(self.tableView)
        self.settingsView = QWidget()
        self.settingsView.setObjectName(u"settingsView")
        self.verticalLayout_3 = QVBoxLayout(self.settingsView)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label = QLabel(self.settingsView)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setPointSize(14)
        font1.setBold(True)
        self.label.setFont(font1)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.label)

        self.tabWidget = QTabWidget(self.settingsView)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabGeneral = QWidget()
        self.tabGeneral.setObjectName(u"tabGeneral")
        self.verticalLayout_4 = QVBoxLayout(self.tabGeneral)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.scrollArea = QScrollArea(self.tabGeneral)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea.setFrameShadow(QFrame.Shadow.Plain)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollGeneral = QWidget()
        self.scrollGeneral.setObjectName(u"scrollGeneral")
        self.scrollGeneral.setGeometry(QRect(0, 0, 478, 563))
        self.verticalLayout_5 = QVBoxLayout(self.scrollGeneral)
        self.verticalLayout_5.setSpacing(15)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupSystemTray = QGroupBox(self.scrollGeneral)
        self.groupSystemTray.setObjectName(u"groupSystemTray")
        self.gridLayout_2 = QGridLayout(self.groupSystemTray)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_2 = QLabel(self.groupSystemTray)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 1, 0, 1, 1)

        self.checkEnableSysTray = QCheckBox(self.groupSystemTray)
        self.checkEnableSysTray.setObjectName(u"checkEnableSysTray")

        self.gridLayout_2.addWidget(self.checkEnableSysTray, 0, 0, 1, 1)

        self.comboOnWindowClose = QComboBox(self.groupSystemTray)
        self.comboOnWindowClose.addItem("")
        self.comboOnWindowClose.addItem("")
        self.comboOnWindowClose.setObjectName(u"comboOnWindowClose")
        self.comboOnWindowClose.setEnabled(False)
        self.comboOnWindowClose.setMinimumSize(QSize(180, 25))
        self.comboOnWindowClose.setMaximumSize(QSize(250, 25))
        self.comboOnWindowClose.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.gridLayout_2.addWidget(self.comboOnWindowClose, 1, 1, 1, 1)


        self.verticalLayout_5.addWidget(self.groupSystemTray)

        self.groupInactiveTimer = QGroupBox(self.scrollGeneral)
        self.groupInactiveTimer.setObjectName(u"groupInactiveTimer")
        self.gridLayout_3 = QGridLayout(self.groupInactiveTimer)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_3 = QLabel(self.groupInactiveTimer)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_3.addWidget(self.label_3, 1, 0, 1, 1)

        self.checkUseCustomTimeout = QCheckBox(self.groupInactiveTimer)
        self.checkUseCustomTimeout.setObjectName(u"checkUseCustomTimeout")

        self.gridLayout_3.addWidget(self.checkUseCustomTimeout, 0, 0, 1, 1)

        self.spinInactiveTimeout = QSpinBox(self.groupInactiveTimer)
        self.spinInactiveTimeout.setObjectName(u"spinInactiveTimeout")
        self.spinInactiveTimeout.setEnabled(False)
        self.spinInactiveTimeout.setMinimumSize(QSize(180, 25))
        self.spinInactiveTimeout.setMaximumSize(QSize(250, 25))
        self.spinInactiveTimeout.setWrapping(True)
        self.spinInactiveTimeout.setFrame(True)
        self.spinInactiveTimeout.setProperty(u"showGroupSeparator", True)
        self.spinInactiveTimeout.setMinimum(15)
        self.spinInactiveTimeout.setMaximum(120)
        self.spinInactiveTimeout.setSingleStep(15)
        self.spinInactiveTimeout.setValue(15)

        self.gridLayout_3.addWidget(self.spinInactiveTimeout, 1, 1, 1, 1)


        self.verticalLayout_5.addWidget(self.groupInactiveTimer)

        self.groupListenerConfig = QGroupBox(self.scrollGeneral)
        self.groupListenerConfig.setObjectName(u"groupListenerConfig")
        self.verticalLayout_6 = QVBoxLayout(self.groupListenerConfig)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.checkEnableListenFilter = QCheckBox(self.groupListenerConfig)
        self.checkEnableListenFilter.setObjectName(u"checkEnableListenFilter")

        self.verticalLayout_6.addWidget(self.checkEnableListenFilter)

        self.groupListeners = QGroupBox(self.groupListenerConfig)
        self.groupListeners.setObjectName(u"groupListeners")
        self.groupListeners.setCheckable(True)
        self.groupListeners.setChecked(False)
        self.gridLayout_4 = QGridLayout(self.groupListeners)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setHorizontalSpacing(70)
        self.gridLayout_4.setVerticalSpacing(15)
        self.gridLayout_4.setContentsMargins(9, 15, 9, 9)
        self.checkListenWhatsminer = QCheckBox(self.groupListeners)
        self.checkListenWhatsminer.setObjectName(u"checkListenWhatsminer")
        self.checkListenWhatsminer.setMaximumSize(QSize(100, 30))
        self.checkListenWhatsminer.setChecked(False)

        self.gridLayout_4.addWidget(self.checkListenWhatsminer, 2, 2, 1, 1)

        self.checkListenAntminer = QCheckBox(self.groupListeners)
        self.checkListenAntminer.setObjectName(u"checkListenAntminer")
        self.checkListenAntminer.setMaximumSize(QSize(100, 30))
        self.checkListenAntminer.setChecked(False)

        self.gridLayout_4.addWidget(self.checkListenAntminer, 2, 0, 1, 1)

        self.checkListenIceRiver = QCheckBox(self.groupListeners)
        self.checkListenIceRiver.setObjectName(u"checkListenIceRiver")
        self.checkListenIceRiver.setMaximumSize(QSize(100, 30))
        self.checkListenIceRiver.setChecked(False)

        self.gridLayout_4.addWidget(self.checkListenIceRiver, 2, 1, 1, 1)

        self.checkListenSealminer = QCheckBox(self.groupListeners)
        self.checkListenSealminer.setObjectName(u"checkListenSealminer")
        self.checkListenSealminer.setMaximumSize(QSize(100, 30))

        self.gridLayout_4.addWidget(self.checkListenSealminer, 3, 0, 1, 1)

        self.checkListenVolcminer = QCheckBox(self.groupListeners)
        self.checkListenVolcminer.setObjectName(u"checkListenVolcminer")
        self.checkListenVolcminer.setMaximumSize(QSize(100, 30))

        self.gridLayout_4.addWidget(self.checkListenVolcminer, 3, 2, 1, 1)

        self.checkListenElphapex = QCheckBox(self.groupListeners)
        self.checkListenElphapex.setObjectName(u"checkListenElphapex")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.checkListenElphapex.sizePolicy().hasHeightForWidth())
        self.checkListenElphapex.setSizePolicy(sizePolicy6)
        self.checkListenElphapex.setMaximumSize(QSize(100, 30))

        self.gridLayout_4.addWidget(self.checkListenElphapex, 4, 0, 1, 1)

        self.checkListenGoldshell = QCheckBox(self.groupListeners)
        self.checkListenGoldshell.setObjectName(u"checkListenGoldshell")
        self.checkListenGoldshell.setMaximumSize(QSize(100, 30))

        self.gridLayout_4.addWidget(self.checkListenGoldshell, 4, 1, 1, 1)

        self.checkListenHammer = QCheckBox(self.groupListeners)
        self.checkListenHammer.setObjectName(u"checkListenHammer")
        self.checkListenHammer.setMaximumSize(QSize(100, 30))

        self.gridLayout_4.addWidget(self.checkListenHammer, 3, 1, 1, 1)


        self.verticalLayout_6.addWidget(self.groupListeners)

        self.groupIPRD = QGroupBox(self.groupListenerConfig)
        self.groupIPRD.setObjectName(u"groupIPRD")
        self.gridLayout_17 = QGridLayout(self.groupIPRD)
        self.gridLayout_17.setObjectName(u"gridLayout_17")
        self.checkEnableIPRDBackend = QCheckBox(self.groupIPRD)
        self.checkEnableIPRDBackend.setObjectName(u"checkEnableIPRDBackend")

        self.gridLayout_17.addWidget(self.checkEnableIPRDBackend, 0, 0, 1, 1)

        self.label_6 = QLabel(self.groupIPRD)
        self.label_6.setObjectName(u"label_6")

        self.gridLayout_17.addWidget(self.label_6, 1, 0, 1, 1)

        self.lineIPRDSocketAddress = QLineEdit(self.groupIPRD)
        self.lineIPRDSocketAddress.setObjectName(u"lineIPRDSocketAddress")
        sizePolicy.setHeightForWidth(self.lineIPRDSocketAddress.sizePolicy().hasHeightForWidth())
        self.lineIPRDSocketAddress.setSizePolicy(sizePolicy)
        self.lineIPRDSocketAddress.setMinimumSize(QSize(180, 25))
        self.lineIPRDSocketAddress.setMaximumSize(QSize(225, 25))
        self.lineIPRDSocketAddress.setClearButtonEnabled(True)

        self.gridLayout_17.addWidget(self.lineIPRDSocketAddress, 1, 1, 1, 1)


        self.verticalLayout_6.addWidget(self.groupIPRD)


        self.verticalLayout_5.addWidget(self.groupListenerConfig)

        self.scrollArea.setWidget(self.scrollGeneral)

        self.verticalLayout_4.addWidget(self.scrollArea)

        self.tabWidget.addTab(self.tabGeneral, "")
        self.tabAPI = QWidget()
        self.tabAPI.setObjectName(u"tabAPI")
        self.verticalLayout_9 = QVBoxLayout(self.tabAPI)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.scrollArea_3 = QScrollArea(self.tabAPI)
        self.scrollArea_3.setObjectName(u"scrollArea_3")
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollAPI = QWidget()
        self.scrollAPI.setObjectName(u"scrollAPI")
        self.scrollAPI.setGeometry(QRect(0, 0, 476, 893))
        self.verticalLayout_8 = QVBoxLayout(self.scrollAPI)
        self.verticalLayout_8.setSpacing(15)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.groupAPISettings = QGroupBox(self.scrollAPI)
        self.groupAPISettings.setObjectName(u"groupAPISettings")
        self.gridLayout_7 = QGridLayout(self.groupAPISettings)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.label_9 = QLabel(self.groupAPISettings)
        self.label_9.setObjectName(u"label_9")

        self.gridLayout_7.addWidget(self.label_9, 0, 0, 1, 1)

        self.spinLocateDuration = QSpinBox(self.groupAPISettings)
        self.spinLocateDuration.setObjectName(u"spinLocateDuration")
        self.spinLocateDuration.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.spinLocateDuration.setMinimum(5)
        self.spinLocateDuration.setMaximum(30)
        self.spinLocateDuration.setSingleStep(5)
        self.spinLocateDuration.setValue(10)

        self.gridLayout_7.addWidget(self.spinLocateDuration, 0, 1, 1, 1)


        self.verticalLayout_8.addWidget(self.groupAPISettings)

        self.groupAPIAuth = QGroupBox(self.scrollAPI)
        self.groupAPIAuth.setObjectName(u"groupAPIAuth")
        self.verticalLayout_10 = QVBoxLayout(self.groupAPIAuth)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.groupAntminer = QGroupBox(self.groupAPIAuth)
        self.groupAntminer.setObjectName(u"groupAntminer")
        self.gridLayout_8 = QGridLayout(self.groupAntminer)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.label_10 = QLabel(self.groupAntminer)
        self.label_10.setObjectName(u"label_10")

        self.gridLayout_8.addWidget(self.label_10, 0, 0, 1, 1)

        self.lineAntminerPasswd = QLineEdit(self.groupAntminer)
        self.lineAntminerPasswd.setObjectName(u"lineAntminerPasswd")
        sizePolicy.setHeightForWidth(self.lineAntminerPasswd.sizePolicy().hasHeightForWidth())
        self.lineAntminerPasswd.setSizePolicy(sizePolicy)
        self.lineAntminerPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_8.addWidget(self.lineAntminerPasswd, 0, 1, 1, 1)


        self.verticalLayout_10.addWidget(self.groupAntminer)

        self.groupIceriver = QGroupBox(self.groupAPIAuth)
        self.groupIceriver.setObjectName(u"groupIceriver")
        self.gridLayout_9 = QGridLayout(self.groupIceriver)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.label_11 = QLabel(self.groupIceriver)
        self.label_11.setObjectName(u"label_11")

        self.gridLayout_9.addWidget(self.label_11, 0, 0, 1, 1)

        self.lineIceriverPasswd = QLineEdit(self.groupIceriver)
        self.lineIceriverPasswd.setObjectName(u"lineIceriverPasswd")
        sizePolicy.setHeightForWidth(self.lineIceriverPasswd.sizePolicy().hasHeightForWidth())
        self.lineIceriverPasswd.setSizePolicy(sizePolicy)
        self.lineIceriverPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_9.addWidget(self.lineIceriverPasswd, 0, 1, 1, 1)


        self.verticalLayout_10.addWidget(self.groupIceriver)

        self.groupWhatsminer = QGroupBox(self.groupAPIAuth)
        self.groupWhatsminer.setObjectName(u"groupWhatsminer")
        self.gridLayout_11 = QGridLayout(self.groupWhatsminer)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.label_12 = QLabel(self.groupWhatsminer)
        self.label_12.setObjectName(u"label_12")

        self.gridLayout_11.addWidget(self.label_12, 0, 0, 1, 1)

        self.lineWhatsminerPasswd = QLineEdit(self.groupWhatsminer)
        self.lineWhatsminerPasswd.setObjectName(u"lineWhatsminerPasswd")
        sizePolicy.setHeightForWidth(self.lineWhatsminerPasswd.sizePolicy().hasHeightForWidth())
        self.lineWhatsminerPasswd.setSizePolicy(sizePolicy)
        self.lineWhatsminerPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_11.addWidget(self.lineWhatsminerPasswd, 0, 1, 1, 1)


        self.verticalLayout_10.addWidget(self.groupWhatsminer)

        self.groupGoldshell = QGroupBox(self.groupAPIAuth)
        self.groupGoldshell.setObjectName(u"groupGoldshell")
        self.gridLayout_10 = QGridLayout(self.groupGoldshell)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.label_13 = QLabel(self.groupGoldshell)
        self.label_13.setObjectName(u"label_13")

        self.gridLayout_10.addWidget(self.label_13, 0, 0, 1, 1)

        self.lineGoldshellPasswd = QLineEdit(self.groupGoldshell)
        self.lineGoldshellPasswd.setObjectName(u"lineGoldshellPasswd")
        sizePolicy.setHeightForWidth(self.lineGoldshellPasswd.sizePolicy().hasHeightForWidth())
        self.lineGoldshellPasswd.setSizePolicy(sizePolicy)
        self.lineGoldshellPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_10.addWidget(self.lineGoldshellPasswd, 0, 1, 1, 1)


        self.verticalLayout_10.addWidget(self.groupGoldshell)

        self.groupHammer = QGroupBox(self.groupAPIAuth)
        self.groupHammer.setObjectName(u"groupHammer")
        self.groupHammer.setEnabled(False)
        self.gridLayout_13 = QGridLayout(self.groupHammer)
        self.gridLayout_13.setObjectName(u"gridLayout_13")
        self.label_14 = QLabel(self.groupHammer)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_13.addWidget(self.label_14, 0, 0, 1, 1)

        self.lineHammerPasswd = QLineEdit(self.groupHammer)
        self.lineHammerPasswd.setObjectName(u"lineHammerPasswd")
        sizePolicy.setHeightForWidth(self.lineHammerPasswd.sizePolicy().hasHeightForWidth())
        self.lineHammerPasswd.setSizePolicy(sizePolicy)
        self.lineHammerPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_13.addWidget(self.lineHammerPasswd, 0, 1, 1, 1)


        self.verticalLayout_10.addWidget(self.groupHammer)

        self.groupVolcminer = QGroupBox(self.groupAPIAuth)
        self.groupVolcminer.setObjectName(u"groupVolcminer")
        self.gridLayout_12 = QGridLayout(self.groupVolcminer)
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.lineVolcminerPasswd = QLineEdit(self.groupVolcminer)
        self.lineVolcminerPasswd.setObjectName(u"lineVolcminerPasswd")
        sizePolicy.setHeightForWidth(self.lineVolcminerPasswd.sizePolicy().hasHeightForWidth())
        self.lineVolcminerPasswd.setSizePolicy(sizePolicy)
        self.lineVolcminerPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_12.addWidget(self.lineVolcminerPasswd, 0, 1, 1, 1)

        self.label_15 = QLabel(self.groupVolcminer)
        self.label_15.setObjectName(u"label_15")

        self.gridLayout_12.addWidget(self.label_15, 0, 0, 1, 1)


        self.verticalLayout_10.addWidget(self.groupVolcminer)

        self.groupElphapex = QGroupBox(self.groupAPIAuth)
        self.groupElphapex.setObjectName(u"groupElphapex")
        self.gridLayout_14 = QGridLayout(self.groupElphapex)
        self.gridLayout_14.setObjectName(u"gridLayout_14")
        self.label_16 = QLabel(self.groupElphapex)
        self.label_16.setObjectName(u"label_16")

        self.gridLayout_14.addWidget(self.label_16, 0, 0, 1, 1)

        self.lineElphapexPasswd = QLineEdit(self.groupElphapex)
        self.lineElphapexPasswd.setObjectName(u"lineElphapexPasswd")
        sizePolicy.setHeightForWidth(self.lineElphapexPasswd.sizePolicy().hasHeightForWidth())
        self.lineElphapexPasswd.setSizePolicy(sizePolicy)
        self.lineElphapexPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_14.addWidget(self.lineElphapexPasswd, 0, 1, 1, 1)


        self.verticalLayout_10.addWidget(self.groupElphapex)

        self.groupSealminer = QGroupBox(self.groupAPIAuth)
        self.groupSealminer.setObjectName(u"groupSealminer")
        self.gridLayout_15 = QGridLayout(self.groupSealminer)
        self.gridLayout_15.setObjectName(u"gridLayout_15")
        self.label_17 = QLabel(self.groupSealminer)
        self.label_17.setObjectName(u"label_17")

        self.gridLayout_15.addWidget(self.label_17, 0, 0, 1, 1)

        self.lineSealminerPasswd = QLineEdit(self.groupSealminer)
        self.lineSealminerPasswd.setObjectName(u"lineSealminerPasswd")
        sizePolicy.setHeightForWidth(self.lineSealminerPasswd.sizePolicy().hasHeightForWidth())
        self.lineSealminerPasswd.setSizePolicy(sizePolicy)
        self.lineSealminerPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_15.addWidget(self.lineSealminerPasswd, 0, 1, 1, 1)


        self.verticalLayout_10.addWidget(self.groupSealminer)


        self.verticalLayout_8.addWidget(self.groupAPIAuth)

        self.groupAPIAuthFirmwares = QGroupBox(self.scrollAPI)
        self.groupAPIAuthFirmwares.setObjectName(u"groupAPIAuthFirmwares")
        self.verticalLayout_12 = QVBoxLayout(self.groupAPIAuthFirmwares)
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.checkUseAntminerLogin = QCheckBox(self.groupAPIAuthFirmwares)
        self.checkUseAntminerLogin.setObjectName(u"checkUseAntminerLogin")

        self.verticalLayout_12.addWidget(self.checkUseAntminerLogin)

        self.groupVnish = QGroupBox(self.groupAPIAuthFirmwares)
        self.groupVnish.setObjectName(u"groupVnish")
        self.gridLayout_16 = QGridLayout(self.groupVnish)
        self.gridLayout_16.setObjectName(u"gridLayout_16")
        self.lineVnishPasswd = QLineEdit(self.groupVnish)
        self.lineVnishPasswd.setObjectName(u"lineVnishPasswd")
        sizePolicy.setHeightForWidth(self.lineVnishPasswd.sizePolicy().hasHeightForWidth())
        self.lineVnishPasswd.setSizePolicy(sizePolicy)
        self.lineVnishPasswd.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_16.addWidget(self.lineVnishPasswd, 0, 1, 1, 1)

        self.label_18 = QLabel(self.groupVnish)
        self.label_18.setObjectName(u"label_18")

        self.gridLayout_16.addWidget(self.label_18, 0, 0, 1, 1)


        self.verticalLayout_12.addWidget(self.groupVnish)


        self.verticalLayout_8.addWidget(self.groupAPIAuthFirmwares)

        self.scrollArea_3.setWidget(self.scrollAPI)

        self.verticalLayout_9.addWidget(self.scrollArea_3)

        self.tabWidget.addTab(self.tabAPI, "")
        self.tabLog = QWidget()
        self.tabLog.setObjectName(u"tabLog")
        self.verticalLayout_7 = QVBoxLayout(self.tabLog)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.scrollArea_2 = QScrollArea(self.tabLog)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setFrameShape(QFrame.Shape.NoFrame)
        self.scrollArea_2.setFrameShadow(QFrame.Shadow.Plain)
        self.scrollArea_2.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollArea_2.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollLogs = QWidget()
        self.scrollLogs.setObjectName(u"scrollLogs")
        self.scrollLogs.setGeometry(QRect(0, 0, 478, 227))
        self.verticalLayout_11 = QVBoxLayout(self.scrollLogs)
        self.verticalLayout_11.setSpacing(15)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.groupLogSettings = QGroupBox(self.scrollLogs)
        self.groupLogSettings.setObjectName(u"groupLogSettings")
        self.groupLogSettings.setMaximumSize(QSize(16777215, 150))
        self.gridLayout_5 = QGridLayout(self.groupLogSettings)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.checkFlushOnClose = QCheckBox(self.groupLogSettings)
        self.checkFlushOnClose.setObjectName(u"checkFlushOnClose")

        self.gridLayout_5.addWidget(self.checkFlushOnClose, 0, 0, 1, 1)

        self.label_5 = QLabel(self.groupLogSettings)
        self.label_5.setObjectName(u"label_5")
        font2 = QFont()
        font2.setPointSize(10)
        self.label_5.setFont(font2)

        self.gridLayout_5.addWidget(self.label_5, 1, 0, 1, 1)

        self.comboLogLevel = QComboBox(self.groupLogSettings)
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.addItem("")
        self.comboLogLevel.setObjectName(u"comboLogLevel")
        self.comboLogLevel.setMinimumSize(QSize(180, 0))
        self.comboLogLevel.setMaximumSize(QSize(250, 16777215))

        self.gridLayout_5.addWidget(self.comboLogLevel, 1, 1, 1, 1)


        self.verticalLayout_11.addWidget(self.groupLogSettings)

        self.groupLogFile = QGroupBox(self.scrollLogs)
        self.groupLogFile.setObjectName(u"groupLogFile")
        self.groupLogFile.setMaximumSize(QSize(16777215, 150))
        self.gridLayout_6 = QGridLayout(self.groupLogFile)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.spinMaxLogSize = QSpinBox(self.groupLogFile)
        self.spinMaxLogSize.setObjectName(u"spinMaxLogSize")
        self.spinMaxLogSize.setMinimumSize(QSize(180, 0))
        self.spinMaxLogSize.setMaximumSize(QSize(250, 16777215))
        self.spinMaxLogSize.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.spinMaxLogSize.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spinMaxLogSize.setProperty(u"showGroupSeparator", True)
        self.spinMaxLogSize.setMinimum(1)
        self.spinMaxLogSize.setMaximum(4096)
        self.spinMaxLogSize.setValue(1024)

        self.gridLayout_6.addWidget(self.spinMaxLogSize, 0, 1, 1, 1)

        self.label_7 = QLabel(self.groupLogFile)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font2)

        self.gridLayout_6.addWidget(self.label_7, 0, 0, 1, 1)

        self.label_8 = QLabel(self.groupLogFile)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font2)

        self.gridLayout_6.addWidget(self.label_8, 1, 0, 1, 1)

        self.comboOnMaxLogSize = QComboBox(self.groupLogFile)
        self.comboOnMaxLogSize.addItem("")
        self.comboOnMaxLogSize.addItem("")
        self.comboOnMaxLogSize.setObjectName(u"comboOnMaxLogSize")
        self.comboOnMaxLogSize.setMinimumSize(QSize(180, 0))
        self.comboOnMaxLogSize.setMaximumSize(QSize(250, 16777215))

        self.gridLayout_6.addWidget(self.comboOnMaxLogSize, 1, 1, 1, 1)


        self.verticalLayout_11.addWidget(self.groupLogFile)

        self.scrollArea_2.setWidget(self.scrollLogs)

        self.verticalLayout_7.addWidget(self.scrollArea_2)

        self.tabWidget.addTab(self.tabLog, "")

        self.verticalLayout_3.addWidget(self.tabWidget)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.pushIPRCancelConfig = QPushButton(self.settingsView)
        self.pushIPRCancelConfig.setObjectName(u"pushIPRCancelConfig")
        self.pushIPRCancelConfig.setFont(font)

        self.gridLayout.addWidget(self.pushIPRCancelConfig, 3, 0, 1, 1)

        self.pushIPRSaveConfig = QPushButton(self.settingsView)
        self.pushIPRSaveConfig.setObjectName(u"pushIPRSaveConfig")
        self.pushIPRSaveConfig.setFont(font)

        self.gridLayout.addWidget(self.pushIPRSaveConfig, 3, 1, 1, 1)

        self.pushIPRResetConfig = QPushButton(self.settingsView)
        self.pushIPRResetConfig.setObjectName(u"pushIPRResetConfig")
        self.pushIPRResetConfig.setFont(font)

        self.gridLayout.addWidget(self.pushIPRResetConfig, 2, 0, 1, 2)


        self.verticalLayout_3.addLayout(self.gridLayout)

        self.stackedWidget.addWidget(self.settingsView)

        self.vwrapper.addWidget(self.stackedWidget)

        self.verticalSpacer = QSpacerItem(20, 18, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.vwrapper.addItem(self.verticalSpacer)

        self.listenerControls = QHBoxLayout()
        self.listenerControls.setObjectName(u"listenerControls")
        self.listenerControls.setContentsMargins(9, 9, 9, 10)
        self.pushIPRListenStart = QPushButton(self.centralwidget)
        self.pushIPRListenStart.setObjectName(u"pushIPRListenStart")
        self.pushIPRListenStart.setFont(font1)

        self.listenerControls.addWidget(self.pushIPRListenStart)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.listenerControls.addItem(self.horizontalSpacer)

        self.pushIPRListenStop = QPushButton(self.centralwidget)
        self.pushIPRListenStop.setObjectName(u"pushIPRListenStop")
        self.pushIPRListenStop.setEnabled(False)
        self.pushIPRListenStop.setFont(font1)

        self.listenerControls.addWidget(self.pushIPRListenStop)


        self.vwrapper.addLayout(self.listenerControls)


        self.verticalLayout.addLayout(self.vwrapper)

        MainWindow.setCentralWidget(self.centralwidget)
        self.iprStatusBar = QStatusBar(MainWindow)
        self.iprStatusBar.setObjectName(u"iprStatusBar")
        MainWindow.setStatusBar(self.iprStatusBar)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)
        self.comboLogLevel.setCurrentIndex(1)
        self.pushIPRListenStart.setDefault(True)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"BitCap IPReporter", None))
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Preset:", None))
        self.label_25.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.actionIPRCreatePreset.setToolTip(QCoreApplication.translate("MainWindow", u"Add new preset", None))
#endif // QT_CONFIG(tooltip)
        self.actionIPRCreatePreset.setText(QCoreApplication.translate("MainWindow", u"\uff0b", None))
#if QT_CONFIG(tooltip)
        self.actionIPRRemovePreset.setToolTip(QCoreApplication.translate("MainWindow", u"Remove preset", None))
#endif // QT_CONFIG(tooltip)
        self.actionIPRRemovePreset.setText(QCoreApplication.translate("MainWindow", u"\u2212", None))
#if QT_CONFIG(tooltip)
        self.checkAutomaticWorkerNames.setToolTip(QCoreApplication.translate("MainWindow", u"Automatically append unique worker names.\n"
"Uses last 5 of SN or MAC address.", None))
#endif // QT_CONFIG(tooltip)
        self.checkAutomaticWorkerNames.setText(QCoreApplication.translate("MainWindow", u"Set Worker", None))
        self.actionIPRSavePreset.setText(QCoreApplication.translate("MainWindow", u"Save Preset", None))
        self.actionIPRClearPreset.setText(QCoreApplication.translate("MainWindow", u"Clear Preset", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"Pool 1:", None))
        self.label_19.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"User:", None))
        self.label_20.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Password:", None))
        self.label_21.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"Pool 2:", None))
        self.label_24.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"User:", None))
        self.label_26.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"Password:", None))
        self.label_27.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Pool 3:", None))
        self.label_4.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"User:", None))
        self.label_22.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"Password:", None))
        self.label_23.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.labelIPRLogo.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Configuration", None))
        self.label.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.groupSystemTray.setTitle(QCoreApplication.translate("MainWindow", u"System Tray", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"On Window Close:", None))
        self.label_2.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.checkEnableSysTray.setToolTip(QCoreApplication.translate("MainWindow", u"Show application in system tray", None))
#endif // QT_CONFIG(tooltip)
        self.checkEnableSysTray.setText(QCoreApplication.translate("MainWindow", u"Enable System Tray Icon", None))
        self.comboOnWindowClose.setItemText(0, QCoreApplication.translate("MainWindow", u"Minimize To Tray", None))
        self.comboOnWindowClose.setItemText(1, QCoreApplication.translate("MainWindow", u"Close", None))

#if QT_CONFIG(tooltip)
        self.comboOnWindowClose.setToolTip(QCoreApplication.translate("MainWindow", u"Set behavior on window close", None))
#endif // QT_CONFIG(tooltip)
        self.groupInactiveTimer.setTitle(QCoreApplication.translate("MainWindow", u"Inactive Timer", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Inactive Timeout:", None))
        self.label_3.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.checkUseCustomTimeout.setToolTip(QCoreApplication.translate("MainWindow", u"Set custom inactive timeout", None))
#endif // QT_CONFIG(tooltip)
        self.checkUseCustomTimeout.setText(QCoreApplication.translate("MainWindow", u"Use Custom Timeout", None))
        self.spinInactiveTimeout.setSuffix(QCoreApplication.translate("MainWindow", u" Minutes", None))
        self.groupListenerConfig.setTitle(QCoreApplication.translate("MainWindow", u"Listener Configuration", None))
#if QT_CONFIG(tooltip)
        self.checkEnableListenFilter.setToolTip(QCoreApplication.translate("MainWindow", u"When enabled, only receive miner types matching the enabled listeners", None))
#endif // QT_CONFIG(tooltip)
        self.checkEnableListenFilter.setText(QCoreApplication.translate("MainWindow", u"Enable Filtering", None))
#if QT_CONFIG(tooltip)
        self.groupListeners.setToolTip(QCoreApplication.translate("MainWindow", u"Check to toggle all listeners", None))
#endif // QT_CONFIG(tooltip)
        self.groupListeners.setTitle(QCoreApplication.translate("MainWindow", u"Listeners", None))
#if QT_CONFIG(tooltip)
        self.checkListenWhatsminer.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Whatsminers", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenWhatsminer.setText(QCoreApplication.translate("MainWindow", u"Whatsminer", None))
#if QT_CONFIG(tooltip)
        self.checkListenAntminer.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Antminers", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenAntminer.setText(QCoreApplication.translate("MainWindow", u"Antminer", None))
#if QT_CONFIG(tooltip)
        self.checkListenIceRiver.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Icerivers", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenIceRiver.setText(QCoreApplication.translate("MainWindow", u"IceRiver", None))
#if QT_CONFIG(tooltip)
        self.checkListenSealminer.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Sealminers", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenSealminer.setText(QCoreApplication.translate("MainWindow", u"Sealminer", None))
#if QT_CONFIG(tooltip)
        self.checkListenVolcminer.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Volcminers", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenVolcminer.setText(QCoreApplication.translate("MainWindow", u"Volcminer", None))
#if QT_CONFIG(tooltip)
        self.checkListenElphapex.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Elphapex miners", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenElphapex.setText(QCoreApplication.translate("MainWindow", u"Elphapex", None))
#if QT_CONFIG(tooltip)
        self.checkListenGoldshell.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Goldshells", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenGoldshell.setText(QCoreApplication.translate("MainWindow", u"Goldshell", None))
#if QT_CONFIG(tooltip)
        self.checkListenHammer.setToolTip(QCoreApplication.translate("MainWindow", u"Enable listening for Hammer miners", None))
#endif // QT_CONFIG(tooltip)
        self.checkListenHammer.setText(QCoreApplication.translate("MainWindow", u"Hammer", None))
        self.groupIPRD.setTitle(QCoreApplication.translate("MainWindow", u"IPR Daemon", None))
#if QT_CONFIG(tooltip)
        self.checkEnableIPRDBackend.setToolTip(QCoreApplication.translate("MainWindow", u"Use the IPR Daemon backend instead of the built-in listener", None))
#endif // QT_CONFIG(tooltip)
        self.checkEnableIPRDBackend.setText(QCoreApplication.translate("MainWindow", u"Enable IPR Daemon backend", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Socket Address:", None))
        self.label_6.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineIPRDSocketAddress.setToolTip(QCoreApplication.translate("MainWindow", u"Socket address pointing to IPRD instance in the format of <HOST>:<PORT>", None))
#endif // QT_CONFIG(tooltip)
        self.lineIPRDSocketAddress.setPlaceholderText(QCoreApplication.translate("MainWindow", u"HOST:PORT", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabGeneral), QCoreApplication.translate("MainWindow", u"General", None))
#if QT_CONFIG(tooltip)
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.tabGeneral), QCoreApplication.translate("MainWindow", u"General Settings", None))
#endif // QT_CONFIG(tooltip)
        self.groupAPISettings.setTitle(QCoreApplication.translate("MainWindow", u"API Settings", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Locate Duration:", None))
        self.label_9.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.spinLocateDuration.setToolTip(QCoreApplication.translate("MainWindow", u"Set the blinking duration when locating.", None))
#endif // QT_CONFIG(tooltip)
        self.spinLocateDuration.setSuffix(QCoreApplication.translate("MainWindow", u" Seconds", None))
#if QT_CONFIG(tooltip)
        self.groupAPIAuth.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative authentication for APIs.", None))
#endif // QT_CONFIG(tooltip)
        self.groupAPIAuth.setTitle(QCoreApplication.translate("MainWindow", u"API Authentication", None))
        self.groupAntminer.setTitle(QCoreApplication.translate("MainWindow", u"Antminer", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_10.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineAntminerPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Antminers. Default: \"root\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupIceriver.setTitle(QCoreApplication.translate("MainWindow", u"IceRiver", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_11.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineIceriverPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for IceRiver miners. Default: \"12345678\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupWhatsminer.setTitle(QCoreApplication.translate("MainWindow", u"Whatsminer", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_12.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineWhatsminerPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Whatsminers. Default: \"admin\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupGoldshell.setTitle(QCoreApplication.translate("MainWindow", u"Goldshell", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_13.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineGoldshellPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Goldshell miners. Default: \"123456789\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupHammer.setTitle(QCoreApplication.translate("MainWindow", u"Hammer", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_14.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineHammerPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Hammer miners. Default: \"root\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupVolcminer.setTitle(QCoreApplication.translate("MainWindow", u"Volcminer", None))
#if QT_CONFIG(tooltip)
        self.lineVolcminerPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Volcminers. Default: \"ltc@dog\"", None))
#endif // QT_CONFIG(tooltip)
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_15.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.groupElphapex.setTitle(QCoreApplication.translate("MainWindow", u"Elphapex", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_16.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineElphapexPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Elphapex miners. Default: \"root\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupSealminer.setTitle(QCoreApplication.translate("MainWindow", u"Sealminer", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_17.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
#if QT_CONFIG(tooltip)
        self.lineSealminerPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Sealminers. Default: \"seal\"", None))
#endif // QT_CONFIG(tooltip)
        self.groupAPIAuthFirmwares.setTitle(QCoreApplication.translate("MainWindow", u"Firmwares", None))
#if QT_CONFIG(tooltip)
        self.checkUseAntminerLogin.setToolTip(QCoreApplication.translate("MainWindow", u"Check to use configured Antminer Login as alternative instead.", None))
#endif // QT_CONFIG(tooltip)
        self.checkUseAntminerLogin.setText(QCoreApplication.translate("MainWindow", u"Use Antminer Login", None))
        self.groupVnish.setTitle(QCoreApplication.translate("MainWindow", u"Vnish", None))
#if QT_CONFIG(tooltip)
        self.lineVnishPasswd.setToolTip(QCoreApplication.translate("MainWindow", u"Set alternative login password for Vnish firmware. Default: \"admin\"", None))
#endif // QT_CONFIG(tooltip)
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Set Alternative Password:", None))
        self.label_18.setProperty(u"StyleClass", QCoreApplication.translate("MainWindow", u"setText", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabAPI), QCoreApplication.translate("MainWindow", u"API", None))
#if QT_CONFIG(tooltip)
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.tabAPI), QCoreApplication.translate("MainWindow", u"API Settings/Miner Auth", None))
#endif // QT_CONFIG(tooltip)
        self.groupLogSettings.setTitle(QCoreApplication.translate("MainWindow", u"Log Settings", None))
        self.checkFlushOnClose.setText(QCoreApplication.translate("MainWindow", u"Flush on Close", None))
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
        self.groupLogFile.setTitle(QCoreApplication.translate("MainWindow", u"Log File", None))
#if QT_CONFIG(tooltip)
        self.spinMaxLogSize.setToolTip(QCoreApplication.translate("MainWindow", u"Set maximum log file size (Max limit 4096kb)", None))
#endif // QT_CONFIG(tooltip)
        self.spinMaxLogSize.setSuffix(QCoreApplication.translate("MainWindow", u" KB", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Maximum Log Size:", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"On Maximum Log Size:", None))
        self.comboOnMaxLogSize.setItemText(0, QCoreApplication.translate("MainWindow", u"Flush", None))
        self.comboOnMaxLogSize.setItemText(1, QCoreApplication.translate("MainWindow", u"Rotate", None))

#if QT_CONFIG(tooltip)
        self.comboOnMaxLogSize.setToolTip(QCoreApplication.translate("MainWindow", u"Choose behavior for when log file reaches set max size", None))
#endif // QT_CONFIG(tooltip)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabLog), QCoreApplication.translate("MainWindow", u"Log", None))
#if QT_CONFIG(tooltip)
        self.tabWidget.setTabToolTip(self.tabWidget.indexOf(self.tabLog), QCoreApplication.translate("MainWindow", u"Log Settings", None))
#endif // QT_CONFIG(tooltip)
        self.pushIPRCancelConfig.setText(QCoreApplication.translate("MainWindow", u"Cancel", None))
        self.pushIPRSaveConfig.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.pushIPRResetConfig.setText(QCoreApplication.translate("MainWindow", u"Reset Settings to Default", None))
        self.pushIPRListenStart.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.pushIPRListenStop.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
    # retranslateUi

