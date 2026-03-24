from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit

from ui.Confirmation import Ui_IPRConfirmation
from ui.widgets import IPR_Titlebar


class IPRConfirmation(QDialog, Ui_IPRConfirmation):
    def __init__(self, stay_on_top: bool = False):
        super().__init__(f=Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, stay_on_top)
        self.setupUi(self)

        self.title_bar = IPR_Titlebar(self, "IP Confirmation", ["min", "close"])
        self.title_bar.minimize_button.clicked.connect(self.window().showMinimized)
        self.title_bar.close_button.clicked.connect(self.window().hide)
        title_bar_widget = self.titleBarWidget.layout()
        if title_bar_widget:
            title_bar_widget.addWidget(self.title_bar)

        self.acceptButton.clicked.connect(self.window().hide)

        self.labelIPLogo.setPixmap(QPixmap(":theme/icons/rc/wifi.png"))
        self.labelMACLogo.setPixmap(QPixmap(":theme/icons/rc/stack.png"))
        self.labelASICLogo.setPixmap(QPixmap(":theme/icons/rc/miner.png"))

        self._create_copy_action(self.lineIPField)
        self._create_copy_action(self.lineMACField)
        self._create_copy_action(self.lineASICField)

        self.actionOpenDashboard = self._create_open_action(self.lineIPField)

    def _create_copy_action(self, lineEdit: QLineEdit) -> QAction:
        copy_action = lineEdit.addAction(
            QIcon(":theme/icons/rc/copy.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        copy_action.setToolTip("Copy content")
        copy_action.triggered.connect(lambda: self._copy_text(lineEdit))
        return copy_action

    def _copy_text(self, lineEdit: QLineEdit):
        lineEdit.selectAll()
        text = lineEdit.text()
        if lineEdit.objectName() == "lineIPField":
            text = f"http://{lineEdit.text()}"
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(text.strip(), mode=cb.Mode.Clipboard)

    def _create_open_action(self, lineEdit: QLineEdit) -> QAction:
        open_action = lineEdit.addAction(
            QIcon(":theme/icons/rc/dashboard.png"),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        open_action.setToolTip("Open Dashboard")
        return open_action
