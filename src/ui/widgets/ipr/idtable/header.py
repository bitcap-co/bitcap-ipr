# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Excel-style filter header for the ID table.

Paints a funnel icon on columns flagged ``filterable`` and tints it to the
theme accent when a value filter is active. Clicking the funnel emits
``filter_clicked`` so the window can pop up the value checklist; clicking
anywhere else on the header falls through to the base class, preserving the
native left-click column-select and left-drag multi-column select. Only the
funnel-hotspot press is swallowed so it doesn't also select the column.
"""

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QHeaderView

# funnel icon box and its inset from the section's right edge (px). The inset
# keeps the hotspot clear of the ~5px section-resize grip at the border.
_GLYPH = 12
_MARGIN = 6

# funnel tint colours: muted when idle, theme accent when a filter is active
_COLOR_IDLE = QColor(150, 150, 150)
_COLOR_ACTIVE = QColor(0x92, 0xBE, 0xFF)


class FilterHeaderView(QHeaderView):
    filter_clicked = Signal(int)  # logical (== view) column index

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._filterable: set[int] = set()
        self._active: set[int] = set()
        # logical index recorded when a left-press lands on a funnel hotspot,
        # so the matching release opens the filter popup (see mousePressEvent).
        self._press_logical: int | None = None
        # Clickable so QTableView's native "select whole column on header press"
        # and left-drag multi-column select work. Only the funnel-hotspot press
        # is swallowed (mousePressEvent) so it doesn't also select the column.
        self.setSectionsClickable(True)
        # pre-tint the white funnel icon once for the idle / active-filter states
        base = QPixmap(":theme/icons/rc/funnel.png")
        self._idle_icon = self._tint(base, _COLOR_IDLE)
        self._active_icon = self._tint(base, _COLOR_ACTIVE)

    def set_filterable_columns(self, columns: set[int]) -> None:
        self._filterable = set(columns)
        self.viewport().update()

    def set_active_columns(self, columns: set[int]) -> None:
        self._active = set(columns)
        self.viewport().update()

    def filter_anchor(self, logical_index: int) -> QPoint:
        """Global point just below the funnel, for positioning the popup."""
        rect = self._section_rect(logical_index)
        return self.mapToGlobal(QPoint(rect.left(), rect.bottom()))

    def _section_rect(self, logical_index: int) -> QRect:
        x = self.sectionViewportPosition(logical_index)
        return QRect(x, 0, self.sectionSize(logical_index), self.height())

    def _glyph_rect(self, section_rect: QRect) -> QRect:
        x = section_rect.right() - _MARGIN - _GLYPH
        y = section_rect.center().y() - _GLYPH // 2
        return QRect(x, y, _GLYPH, _GLYPH)

    @staticmethod
    def _tint(pixmap: QPixmap, color: QColor) -> QPixmap:
        """Recolour a transparent white glyph to ``color``, preserving its alpha."""
        if pixmap.isNull():
            return pixmap
        tinted = QPixmap(pixmap.size())
        tinted.fill(Qt.GlobalColor.transparent)
        painter = QPainter(tinted)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(tinted.rect(), color)
        painter.end()
        return tinted

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int) -> None:
        super().paintSection(painter, rect, logical_index)
        if logical_index not in self._filterable:
            return
        icon = self._active_icon if logical_index in self._active else self._idle_icon
        if icon.isNull():
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(self._glyph_rect(rect), icon)
        painter.restore()

    def _filter_hotspot_at(self, point: QPoint) -> int | None:
        """Logical index of the funnel hotspot under ``point``, else ``None``."""
        logical = self.logicalIndexAt(point)
        if logical not in self._filterable:
            return None
        # pad the glyph box left/top/bottom for an easier target; the right
        # edge stays inset so the section-resize grip remains reachable.
        hotspot = self._glyph_rect(self._section_rect(logical)).adjusted(-3, -4, 0, 4)
        return logical if hotspot.contains(point) else None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        point = event.position().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            logical = self._filter_hotspot_at(point)
            if logical is not None:
                # swallow the press so native column selection doesn't start;
                # the funnel popup opens on the matching release.
                self._press_logical = logical
                return
        self._press_logical = None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        pressed = self._press_logical
        self._press_logical = None
        if pressed is not None:
            point = event.position().toPoint()
            if self._filter_hotspot_at(point) == pressed:
                self.filter_clicked.emit(pressed)
            return
        super().mouseReleaseEvent(event)
