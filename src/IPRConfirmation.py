from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from ui.TitleBar import TitleBar
from ui.GUI import Ui_IPRConfirmation


class IPRConfirmation(QWidget, Ui_IPRConfirmation):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )

        # title bar
        self.title_bar = TitleBar(self, "IP Confirmation", ['min', 'close'])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.window().close)
        title_bar_widget = self.titlebarwidget.layout()
        title_bar_widget.addWidget(self.title_bar)
