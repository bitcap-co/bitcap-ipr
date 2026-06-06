# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.About import Ui_IPRAbout
from ui.widgets import IPR_Titlebar, SvgLabel


class IPRMessage(QDialog, Ui_IPRAbout):
    """A frameless, IPR-styled message dialog.

    Mirrors the About dialog look (custom title bar, center logo and body
    text) for simple prompts. When action_text is provided, an extra action
    button is shown and the dialog accepts when it is clicked, so callers can
    branch on exec() == QDialog.DialogCode.Accepted (e.g. open a download).

    Args:
        parent (QWidget): parent widget.
        title (str): window and title bar text.
        text (str): body text.
        action_text (str | None): label for an optional action button. When
            set, the dismiss button becomes "Close"; otherwise a single "OK"
            button is shown.
    """

    def __init__(
        self,
        parent: QWidget,
        title: str,
        text: str,
        action_text: str | None = None,
    ):
        super().__init__(f=Qt.WindowType.FramelessWindowHint)
        self.setupUi(self)

        self._parent = parent
        self._title_str = title
        self._message_text = text

        self.setWindowTitle(self._title_str)

        self.title_bar = IPR_Titlebar(self, self._title_str, ["close"])
        self.title_bar.close_button.clicked.connect(self.reject)
        title_bar_widget = self.titleBarWidget.layout()
        if title_bar_widget:
            title_bar_widget.addWidget(self.title_bar)

        if action_text:
            self.acceptButton.setText("Close")
            self.acceptButton.setDefault(False)
            self.acceptButton.clicked.connect(self.reject)
            self.actionButton = QPushButton(action_text)
            self.actionButton.setDefault(True)
            self.actionButton.clicked.connect(self.accept)
            buttons_layout = self.buttons.layout()
            if buttons_layout:
                buttons_layout.insertWidget(
                    0, self.actionButton, 0, Qt.AlignmentFlag.AlignRight
                )
        else:
            self.acceptButton.clicked.connect(self.accept)

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
            self.text_label.setText(self._message_text)
            central_widget.addWidget(self.text_label)
