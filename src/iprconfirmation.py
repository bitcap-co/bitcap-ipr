from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap

from ui.Confirmation import Ui_IPRConfirmation
from ui.widgets.titlebar import TitleBar
from utils import CURR_PLATFORM


class IPRConfirmation(QWidget, Ui_IPRConfirmation):
    def __init__(self):
        super().__init__(f=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)

        # title bar
        if CURR_PLATFORM == "darwin":
            self.title_bar = TitleBar(
                self, "IP Confirmation", ["close", "min"], style="mac"
            )
        else:
            self.title_bar = TitleBar(self, "IP Confirmation", ["min", "close"])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.window().hide)
        title_bar_widget = self.titlebarwidget.layout()
        title_bar_widget.addWidget(self.title_bar)

        self.ipLogo.setPixmap(
            QPixmap(":theme/icons/rc/wifi.png")
        )

        self.macLogo.setPixmap(
            QPixmap(":theme/icons/rc/stack.png")
        )
