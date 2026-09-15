# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import override

from PySide6.QtCore import QEvent, QPoint, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from utils import CURR_PLATFORM


class IPRTitlebar(QWidget):
    def __init__(
        self, parent: QWidget, title: str, button_hints: list[str] | None = None
    ):
        super().__init__(parent)
        self._parent: QWidget = parent
        self._window: QWidget = self._parent.window()
        self._title_str: str = title
        if not button_hints:
            button_hints = ["min", "max", "close"]
        self._button_hints: list[str] = button_hints
        self._bar_style: str = CURR_PLATFORM

        self._rc_path: str = ":rc/titlebar/"
        if self._bar_style == "darwin":
            self._rc_path += "macos/"

        self._init_titlebar()
        self._init_ui()

    def _init_titlebar(self) -> None:
        self._set_pos: bool = False
        self._pos: QPoint | None = None

        self.title_label: QLabel = QLabel()
        self.icon_button: QToolButton = QToolButton()
        self.close_button: QToolButton = QToolButton()
        self.close_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.close_button.setIconSize(QSize(16, 16))
        self.close_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.minimize_button: QToolButton = QToolButton()
        self.minimize_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.minimize_button.setIconSize(QSize(16, 16))
        self.minimize_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.maximize_button: QToolButton = QToolButton()
        self.maximize_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.maximize_button.setIconSize(QSize(16, 16))
        self.maximize_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        self._buttons: dict[str, QToolButton] = {
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
                btn_size = 15
                btn_colors = {
                    "close": "#DD0000",
                    "min": "#AA8800",
                    "max": "#008800",
                }
                # buttons are internally in darwin order.
                # Other OSes (Windows, Linux), we follow hint order.
                for x in self._buttons:
                    if x in self._button_hints:
                        self._buttons[x].setFixedSize(btn_size, btn_size)
                        border_color = QColor(btn_colors[x])
                        border_color_name = border_color.name()
                        bkg_color_name = border_color.lighter().name()
                        self._buttons[x].setStyleSheet(f"""QToolButton {{
                                                            padding: 1px;
                                                            margin: 0px;
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
            self.close_button.setIcon(QIcon(":rc/titlebar/close.png"))
            self.minimize_button.setIcon(QIcon(":rc/titlebar/min.png"))
            self.maximize_button.setIcon(QIcon(":rc/titlebar/max.png"))

            for x in self._button_hints:
                if x in self._buttons:
                    self._buttons[x].setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    title_bar_layout.addWidget(self._buttons[x])

    def toggle_maximize(self) -> None:
        """Toggle the window between maximized and its normal size."""
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def sync_maximize_button(self) -> None:
        """Swap the maximize/restore glyph to match the window state."""
        self.maximize_button.setIcon(
            QIcon(
                self._rc_path + "restore.png"
                if self._window.isMaximized()
                else self._rc_path + "max.png"
            )
        )

    @override
    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        event.accept()

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        # double-clicking the bar maximizes/restores, like a native title bar
        if event.button() == Qt.MouseButton.LeftButton and "max" in self._button_hints:
            self.toggle_maximize()
        return event.accept()

    @override
    def enterEvent(self, event: QEvent) -> None:
        if self._bar_style == "darwin":
            # redraw icons on hover for macOS
            self.close_button.setIcon(QIcon(f"{self._rc_path}close.png"))
            self.minimize_button.setIcon(QIcon(f"{self._rc_path}min.png"))
            self.sync_maximize_button()
        event.accept()

    @override
    def leaveEvent(self, event: QEvent) -> None:
        if self._bar_style == "darwin":
            for x in self._buttons:
                self._buttons[x].setIcon(QIcon())
        event.accept()

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and not self._window.windowHandle().startSystemMove()
        ):
            self._set_pos = True
            self._pos = event.position().toPoint()
        return event.accept()

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._set_pos and self._pos is not None:
            offset = event.position().toPoint() - self._pos
            self._window.move(
                self._window.x() + offset.x(), self._window.y() + offset.y()
            )
        return event.accept()

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._set_pos = False
            self._pos = None
        return event.accept()
