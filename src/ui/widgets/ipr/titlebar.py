from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QToolButton,
    QWidget,
)

import ui.resources  # noqa: F401
from utils import CURR_PLATFORM


class IPR_Titlebar(QWidget):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        button_hints: list[str] = ["min", "max", "close"],
    ):
        super().__init__(parent)
        self._parent = parent
        self._window = self._parent.window()
        self._title_str = title
        self._button_hints = button_hints
        self._bar_style = CURR_PLATFORM

        self._init_titlebar()
        self._init_ui()

    def _init_titlebar(self) -> None:
        self._set_pos = False
        self._pos = None

        self.title_label = QLabel()
        self.icon_button = QToolButton()
        self.close_button = QToolButton()
        self.minimize_button = QToolButton()
        self.maximize_button = QToolButton()

        self._buttons = {
            "close": self.close_button,
            "min": self.minimize_button,
            "max": self.maximize_button,
        }

    def _init_ui(self) -> None:
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(5, 0, 0, 0)
        title_bar_layout.setSpacing(10)

        match self._bar_style:
            case "darwin":
                btn_size = 14
                btn_colors = {
                    "close": "#DD0000",
                    "min": "#AA8800",
                    "max": "#008800",
                }
                for x in self._button_hints:
                    if x in self._buttons:
                        self._buttons[x].setFixedSize(btn_size, btn_size)
                        border_color = QColor(btn_colors[x])
                        border_color_name = border_color.name()
                        bkg_color_name = border_color.lighter().name()
                        self._buttons[x].setStyleSheet(f"""QToolButton {{
                                                            background-color: {bkg_color_name};
                                                            border: {btn_size // 20} solid {border_color_name};
                                                            border-radius: {btn_size // 2};
                                                        }}""")
                        title_bar_layout.addWidget(self._buttons[x])
            case _:
                icon = QIcon()
                icon.addPixmap(
                    QPixmap(":rc/img/BitCapIPR_BLK-02_Square.png"),
                    QIcon.Mode.Disabled,
                    QIcon.State.On,
                )
                self.icon_button.setIcon(icon)
                self.icon_button.setEnabled(False)
                title_bar_layout.addWidget(self.icon_button)

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.title_label.setText(self._title_str)
        self.title_label.setStyleSheet("""QLabel {
                                            color: #FFFFFF;
                                            font-weight: bold;
                                            font-size: 14px;
                                        }""")
        title_bar_layout.addWidget(self.title_label)

        if self._bar_style != "darwin":
            self.close_button.setText("🗙")
            self.minimize_button.setText("🗕")
            self.maximize_button.setText("🗖")

            for x in self._button_hints:
                if x in self._buttons:
                    self._buttons[x].setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    title_bar_layout.addWidget(self._buttons[x])

    def changeEvent(self, event):
        super().changeEvent(event)
        event.accept()

    def enterEvent(self, event):
        if self._bar_style == "darwin":
            for x in self._buttons:
                self._buttons[x].setIcon(QIcon(f":rc/titlebar/macos/{x}.png"))
        event.accept()

    def leaveEvent(self, event):
        if self._bar_style == "darwin":
            for x in self._buttons:
                self._buttons[x].setIcon(QIcon())
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._window.windowHandle().startSystemMove():
                self._set_pos = True
                self._pos = event.position().toPoint()
        return event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._set_pos:
            if self._pos is not None:
                offset = event.position().toPoint() - self._pos
                self._window.move(
                    self._window.x() + offset.x(), self._window.y() + offset.y()
                )
        return event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._set_pos = False
            self._pos = None
        return event.accept()
