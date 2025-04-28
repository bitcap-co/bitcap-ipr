# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_IPRAbout(object):
    def setupUi(self, IPRAbout):
        if not IPRAbout.objectName():
            IPRAbout.setObjectName(u"IPRAbout")
        IPRAbout.resize(450, 250)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(IPRAbout.sizePolicy().hasHeightForWidth())
        IPRAbout.setSizePolicy(sizePolicy)
        self.titlebarwidget = QWidget(IPRAbout)
        self.titlebarwidget.setObjectName(u"titlebarwidget")
        self.titlebarwidget.setGeometry(QRect(0, 0, 450, 30))
        self.verticalLayout = QVBoxLayout(self.titlebarwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.centralwidget = QWidget(IPRAbout)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setGeometry(QRect(0, 35, 450, 180))
        self.horizontalLayout_2 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 9, 9, 9)
        self.buttons = QWidget(IPRAbout)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setGeometry(QRect(0, 200, 450, 50))
        self.horizontalLayout = QHBoxLayout(self.buttons)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.line = QFrame(IPRAbout)
        self.line.setObjectName(u"line")
        self.line.setGeometry(QRect(9, 30, 430, 4))
        self.line.setFrameShadow(QFrame.Plain)
        self.line.setFrameShape(QFrame.Shape.HLine)

        self.retranslateUi(IPRAbout)

        QMetaObject.connectSlotsByName(IPRAbout)
    # setupUi

    def retranslateUi(self, IPRAbout):
        IPRAbout.setWindowTitle(QCoreApplication.translate("IPRAbout", u"Dialog", None))
    # retranslateUi

