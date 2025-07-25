from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QColor,
    QMouseEvent
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
    QLabel,
    QToolButton,
)
import ui.resources  # noqa: F401


class IPR_Titlebar(QWidget):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        hint: list = ["min", "max", "close"],
        style: str = "win",
    ):
        super().__init__(parent)
        self.__initObj(parent, title, hint, style)
        self.__initUI()

    def __initObj(self, parent, title, hint, style):
        self.set_pos = False
        self.pos = None

        self._title = QLabel()
        self._iconButton = QToolButton()
        self._closeButton = QToolButton()
        self._minimizeButton = QToolButton()
        self._maximizeButton = QToolButton()

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

        # mac buttons
        if self._style == "mac":
            self._button_size = 14
            self._border_width = self._button_size // 20
            self._border_radius = self._button_size // 2
            self._colors = {
                "close": "#DD0000",
                "min": "#AA8800",
                "max": "#008800",
            }
            for x in self._hint:
                if x in self._button_dict:
                    self._button_dict[x].setFixedSize(
                        self._button_size, self._button_size
                    )
                    self.setMacButtonStyle(self._button_dict[x], self._colors[x])
                    title_bar_layout.addWidget(self._button_dict[x])

        if self._style == "win":
            icon = QIcon()
            icon.addPixmap(
                QPixmap(":rc/img/BitCapIPR_BLK-02_Square.png"),
                QIcon.Mode.Disabled,
                QIcon.State.On,
            )
            self._iconButton.setIcon(icon)
            self._iconButton.setEnabled(False)
            title_bar_layout.addWidget(self._iconButton)

        # title
        self._title.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._title.setText(self._title_str)
        self._title.setStyleSheet("""QLabel {
                                    color: #FFFFFF;
                                    font-weight: bold;
                                    font-size: 14px;
                                  }""")
        title_bar_layout.addWidget(self._title)

        # win buttons
        if self._style == "win":
            self._closeButton.setText("🗙")
            self._minimizeButton.setText("🗕")
            self._maximizeButton.setText("🗖")
            for x in self._hint:
                if x in self._button_dict:
                    self._button_dict[x].setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    title_bar_layout.addWidget(self._button_dict[x])

    def setMacButtonStyle(self, btn, color):
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

    def enterEvent(self, event):
        if self._style == "mac":
            for x in self._button_dict:
                self._button_dict[x].setIcon(QIcon(f":rc/titlebar/macos/{x}.png"))
        event.accept()

    def leaveEvent(self, event):
        if self._style == "mac":
            for x in self._button_dict:
                self._button_dict[x].setIcon(QIcon())
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._window.windowHandle().startSystemMove():
                self.set_pos = True
                self.pos = event.position().toPoint()
        return event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.set_pos:
            if self.pos is not None:
                offset = event.position().toPoint() - self.pos
                self._window.move(
                    self._window.x() + offset.x(),
                    self._window.y() + offset.y()
                )
        return event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_pos = False
            self.pos = None
        return event.accept()
