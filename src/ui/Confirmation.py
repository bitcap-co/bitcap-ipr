# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'confirmation.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_IPRConfirmation(object):
    def setupUi(self, IPRConfirmation):
        if not IPRConfirmation.objectName():
            IPRConfirmation.setObjectName(u"IPRConfirmation")
        IPRConfirmation.resize(320, 360)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(IPRConfirmation.sizePolicy().hasHeightForWidth())
        IPRConfirmation.setSizePolicy(sizePolicy)
        IPRConfirmation.setMinimumSize(QSize(320, 360))
        IPRConfirmation.setMaximumSize(QSize(320, 360))
        self.verticalLayout = QVBoxLayout(IPRConfirmation)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.titleBarWidget = QWidget(IPRConfirmation)
        self.titleBarWidget.setObjectName(u"titleBarWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.titleBarWidget.sizePolicy().hasHeightForWidth())
        self.titleBarWidget.setSizePolicy(sizePolicy1)
        self.titleBarWidget.setMinimumSize(QSize(320, 30))
        self.titleBarWidget.setMaximumSize(QSize(320, 30))
        self.horizontalLayout = QHBoxLayout(self.titleBarWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 9, 9, 0)

        self.verticalLayout.addWidget(self.titleBarWidget)

        self.line = QFrame(IPRConfirmation)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.HLine)

        self.verticalLayout.addWidget(self.line)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 6, 9, 9)
        self.ipAddr = QWidget(IPRConfirmation)
        self.ipAddr.setObjectName(u"ipAddr")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.ipAddr.sizePolicy().hasHeightForWidth())
        self.ipAddr.setSizePolicy(sizePolicy2)
        self.horizontalLayout_2 = QHBoxLayout(self.ipAddr)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.labelIPLogo = QLabel(self.ipAddr)
        self.labelIPLogo.setObjectName(u"labelIPLogo")
        sizePolicy.setHeightForWidth(self.labelIPLogo.sizePolicy().hasHeightForWidth())
        self.labelIPLogo.setSizePolicy(sizePolicy)
        self.labelIPLogo.setMinimumSize(QSize(8, 0))

        self.horizontalLayout_2.addWidget(self.labelIPLogo)

        self.lineIPField = QLineEdit(self.ipAddr)
        self.lineIPField.setObjectName(u"lineIPField")
        sizePolicy.setHeightForWidth(self.lineIPField.sizePolicy().hasHeightForWidth())
        self.lineIPField.setSizePolicy(sizePolicy)
        self.lineIPField.setMinimumSize(QSize(200, 0))
        font = QFont()
        font.setPointSize(11)
        self.lineIPField.setFont(font)
        self.lineIPField.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.lineIPField.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.lineIPField.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.lineIPField.setAcceptDrops(False)
        self.lineIPField.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineIPField.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineIPField)


        self.gridLayout.addWidget(self.ipAddr, 3, 0, 1, 1)

        self.macAddr = QWidget(IPRConfirmation)
        self.macAddr.setObjectName(u"macAddr")
        sizePolicy2.setHeightForWidth(self.macAddr.sizePolicy().hasHeightForWidth())
        self.macAddr.setSizePolicy(sizePolicy2)
        self.horizontalLayout_3 = QHBoxLayout(self.macAddr)
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.labelMACLogo = QLabel(self.macAddr)
        self.labelMACLogo.setObjectName(u"labelMACLogo")
        sizePolicy.setHeightForWidth(self.labelMACLogo.sizePolicy().hasHeightForWidth())
        self.labelMACLogo.setSizePolicy(sizePolicy)
        self.labelMACLogo.setMinimumSize(QSize(8, 0))

        self.horizontalLayout_3.addWidget(self.labelMACLogo)

        self.lineMACField = QLineEdit(self.macAddr)
        self.lineMACField.setObjectName(u"lineMACField")
        sizePolicy.setHeightForWidth(self.lineMACField.sizePolicy().hasHeightForWidth())
        self.lineMACField.setSizePolicy(sizePolicy)
        self.lineMACField.setMinimumSize(QSize(200, 0))
        self.lineMACField.setFont(font)
        self.lineMACField.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.lineMACField.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.lineMACField.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.lineMACField.setAcceptDrops(False)
        self.lineMACField.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineMACField.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineMACField)


        self.gridLayout.addWidget(self.macAddr, 5, 0, 1, 1)

        self.label = QLabel(IPRConfirmation)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.label.setFont(font1)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label, 2, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.label_4 = QLabel(IPRConfirmation)
        self.label_4.setObjectName(u"label_4")
        sizePolicy1.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy1)
        self.label_4.setFont(font1)
        self.label_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.recvAt = QWidget(IPRConfirmation)
        self.recvAt.setObjectName(u"recvAt")
        sizePolicy2.setHeightForWidth(self.recvAt.sizePolicy().hasHeightForWidth())
        self.recvAt.setSizePolicy(sizePolicy2)
        self.horizontalLayout_5 = QHBoxLayout(self.recvAt)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.labelRecvAtLogo = QLabel(self.recvAt)
        self.labelRecvAtLogo.setObjectName(u"labelRecvAtLogo")
        sizePolicy.setHeightForWidth(self.labelRecvAtLogo.sizePolicy().hasHeightForWidth())
        self.labelRecvAtLogo.setSizePolicy(sizePolicy)
        self.labelRecvAtLogo.setMinimumSize(QSize(8, 0))

        self.horizontalLayout_5.addWidget(self.labelRecvAtLogo)

        self.lineRecvAtField = QLineEdit(self.recvAt)
        self.lineRecvAtField.setObjectName(u"lineRecvAtField")
        sizePolicy.setHeightForWidth(self.lineRecvAtField.sizePolicy().hasHeightForWidth())
        self.lineRecvAtField.setSizePolicy(sizePolicy)
        self.lineRecvAtField.setMinimumSize(QSize(200, 0))
        self.lineRecvAtField.setFont(font)
        self.lineRecvAtField.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.lineRecvAtField.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.lineRecvAtField.setAcceptDrops(False)
        self.lineRecvAtField.setReadOnly(True)

        self.horizontalLayout_5.addWidget(self.lineRecvAtField)


        self.gridLayout.addWidget(self.recvAt, 1, 0, 1, 1)

        self.label_3 = QLabel(IPRConfirmation)
        self.label_3.setObjectName(u"label_3")
        sizePolicy1.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy1)
        self.label_3.setFont(font1)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_3, 6, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.label_2 = QLabel(IPRConfirmation)
        self.label_2.setObjectName(u"label_2")
        sizePolicy1.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy1)
        self.label_2.setFont(font1)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_2, 4, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.minerType = QWidget(IPRConfirmation)
        self.minerType.setObjectName(u"minerType")
        sizePolicy2.setHeightForWidth(self.minerType.sizePolicy().hasHeightForWidth())
        self.minerType.setSizePolicy(sizePolicy2)
        self.horizontalLayout_4 = QHBoxLayout(self.minerType)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.labelASICLogo = QLabel(self.minerType)
        self.labelASICLogo.setObjectName(u"labelASICLogo")
        sizePolicy.setHeightForWidth(self.labelASICLogo.sizePolicy().hasHeightForWidth())
        self.labelASICLogo.setSizePolicy(sizePolicy)
        self.labelASICLogo.setMinimumSize(QSize(8, 0))

        self.horizontalLayout_4.addWidget(self.labelASICLogo)

        self.lineASICField = QLineEdit(self.minerType)
        self.lineASICField.setObjectName(u"lineASICField")
        sizePolicy.setHeightForWidth(self.lineASICField.sizePolicy().hasHeightForWidth())
        self.lineASICField.setSizePolicy(sizePolicy)
        self.lineASICField.setMinimumSize(QSize(200, 0))
        self.lineASICField.setFont(font)
        self.lineASICField.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.lineASICField.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.lineASICField.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.lineASICField.setAcceptDrops(False)
        self.lineASICField.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineASICField.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.lineASICField)


        self.gridLayout.addWidget(self.minerType, 7, 0, 1, 1)

        self.acceptButton = QPushButton(IPRConfirmation)
        self.acceptButton.setObjectName(u"acceptButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.acceptButton.sizePolicy().hasHeightForWidth())
        self.acceptButton.setSizePolicy(sizePolicy3)
        font2 = QFont()
        font2.setBold(True)
        self.acceptButton.setFont(font2)

        self.gridLayout.addWidget(self.acceptButton, 8, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)


        self.verticalLayout.addLayout(self.gridLayout)


        self.retranslateUi(IPRConfirmation)

        self.acceptButton.setDefault(True)


        QMetaObject.connectSlotsByName(IPRConfirmation)
    # setupUi

    def retranslateUi(self, IPRConfirmation):
        IPRConfirmation.setWindowTitle(QCoreApplication.translate("IPRConfirmation", u"IPR Confirmation", None))
        self.labelIPLogo.setText("")
        self.labelMACLogo.setText("")
        self.label.setText(QCoreApplication.translate("IPRConfirmation", u"IP Address", None))
        self.label.setProperty(u"StyleClass", QCoreApplication.translate("IPRConfirmation", u"setText", None))
        self.label_4.setText(QCoreApplication.translate("IPRConfirmation", u"Received At", None))
        self.label_3.setText(QCoreApplication.translate("IPRConfirmation", u"Miner Type", None))
        self.label_3.setProperty(u"StyleClass", QCoreApplication.translate("IPRConfirmation", u"setText", None))
        self.label_2.setText(QCoreApplication.translate("IPRConfirmation", u"Mac Address", None))
        self.label_2.setProperty(u"StyleClass", QCoreApplication.translate("IPRConfirmation", u"setText", None))
        self.labelASICLogo.setText("")
        self.acceptButton.setText(QCoreApplication.translate("IPRConfirmation", u"OK", None))
    # retranslateUi

