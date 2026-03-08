# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QPushButton, QSizePolicy, QWidget)

class Ui_IPRAbout(object):
    def setupUi(self, IPRAbout):
        if not IPRAbout.objectName():
            IPRAbout.setObjectName(u"IPRAbout")
        IPRAbout.resize(450, 250)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(IPRAbout.sizePolicy().hasHeightForWidth())
        IPRAbout.setSizePolicy(sizePolicy)
        IPRAbout.setMinimumSize(QSize(450, 250))
        IPRAbout.setMaximumSize(QSize(450, 250))
        self.titleBarWidget = QWidget(IPRAbout)
        self.titleBarWidget.setObjectName(u"titleBarWidget")
        self.titleBarWidget.setGeometry(QRect(0, 0, 450, 30))
        self.horizontalLayout_3 = QHBoxLayout(self.titleBarWidget)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, -1, -1, 0)
        self.centralWidget = QWidget(IPRAbout)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setGeometry(QRect(0, 35, 450, 180))
        self.horizontalLayout_2 = QHBoxLayout(self.centralWidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 9, 9, 9)
        self.buttons = QWidget(IPRAbout)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setGeometry(QRect(0, 200, 450, 50))
        self.horizontalLayout = QHBoxLayout(self.buttons)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.acceptButton = QPushButton(self.buttons)
        self.acceptButton.setObjectName(u"acceptButton")

        self.horizontalLayout.addWidget(self.acceptButton, 0, Qt.AlignmentFlag.AlignRight)

        self.line = QFrame(IPRAbout)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(9, 30, 430, 4))
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.HLine)

        self.retranslateUi(IPRAbout)

        self.acceptButton.setDefault(True)


        QMetaObject.connectSlotsByName(IPRAbout)
    # setupUi

    def retranslateUi(self, IPRAbout):
        IPRAbout.setWindowTitle(QCoreApplication.translate("IPRAbout", u"Dialog", None))
        self.acceptButton.setText(QCoreApplication.translate("IPRAbout", u"OK", None))
    # retranslateUi

