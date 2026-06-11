# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.widgets import IPR_Titlebar


class IPRMessage(QDialog):
    """A frameless, IPR-styled message dialog.

    Mirrors the About dialog look (custom title bar, separator and body
    text) for simple prompts. The dialog sizes itself to its content: the
    body wraps at a comfortable width and the height grows with the text.

    When action_text is provided, an extra action button is shown and the
    dialog accepts when it is clicked, so callers can branch on
    exec() == QDialog.DialogCode.Accepted (e.g. open a download).

    Args:
        parent (QWidget): parent widget.
        title (str): window and title bar text.
        text (str): body text.
        action_text (str | None): label for an optional action button. When
            set, the dismiss button becomes "Close"; otherwise a single "OK"
            button is shown.
    """

    TITLE_BAR_HEIGHT = 30
    MIN_BODY_WIDTH = 300
    MAX_BODY_WIDTH = 460

    def __init__(
        self,
        parent: QWidget,
        title: str,
        text: str,
        action_text: str | None = None,
    ):
        super().__init__(parent=parent, f=Qt.WindowType.FramelessWindowHint)

        self._parent = parent
        self._title_str = title
        self._message_text = text

        self.setWindowTitle(self._title_str)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # size the dialog to fit its content and keep it non-resizable.
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.title_bar = IPR_Titlebar(self, self._title_str, ["close"])
        self.title_bar.setFixedHeight(self.TITLE_BAR_HEIGHT)
        self.title_bar.close_button.clicked.connect(self.reject)
        layout.addWidget(self.title_bar)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        layout.addWidget(self.line)

        self.text_label = QLabel(self._message_text)
        self.text_label.setWordWrap(True)
        self.text_label.setMinimumWidth(self.MIN_BODY_WIDTH)
        self.text_label.setMaximumWidth(self.MAX_BODY_WIDTH)
        self.text_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(15, 15, 15, 15)
        body_layout.addWidget(self.text_label)
        layout.addWidget(body)

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(9, 9, 9, 9)
        buttons_layout.addStretch(1)
        if action_text:
            self.actionButton = QPushButton(action_text)
            self.actionButton.setDefault(True)
            self.actionButton.clicked.connect(self.accept)
            buttons_layout.addWidget(self.actionButton)
            self.acceptButton = QPushButton("Close")
            self.acceptButton.clicked.connect(self.reject)
        else:
            self.acceptButton = QPushButton("OK")
            self.acceptButton.setDefault(True)
            self.acceptButton.clicked.connect(self.accept)
        buttons_layout.addWidget(self.acceptButton)
        layout.addWidget(buttons)
