# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Value checklist popup for a single ID-table column.

Opened from the header funnel. Lists the column's distinct values (grouped
case-insensitively upstream) with a "(Select All)" toggle. ``applied`` carries
the chosen labels; ``cleared`` removes the column filter entirely. The window
uses ``Qt.Popup`` so it dismisses on an outside click like a native dropdown.
"""

from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


class ColumnFilterPopup(QFrame):
    applied = Signal(list)  # list[str] of checked value labels
    cleared = Signal()  # remove the column filter (show all)

    def __init__(
        self,
        title: str,
        values: list[str],
        checked: set[str] | None,
        parent=None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._guard = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        heading = QLabel(f"Filter: {title}")
        heading.setStyleSheet("font-weight: bold;")
        layout.addWidget(heading)

        self._list = QListWidget(self)
        self._list.setMinimumWidth(200)
        self._list.setMaximumHeight(260)
        layout.addWidget(self._list)

        self._select_all = QListWidgetItem("(Select All)")
        self._select_all.setFlags(
            Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
        )
        self._list.addItem(self._select_all)

        # ``checked is None`` means no active filter -> everything is shown.
        self._value_items: list[QListWidgetItem] = []
        for value in values:
            item = QListWidgetItem(value)
            item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            is_on = checked is None or value.casefold() in checked
            item.setCheckState(
                Qt.CheckState.Checked if is_on else Qt.CheckState.Unchecked
            )
            self._list.addItem(item)
            self._value_items.append(item)

        self._sync_select_all()
        self._list.itemChanged.connect(self._on_item_changed)

        buttons = QHBoxLayout()
        self._clear_btn = QPushButton("Clear Filter", self)
        self._clear_btn.clicked.connect(self._on_clear)
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.close)
        self._apply_btn = QPushButton("Apply", self)
        self._apply_btn.setDefault(True)
        self._apply_btn.clicked.connect(self._on_apply)
        buttons.addWidget(self._clear_btn)
        buttons.addStretch(1)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(self._apply_btn)
        layout.addLayout(buttons)

        self._update_apply_enabled()

    def show_at(self, global_pos: QPoint) -> None:
        self.adjustSize()
        self.move(global_pos)
        self.show()

    def _checked_labels(self) -> list[str]:
        return [
            item.text()
            for item in self._value_items
            if item.checkState() == Qt.CheckState.Checked
        ]

    def _sync_select_all(self) -> None:
        total = len(self._value_items)
        on = sum(
            item.checkState() == Qt.CheckState.Checked for item in self._value_items
        )
        if on == 0:
            state = Qt.CheckState.Unchecked
        elif on == total:
            state = Qt.CheckState.Checked
        else:
            state = Qt.CheckState.PartiallyChecked
        self._guard = True
        self._select_all.setCheckState(state)
        self._guard = False

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if self._guard:
            return
        if item is self._select_all:
            target = (
                Qt.CheckState.Unchecked
                if item.checkState() == Qt.CheckState.Unchecked
                else Qt.CheckState.Checked
            )
            self._guard = True
            for value_item in self._value_items:
                value_item.setCheckState(target)
            self._select_all.setCheckState(target)
            self._guard = False
        else:
            self._sync_select_all()
        self._update_apply_enabled()

    def _update_apply_enabled(self) -> None:
        # applying an empty selection would hide every row; require at least one
        self._apply_btn.setEnabled(bool(self._checked_labels()))

    def _on_apply(self) -> None:
        self.applied.emit(self._checked_labels())
        self.close()

    def _on_clear(self) -> None:
        self.cleared.emit()
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def hideEvent(self, event: QEvent) -> None:
        # single-use popup: dismissing it (Apply/Cancel/Clear/outside-click, all
        # of which hide the Qt.Popup) also disposes of it.
        super().hideEvent(event)
        self.deleteLater()
