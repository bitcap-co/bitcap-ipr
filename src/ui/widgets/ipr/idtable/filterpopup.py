# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Value checklist popup for a single ID-table column.

Opened from the header funnel. Lists the column's distinct values (grouped
case-insensitively upstream) with a "(Select All)" toggle. ``applied`` carries
the chosen labels; ``cleared`` removes the column filter entirely. The window
uses ``Qt.Popup`` so it dismisses on an outside click like a native dropdown.

For longer value lists a search box appears to narrow the visible entries;
searching only hides rows (checked-but-hidden values stay in the result), and
"(Select All)" then acts on whatever is currently visible.
"""

from PySide6.QtCore import QEvent, QPoint, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from .model import normalize_value

# show the search box once a column has at least this many distinct values
_SEARCH_THRESHOLD = 9


class ColumnFilterPopup(QFrame):
    applied = Signal(list)  # list[str] of checked value labels
    cleared = Signal()  # remove the column filter (show all)

    def __init__(
        self,
        title: str,
        values: list[tuple[str, int]],
        checked: set[str] | None,
        parent=None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("columnFilterPopup")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._guard = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        heading = QLabel(f"Filter: {title}")
        heading.setObjectName("filterPopupTitle")
        layout.addWidget(heading)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Search…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)
        self._search.setVisible(len(values) >= _SEARCH_THRESHOLD)
        layout.addWidget(self._search)

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
        # The raw value lives in UserRole (used for matching/applying) while the
        # visible text carries the row count, e.g. "S19J (23)".
        self._value_items: list[QListWidgetItem] = []
        for value, count in values:
            item = QListWidgetItem(f"{value} ({count})")
            item.setData(Qt.ItemDataRole.UserRole, value)
            item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            is_on = checked is None or normalize_value(value) in checked
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
        if self._search.isVisible():
            self._search.setFocus()

    def _checked_labels(self) -> list[str]:
        # every checked value (raw label, not the "(count)" display text),
        # including any hidden by the current search
        return [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self._value_items
            if item.checkState() == Qt.CheckState.Checked
        ]

    def _visible_value_items(self) -> list[QListWidgetItem]:
        return [item for item in self._value_items if not item.isHidden()]

    def _sync_select_all(self) -> None:
        # "(Select All)" reflects the currently visible (searched) items
        visible = self._visible_value_items()
        on = sum(
            item.checkState() == Qt.CheckState.Checked for item in visible
        )
        if not visible or on == 0:
            state = Qt.CheckState.Unchecked
        elif on == len(visible):
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
            for value_item in self._visible_value_items():
                value_item.setCheckState(target)
            self._select_all.setCheckState(target)
            self._guard = False
        else:
            self._sync_select_all()
        self._update_apply_enabled()

    def _on_search(self, text: str) -> None:
        # match the raw value so the "(count)" suffix doesn't affect searching
        needle = text.strip().casefold()
        for item in self._value_items:
            label = item.data(Qt.ItemDataRole.UserRole)
            item.setHidden(bool(needle) and needle not in label.casefold())
        self._sync_select_all()

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
