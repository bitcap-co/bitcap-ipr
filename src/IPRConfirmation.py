import logging
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from ui.widgets.TitleBar import TitleBar
from ui.GUI import Ui_IPRConfirmation
from util import curr_platform

logger = logging.getLogger(__name__)


class IPRConfirmation(QWidget, Ui_IPRConfirmation):
    def __init__(self):
        logger.info(" start IPRConfirmation() init.")
        super().__init__(flags=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)

        # title bar
        if curr_platform == "darwin":
            self.title_bar = TitleBar(self, "IP Confirmation", ['close', 'min'], style="mac")
        else:
            self.title_bar = TitleBar(self, "IP Confirmation", ['min', 'close'])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.window().hide)
        title_bar_widget = self.titlebarwidget.layout()
        title_bar_widget.addWidget(self.title_bar)
