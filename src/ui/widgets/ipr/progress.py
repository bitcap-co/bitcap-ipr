# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .titlebar import IPRTitlebar


class IPRProgress(QDialog):
    """A frameless, IPR-styled progress dialog.

    Shows a body message, a progress bar and a cancel button. Emits the
    cancelled signal when the user dismisses it so callers can stop the
    underlying work (e.g. a download).

    Args:
        parent (QWidget): parent widget.
        title (str): window and title bar text.
        text (str): body text.
        cancellable (bool): when False, hide the cancel/close controls for
            operations that must not be interrupted (e.g. installing).

    Signals:
        cancelled (): emitted when the user cancels or closes the dialog.
    """

    cancelled = Signal()

    TITLE_BAR_HEIGHT = 30
    BAR_WIDTH = 340

    def __init__(
        self, parent: QWidget, title: str, text: str, cancellable: bool = True
    ):
        super().__init__(parent=parent, f=Qt.WindowType.FramelessWindowHint)

        self._parent = parent
        self._title_str = title
        self._cancellable = cancellable

        self.setWindowTitle(self._title_str)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        title_buttons = ["close"] if cancellable else []
        self.title_bar = IPRTitlebar(self, self._title_str, title_buttons)
        self.title_bar.setFixedHeight(self.TITLE_BAR_HEIGHT)
        if cancellable:
            self.title_bar.close_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.title_bar)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        layout.addWidget(self.line)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(15, 15, 15, 15)
        body_layout.setSpacing(10)

        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        body_layout.addWidget(self.text_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(self.BAR_WIDTH)
        # start indeterminate until the first progress update reports a total.
        self.progress_bar.setRange(0, 0)
        body_layout.addWidget(self.progress_bar)
        layout.addWidget(body)

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(9, 9, 9, 9)
        buttons_layout.addStretch(1)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self._on_cancel)
        self.cancelButton.setVisible(self._cancellable)
        buttons_layout.addWidget(self.cancelButton)
        layout.addWidget(buttons)

    def _on_cancel(self) -> None:
        self.cancelled.emit()
        self.reject()

    def set_progress(self, received: int, total: int) -> None:
        """Update the progress bar and label from a download update.

        Args:
            received (int): bytes downloaded so far.
            total (int): total bytes expected, or 0 if unknown.
        """
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(received)
            self.text_label.setText(
                f"Downloading update... "
                f"({received / 1_048_576:.1f} MB / {total / 1_048_576:.1f} MB)"
            )
        else:
            self.text_label.setText(
                f"Downloading update... ({received / 1_048_576:.1f} MB)"
            )
