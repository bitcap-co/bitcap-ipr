# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'confirmation.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
        IPRConfirmation.resize(320, 320)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(IPRConfirmation.sizePolicy().hasHeightForWidth())
        IPRConfirmation.setSizePolicy(sizePolicy)
        IPRConfirmation.setMinimumSize(QSize(320, 320))
        IPRConfirmation.setMaximumSize(QSize(320, 320))
        self.titlebarwidget = QWidget(IPRConfirmation)
        self.titlebarwidget.setObjectName(u"titlebarwidget")
        self.titlebarwidget.setGeometry(QRect(0, 0, 320, 30))
        self.verticalLayout = QVBoxLayout(self.titlebarwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_2 = QWidget(IPRConfirmation)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setGeometry(QRect(0, 30, 320, 290))
        self.widget_2.setMinimumSize(QSize(320, 290))
        self.widget_2.setMaximumSize(QSize(320, 290))
        self.gridLayout = QGridLayout(self.widget_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 0, 9, 9)
        self.line = QFrame(self.widget_2)
        self.line.setObjectName(u"line")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy1)
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.HLine)

        self.gridLayout.addWidget(self.line, 0, 0, 1, 1)

        self.label_3 = QLabel(self.widget_2)
        self.label_3.setObjectName(u"label_3")
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_3.setFont(font)
        self.label_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_3, 6, 0, 1, 1)

        self.hwrapper = QWidget(self.widget_2)
        self.hwrapper.setObjectName(u"hwrapper")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.hwrapper.sizePolicy().hasHeightForWidth())
        self.hwrapper.setSizePolicy(sizePolicy2)
        self.horizontalLayout = QHBoxLayout(self.hwrapper)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.ipLogo = QLabel(self.hwrapper)
        self.ipLogo.setObjectName(u"ipLogo")
        sizePolicy2.setHeightForWidth(self.ipLogo.sizePolicy().hasHeightForWidth())
        self.ipLogo.setSizePolicy(sizePolicy2)

        self.horizontalLayout.addWidget(self.ipLogo)

        self.lineIPField = QLineEdit(self.hwrapper)
        self.lineIPField.setObjectName(u"lineIPField")
        self.lineIPField.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.lineIPField.sizePolicy().hasHeightForWidth())
        self.lineIPField.setSizePolicy(sizePolicy2)
        self.lineIPField.setMinimumSize(QSize(200, 0))
        font1 = QFont()
        font1.setPointSize(12)
        self.lineIPField.setFont(font1)
        self.lineIPField.setFrame(True)
        self.lineIPField.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineIPField.setReadOnly(True)

        self.horizontalLayout.addWidget(self.lineIPField, 0, Qt.AlignmentFlag.AlignHCenter)


        self.gridLayout.addWidget(self.hwrapper, 2, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.label = QLabel(self.widget_2)
        self.label.setObjectName(u"label")
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.hwrapper_3 = QWidget(self.widget_2)
        self.hwrapper_3.setObjectName(u"hwrapper_3")
        sizePolicy2.setHeightForWidth(self.hwrapper_3.sizePolicy().hasHeightForWidth())
        self.hwrapper_3.setSizePolicy(sizePolicy2)
        self.horizontalLayout_3 = QHBoxLayout(self.hwrapper_3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.typeLogo = QLabel(self.hwrapper_3)
        self.typeLogo.setObjectName(u"typeLogo")
        sizePolicy2.setHeightForWidth(self.typeLogo.sizePolicy().hasHeightForWidth())
        self.typeLogo.setSizePolicy(sizePolicy2)

        self.horizontalLayout_3.addWidget(self.typeLogo)

        self.lineASICField = QLineEdit(self.hwrapper_3)
        self.lineASICField.setObjectName(u"lineASICField")
        self.lineASICField.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.lineASICField.sizePolicy().hasHeightForWidth())
        self.lineASICField.setSizePolicy(sizePolicy2)
        self.lineASICField.setMinimumSize(QSize(200, 0))
        font2 = QFont()
        font2.setPointSize(12)
        font2.setBold(False)
        self.lineASICField.setFont(font2)
        self.lineASICField.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineASICField.setReadOnly(True)

        self.horizontalLayout_3.addWidget(self.lineASICField)


        self.gridLayout.addWidget(self.hwrapper_3, 7, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.hwrapper_2 = QWidget(self.widget_2)
        self.hwrapper_2.setObjectName(u"hwrapper_2")
        sizePolicy2.setHeightForWidth(self.hwrapper_2.sizePolicy().hasHeightForWidth())
        self.hwrapper_2.setSizePolicy(sizePolicy2)
        self.horizontalLayout_2 = QHBoxLayout(self.hwrapper_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.macLogo = QLabel(self.hwrapper_2)
        self.macLogo.setObjectName(u"macLogo")
        sizePolicy2.setHeightForWidth(self.macLogo.sizePolicy().hasHeightForWidth())
        self.macLogo.setSizePolicy(sizePolicy2)

        self.horizontalLayout_2.addWidget(self.macLogo)

        self.lineMACField = QLineEdit(self.hwrapper_2)
        self.lineMACField.setObjectName(u"lineMACField")
        self.lineMACField.setEnabled(True)
        sizePolicy2.setHeightForWidth(self.lineMACField.sizePolicy().hasHeightForWidth())
        self.lineMACField.setSizePolicy(sizePolicy2)
        self.lineMACField.setMinimumSize(QSize(200, 0))
        self.lineMACField.setFont(font2)
        self.lineMACField.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lineMACField.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.lineMACField)


        self.gridLayout.addWidget(self.hwrapper_2, 5, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.label_2 = QLabel(self.widget_2)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setFont(font)
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout.addWidget(self.label_2, 4, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        self.accept = QPushButton(self.widget_2)
        self.accept.setObjectName(u"accept")
        sizePolicy2.setHeightForWidth(self.accept.sizePolicy().hasHeightForWidth())
        self.accept.setSizePolicy(sizePolicy2)
        font3 = QFont()
        font3.setPointSize(10)
        font3.setBold(True)
        self.accept.setFont(font3)

        self.gridLayout.addWidget(self.accept, 8, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)


        self.retranslateUi(IPRConfirmation)

        self.accept.setDefault(True)


        QMetaObject.connectSlotsByName(IPRConfirmation)
    # setupUi

    def retranslateUi(self, IPRConfirmation):
        IPRConfirmation.setWindowTitle(QCoreApplication.translate("IPRConfirmation", u"IPR Confirmation", None))
        self.label_3.setText(QCoreApplication.translate("IPRConfirmation", u"Miner Type", None))
        self.label_3.setProperty(u"StyleClass", QCoreApplication.translate("IPRConfirmation", u"setText", None))
        self.ipLogo.setText("")
        self.lineIPField.setText("")
        self.label.setText(QCoreApplication.translate("IPRConfirmation", u"IP Address", None))
        self.label.setProperty(u"StyleClass", QCoreApplication.translate("IPRConfirmation", u"setText", None))
        self.typeLogo.setText("")
        self.lineASICField.setText("")
        self.macLogo.setText("")
        self.lineMACField.setText("")
        self.label_2.setText(QCoreApplication.translate("IPRConfirmation", u"MAC Address", None))
        self.label_2.setProperty(u"StyleClass", QCoreApplication.translate("IPRConfirmation", u"setText", None))
        self.accept.setText(QCoreApplication.translate("IPRConfirmation", u"OK", None))
    # retranslateUi

