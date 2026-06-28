# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
    QWidget,
)


class IPRPresetSelector(QWidget):
    """An editable combo box paired with add/remove buttons for managing a
    named list of presets (pool configs, IPRD socket addresses, ...).

    Exposes the underlying ``combo``, ``add_button`` and ``remove_button`` so
    callers wire their own slots, mirroring the other IPR custom widgets. The
    ``create_requested`` and ``remove_requested`` signals are convenience
    aliases for the button clicks.
    """

    create_requested = Signal()
    remove_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        tooltip: str = "",
        add_tooltip: str = "Add new preset",
        remove_tooltip: str = "Remove preset",
        combo_max_width: int = 225,
    ):
        super().__init__(parent)
        self._init_ui(tooltip, add_tooltip, remove_tooltip, combo_max_width)

    def _init_ui(
        self,
        tooltip: str,
        add_tooltip: str,
        remove_tooltip: str,
        combo_max_width: int,
    ) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.combo = QComboBox(self)
        size_policy = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed
        )
        self.combo.setSizePolicy(size_policy)
        self.combo.setMinimumSize(QSize(110, 25))
        self.combo.setMaximumSize(QSize(combo_max_width, 25))
        self.combo.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        if tooltip:
            self.combo.setToolTip(tooltip)
        layout.addWidget(self.combo)

        bold = QFont()
        bold.setBold(True)

        self.add_button = self._make_tool_button("＋", add_tooltip, bold)
        layout.addWidget(self.add_button)

        self.remove_button = self._make_tool_button("−", remove_tooltip, bold)
        layout.addWidget(self.remove_button)

        self.add_button.clicked.connect(self.create_requested)
        self.remove_button.clicked.connect(self.remove_requested)

    def _make_tool_button(
        self, text: str, tooltip: str, font: QFont
    ) -> QToolButton:
        button = QToolButton(self)
        button.setMinimumSize(QSize(25, 22))
        button.setMaximumSize(QSize(25, 22))
        button.setFont(font)
        button.setToolTip(tooltip)
        button.setText(text)
        return button
