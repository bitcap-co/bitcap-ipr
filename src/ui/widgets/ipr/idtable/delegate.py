# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from PySide6.QtCore import (
    QEvent,
    QModelIndex,
    QPersistentModelIndex,
    QRect,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QHelpEvent, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolTip,
)

from .model import COL_ACTION

_ICONS = {
    COL_ACTION: ":theme/icons/rc/wrench.png",
}

_TOOLTIPS = {
    COL_ACTION: "Control miner",
}

# cap the action icons at their native size so they don't upscale to fill a
# taller row / wider cell
_ICON_MAX = QSize(15, 15)


class IPRActionDelegate(QStyledItemDelegate):
    # emitted with the action column (COL_ACTION) and source row
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
            option.rect.size().boundedTo(_ICON_MAX),
            Qt.AspectRatioMode.KeepAspectRatio,
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

    def helpEvent(
        self,
        event: QHelpEvent,
        view: QAbstractItemView,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> bool:
        if event.type() == QEvent.Type.ToolTip:
            tip = _TOOLTIPS.get(index.column())
            if tip is not None:
                QToolTip.showText(event.globalPos(), tip, view)
                return True
            # non-action cell: hide any lingering action tooltip
            QToolTip.hideText()
        return super().helpEvent(event, view, option, index)
