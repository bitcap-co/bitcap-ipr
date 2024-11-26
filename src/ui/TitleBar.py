import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

basedir = os.path.dirname(__file__)
icons = os.path.join(basedir, "../resources/icons/app")


class TitleBar(QWidget):
    def __init__(
        self, parent: QWidget, title: str, hint: list = ["min", "max", "close"], style: str = "win"
    ):
        super().__init__(parent)
        self.__size = 12
        self.__initObj(parent, title, hint, style)
        self.__initUI()

    def __initObj(self, parent, title, hint, style):
        self.initial_pos = None

        self._title = QLabel()
        self._iconButton = QToolButton()
        self._closeButton = QToolButton()
        self._minimizeButton = QToolButton()
        self._maximizeButton = QToolButton()
        if style == "win":
            self._closeButton.setText("🗙")
            self._minimizeButton.setText("🗕")
            self._maximizeButton.setText("🗖")
        elif style == "mac":
            self._border_width = self.__size // 20
            self._border_radius = self.__size // 2
            self._macBtnStyle = ''
            self._colors = {
                "close": '#DD0000',
                "min": '#AA8800',
                "max": '#008800',
            }

        self._button_dict = {
            "close": self._closeButton,
            "min": self._minimizeButton,
            "max": self._maximizeButton,
        }

        self._title_str = title
        self._hint = hint
        self._style = style
        self._parent = parent
        self._window = self._parent.window()

    def __initUI(self):
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(5, 0, 0, 0)
        title_bar_layout.setSpacing(10)

        if self._style == "mac":
            for x in self._hint:
                if x in self._button_dict:
                    self._button_dict[x].setFixedSize(self.__size, self.__size)
                    self.__setMacStyle(self._button_dict[x], self._colors[x])
                    title_bar_layout.addWidget(self._button_dict[x])

        if self._style == "win":
            icon = QIcon()
            icon.addPixmap(
                QPixmap(
                    os.path.join(
                        icons, "BitCapLngLogo_IPR_Full_ORG_BLK-02_Square.png"
                    )
                ),
                QIcon.Mode.Disabled,
                QIcon.State.On,
            )
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
                                  }""")
        title_bar_layout.addWidget(self._title)

        if self._style == "win":
            for x in self._hint:
                if x in self._button_dict:
                    self._button_dict[x].setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    title_bar_layout.addWidget(self._button_dict[x])

    def __setMacStyle(self, btn, color):
        border_color = QColor(color)
        border_color_name = border_color.name()
        background_color_name = border_color.lighter().name()

        btn.setStyleSheet(f"""QToolButton {{
                            background-color: {background_color_name};
                            border: {self._border_width} solid {border_color_name};
                            border-radius: {self._border_radius};
                          }}""")

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
