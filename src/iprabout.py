from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QPushButton,
    QLabel,
)
from ui.About import Ui_IPRAbout
from ui.widgets.titlebar import TitleBar
from ui.widgets.svglabel import SvgLabel
from utils import CURR_PLATFORM


class IPRAbout(QDialog, Ui_IPRAbout):
    def __init__(self, parent: QWidget, title: str, text: str):
        super().__init__(f=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)
        self.__initObj(parent, title, text)
        self.__initUI()

    def __initObj(self, parent, title, text):
        self._logo = SvgLabel()
        self._logo.setSvgFile(":rc/img/scalable/BitCapIPRCenterLogo.svg")
        self._textLabel = QLabel()
        self._acceptButton = QPushButton()
        self._acceptButton.setText("OK")
        self._acceptButton.setDefault(True)

        self._title_str = title
        self._about_text = text
        self._parent = parent
        self._window = self._parent.window()

    def __initUI(self):
        self.setWindowTitle(self._title_str)
        # title bar
        if CURR_PLATFORM == "darwin":
            self.title_bar = TitleBar(self, self._title_str, ["close"], style="mac")
        else:
            self.title_bar = TitleBar(self, self._title_str, ["close"])
        self.title_bar._minimizeButton.clicked.connect(self.window().showMinimized)
        self.title_bar._closeButton.clicked.connect(self.window().close)
        title_bar_widget = self.titlebarwidget.layout()
        title_bar_widget.addWidget(self.title_bar)

        # central widget
        central_widget = self.centralwidget.layout()
        self._logo.setFixedSize(QSize(150, 150))
        self._logo.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        central_widget.addWidget(self._logo)
        self._textLabel.setWordWrap(True)
        self._textLabel.setMargin(10)
        self._textLabel.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._textLabel.setText(self._about_text)
        central_widget.addWidget(self._textLabel)

        buttons_widget = self.buttons.layout()
        buttons_widget.addWidget(self._acceptButton)
