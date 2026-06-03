# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Delegate that paints the action-column icons (refresh / locate).

Replaces the old ``setCellWidget(row, col, QLabel(...))`` approach. A delegate
paints once per cell instead of allocating a QLabel per row, centers the icon
in the narrow 15px columns, and emits a signal carrying the *source* row when
clicked.
"""

from PySide6.QtCore import QEvent, QModelIndex, QPersistentModelIndex, QRect, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem

from .model import COL_LOCATE, COL_REFRESH

_ICONS = {
    COL_REFRESH: ":theme/icons/rc/refresh.png",
    COL_LOCATE: ":theme/icons/rc/flash.png",
}


class IPRActionDelegate(QStyledItemDelegate):
    # emitted with the action column (COL_REFRESH/COL_LOCATE) and source row
    action_clicked = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pixmaps = {col: QPixmap(path) for col, path in _ICONS.items()}

    def paint(
        self,
        painter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        pixmap = self._pixmaps.get(index.column())
        if pixmap is None or pixmap.isNull():
            return super().paint(painter, option, index)
        size = pixmap.size().scaled(
            option.rect.size(), Qt.AspectRatioMode.KeepAspectRatio
        )
        target = QRect(0, 0, size.width(), size.height())
        target.moveCenter(option.rect.center())
        painter.drawPixmap(target, pixmap)

    def editorEvent(
        self,
        event: QEvent,
        model,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        col = index.column()
        if (
            event.type() == QEvent.Type.MouseButtonRelease
            and col in self._pixmaps
            and event.button() == Qt.MouseButton.LeftButton
        ):
            # index here belongs to the proxy; map to source for the row id
            proxy = index.model()
            source_row = proxy.mapToSource(index).row()
            self.action_clicked.emit(col, source_row)
            return True
        return super().editorEvent(event, model, option, index)
