# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Single-miner control popup for the ID-table action column.

Opened from the action-column wrench glyph. Lists the per-miner control
actions as a vertical button stack; clicking one emits ``action_selected``
with the action key and dismisses the popup. The window uses ``Qt.Popup`` so
it closes on an outside click like a native menu.

An icon sits beside a label when its ``ACTIONS`` entry carries an icon path
(icons are optional for now — leave the path ``None`` to render text only).
"""

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QGuiApplication, QIcon, QKeyEvent
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout

# (key, label, icon resource path | None) — the order here is the display order
ACTIONS: list[tuple[str, str, str | None]] = [
    ("refresh", "Refresh Miner", ":theme/icons/rc/refresh.png"),
    ("locate", "Locate Miner", ":theme/icons/rc/flash.png"),
    ("start", "Start Miner", ":theme/icons/rc/start.png"),
    ("stop", "Stop Miner", ":theme/icons/rc/pause.png"),
    ("restart", "Restart Miner", ":theme/icons/rc/restart.png"),
    ("reboot", "Reboot Miner", ":theme/icons/rc/reboot.png"),
]

_ICON_SIZE = QSize(15, 15)


class MinerControlPopup(QFrame):
    action_selected = Signal(str)  # the chosen action key (see ACTIONS)

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("minerControlPopup")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        for key, label, icon_path in ACTIONS:
            # flat QPushButtons fill the popup width and left-align like a menu
            button = QPushButton(label, self)
            button.setFlat(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if icon_path:
                button.setIcon(QIcon(icon_path))
                button.setIconSize(_ICON_SIZE)
            button.clicked.connect(lambda _checked=False, k=key: self._on_action(k))
            layout.addWidget(button)

    def _on_action(self, key: str) -> None:
        self.action_selected.emit(key)
        self.close()

    def show_at(self, global_pos: QPoint) -> None:
        self.adjustSize()
        self.move(self._clamp_to_bounds(global_pos))
        self.show()

    def _clamp_to_bounds(self, global_pos: QPoint) -> QPoint:
        """Keep the popup inside the parent window (and the screen).

        The action cell anchors the popup at its bottom-left; for rows near the
        bottom edge it would otherwise spill off-screen, so shift it back in.
        """
        size = self.sizeHint()
        x, y = global_pos.x(), global_pos.y()

        rect: QRect | None = None
        parent = self.parentWidget()
        if parent is not None:
            win = parent.window()
            rect = QRect(win.mapToGlobal(QPoint(0, 0)), win.size())
        screen = QGuiApplication.screenAt(global_pos)
        if screen is not None:
            avail = screen.availableGeometry()
            rect = avail if rect is None else rect.intersected(avail)
        if rect is None:
            return global_pos

        if x + size.width() > rect.right():
            x = rect.right() - size.width()
        if y + size.height() > rect.bottom():
            y = rect.bottom() - size.height()
        x = max(x, rect.left())
        y = max(y, rect.top())
        return QPoint(x, y)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def hideEvent(self, event: QEvent) -> None:
        # single-use popup: any dismissal (selection/Esc/outside-click) disposes
        # of it, matching ColumnFilterPopup's lifecycle
        super().hideEvent(event)
        self.deleteLater()
