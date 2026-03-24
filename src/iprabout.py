from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QWidget,
)

from ui.About import Ui_IPRAbout
from ui.widgets import IPR_Titlebar, SvgLabel


class IPRAbout(QDialog, Ui_IPRAbout):
    def __init__(self, parent: QWidget, title: str, text: str):
        super().__init__(f=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)

        self._parent = parent
        self._window = self._parent.window()
        self._title_str = title
        self._about_text = text

        self.setWindowTitle(self._title_str)

        self.title_bar = IPR_Titlebar(self, self._title_str, ["close"])
        self.title_bar.close_button.clicked.connect(self.window().close)
        title_bar_widget = self.titleBarWidget.layout()
        if title_bar_widget:
            title_bar_widget.addWidget(self.title_bar)

        self.acceptButton.clicked.connect(self.window().close)

        central_widget = self.centralWidget.layout()
        if central_widget:
            self.logo = SvgLabel()
            self.logo.setSvgFile(":rc/img/scalable/BitCapIPRCenterLogo.svg")
            self.logo.setFixedSize(QSize(150, 150))
            self.logo.setAlignment(
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
            )
            central_widget.addWidget(self.logo)

            self.text_label = QLabel()
            self.text_label.setWordWrap(True)
            self.text_label.setMargin(10)
            self.text_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.text_label.setText(self._about_text)
            central_widget.addWidget(self.text_label)
