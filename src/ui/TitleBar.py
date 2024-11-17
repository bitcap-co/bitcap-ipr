import os
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QToolButton,
    QWidget
)

basedir = os.path.dirname(__file__)
icons = os.path.join(basedir, "../resources/icons/app")

class TitleBar(QWidget):
    def __init__(self, parent: QWidget, title: str, hint: list = ['min', 'max', 'close']):
        super().__init__(parent)
        self.__initObj(parent, title, hint)
        self.__initUI()

    def __initObj(self, parent, title, hint):
        self.initial_pos = None

        self._title = QLabel()
        self._iconButton = QToolButton()
        self._closeButton = QToolButton()
        self._closeButton.setText("🗙")
        self._minimizeButton = QToolButton()
        self._minimizeButton.setText("🗕")
        self._maximizeButton = QToolButton()
        self._maximizeButton.setText("🗖")

        self._button_dict = {'min': self._minimizeButton, 'max': self._maximizeButton, 'close': self._closeButton}

        self._title_str = title
        self._hint = hint
        self._parent = parent
        self._window = self._parent.window()

    def __initUI(self):
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(5, 0, 0, 0)
        title_bar_layout.setSpacing(10)

        icon = QIcon()
        icon.addPixmap(QPixmap(os.path.join(icons, "BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png")), QIcon.Mode.Disabled, QIcon.State.On)
        self._iconButton.setIcon(icon)
        self._iconButton.setEnabled(False)
        title_bar_layout.addWidget(self._iconButton)

        # title
        self._title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._title.setText(self._title_str)
        self._title.setStyleSheet("""QLabel {
                                    color: #FFFFFF;
                                    font-weight: bold;
                                    font-size: 14px;
                                  }"""
        )
        title_bar_layout.addWidget(self._title)

        # buttons
        for x in self._hint:
            if x in self._button_dict:
                self._button_dict[x].setFocusPolicy(Qt.FocusPolicy.NoFocus)
                title_bar_layout.addWidget(self._button_dict[x])

    def changeEvent(self, event):
        super().changeEvent(event)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.initial_pos = event.position().toPoint()
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        if self.initial_pos is not None:
            delta = event.position().toPoint() - self.initial_pos
            self._window.move(
                self._window.x() + delta.x(),
                self._window.y() + delta.y(),
            )
        super().mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.initial_pos = None
        super().mouseReleaseEvent(event)
        event.accept()
