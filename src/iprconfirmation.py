from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

from ui.Confirmation import Ui_IPRConfirmation
from ui.widgets.ipr import IPR_Titlebar
from utils import CURR_PLATFORM


class IPRConfirmation(QWidget, Ui_IPRConfirmation):
    def __init__(self):
        super().__init__(f=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)

        # title bar
        if CURR_PLATFORM == "darwin":
            self.title_bar = IPR_Titlebar(
                self, "IP Confirmation", ["close", "min"], style="mac"
            )
        else:
            self.title_bar = IPR_Titlebar(self, "IP Confirmation", ["min", "close"])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.window().hide)
        titlebarwidget = self.titlebarwidget.layout()
        if titlebarwidget:
            titlebarwidget.addWidget(self.title_bar)
        self.ipLogo.setPixmap(QPixmap(":theme/icons/rc/wifi.png"))
        self.macLogo.setPixmap(QPixmap(":theme/icons/rc/stack.png"))
        self.typeLogo.setPixmap(QPixmap(":theme/icons/rc/miner.png"))

        self.lineIPField.actionCopy = self.create_copy_text_action(self.lineIPField)
        self.lineMACField.actionCopy = self.create_copy_text_action(self.lineMACField)
        self.lineASICField.actionCopy = self.create_copy_text_action(self.lineASICField)

        self.lineIPField.actionDashboard = self.create_dashboard_action(
            self.lineIPField
        )

    def create_copy_text_action(self, line: QLineEdit) -> QAction:
        copy_action = line.addAction(
            QIcon(":theme/icons/rc/copy.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        copy_action.setToolTip("Copy content")
        copy_action.triggered.connect(lambda: self.copy_text(line))
        return copy_action

    def create_dashboard_action(self, line: QLineEdit) -> QAction:
        dashboard_action = line.addAction(
            QIcon(":theme/icons/rc/dashboard.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        dashboard_action.setToolTip("Open Dashboard")
        return dashboard_action

    def copy_text(self, line: QLineEdit):
        line.selectAll()
        text = line.text()
        if line.objectName() == "lineIPField":
            text = f"http://{line.text()}"
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(text.strip(), mode=cb.Mode.Clipboard)
