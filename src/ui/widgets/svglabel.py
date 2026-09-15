# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import override

from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel, QWidget


class SvgLabel(QLabel):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._renderer: QSvgRenderer

    @override
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        if self._renderer:
            self._renderer.render(painter)
        return super().paintEvent(event)

    def setSvgFile(self, filename: str):
        self._renderer = QSvgRenderer(filename)
        self.resize(self._renderer.defaultSize())
        length = max(self.sizeHint().width(), self.sizeHint().height())
        self.setFixedSize(length, length)
