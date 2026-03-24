from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel


class SvgLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._renderer: QSvgRenderer

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._renderer:
            self._renderer.render(painter)
        return super().paintEvent(event)

    def setSvgFile(self, filename: str):
        self._renderer = QSvgRenderer(filename)
        self.resize(self._renderer.defaultSize())
        length = max(self.sizeHint().width(), self.sizeHint().height())
        self.setFixedSize(length, length)
