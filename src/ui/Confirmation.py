# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'confirmation.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_IPRConfirmation(object):
    def setupUi(self, IPRConfirmation):
        if not IPRConfirmation.objectName():
            IPRConfirmation.setObjectName(u"IPRConfirmation")
        IPRConfirmation.resize(350, 260)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(IPRConfirmation.sizePolicy().hasHeightForWidth())
        IPRConfirmation.setSizePolicy(sizePolicy)
        self.titlebarwidget = QWidget(IPRConfirmation)
        self.titlebarwidget.setObjectName(u"titlebarwidget")
        self.titlebarwidget.setGeometry(QRect(0, 0, 350, 30))
        self.verticalLayout = QVBoxLayout(self.titlebarwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_2 = QWidget(IPRConfirmation)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setGeometry(QRect(0, 30, 350, 230))
        self.gridLayout = QGridLayout(self.widget_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 0, 9, 9)
        self.lineIPField = QLineEdit(self.widget_2)
        self.lineIPField.setObjectName(u"lineIPField")
        self.lineIPField.setEnabled(True)
        font = QFont()
        font.setPointSize(12)
        self.lineIPField.setFont(font)
        self.lineIPField.setFrame(True)
        self.lineIPField.setAlignment(Qt.AlignCenter)
        self.lineIPField.setReadOnly(True)

        self.gridLayout.addWidget(self.lineIPField, 2, 0, 1, 1)

        self.label = QLabel(self.widget_2)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        self.label.setFont(font1)
        self.label.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.accept = QPushButton(self.widget_2)
        self.accept.setObjectName(u"accept")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.accept.sizePolicy().hasHeightForWidth())
        self.accept.setSizePolicy(sizePolicy1)
        font2 = QFont()
        font2.setPointSize(10)
        font2.setBold(True)
        self.accept.setFont(font2)

        self.gridLayout.addWidget(self.accept, 7, 0, 1, 1, Qt.AlignHCenter)

        self.actionOpenBrowser = QPushButton(self.widget_2)
        self.actionOpenBrowser.setObjectName(u"actionOpenBrowser")
        sizePolicy1.setHeightForWidth(self.actionOpenBrowser.sizePolicy().hasHeightForWidth())
        self.actionOpenBrowser.setSizePolicy(sizePolicy1)
        self.actionOpenBrowser.setFont(font2)

        self.gridLayout.addWidget(self.actionOpenBrowser, 4, 0, 1, 1, Qt.AlignHCenter)

        self.label_2 = QLabel(self.widget_2)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setFont(font1)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.gridLayout.addWidget(self.label_2, 5, 0, 1, 1)

        self.lineMACField = QLineEdit(self.widget_2)
        self.lineMACField.setObjectName(u"lineMACField")
        self.lineMACField.setEnabled(True)
        font3 = QFont()
        font3.setPointSize(12)
        font3.setBold(False)
        self.lineMACField.setFont(font3)
        self.lineMACField.setAlignment(Qt.AlignCenter)
        self.lineMACField.setReadOnly(True)

        self.gridLayout.addWidget(self.lineMACField, 6, 0, 1, 1)

        self.line = QFrame(self.widget_2)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Plain)
        self.line.setFrameShape(QFrame.Shape.HLine)

        self.gridLayout.addWidget(self.line, 0, 0, 1, 1)


        self.retranslateUi(IPRConfirmation)

        self.accept.setDefault(True)


        QMetaObject.connectSlotsByName(IPRConfirmation)
    # setupUi

    def retranslateUi(self, IPRConfirmation):
        IPRConfirmation.setWindowTitle(QCoreApplication.translate("IPRConfirmation", u"IPR Confirmation", None))
        self.lineIPField.setText("")
        self.label.setText(QCoreApplication.translate("IPRConfirmation", u"IP Address", None))
        self.label.setProperty(u"StyleClass", QCoreApplication.translate("IPRConfirmation", u"setText", None))
        self.accept.setText(QCoreApplication.translate("IPRConfirmation", u"OK", None))
        self.actionOpenBrowser.setText(QCoreApplication.translate("IPRConfirmation", u"Open Browser", None))
        self.label_2.setText(QCoreApplication.translate("IPRConfirmation", u"MAC Address", None))
        self.label_2.setProperty(u"StyleClass", QCoreApplication.translate("IPRConfirmation", u"setText", None))
        self.lineMACField.setText("")
    # retranslateUi

