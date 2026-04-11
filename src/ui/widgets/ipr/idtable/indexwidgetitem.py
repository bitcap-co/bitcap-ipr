# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QTableWidgetItem


class IPRIndexWidgetItem(QTableWidgetItem):
    def __init__(self, value: int):
        super().__init__()
        self.setData(Qt.ItemDataRole.UserRole, value)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if isinstance(other, IPRIndexWidgetItem):
            return self.data(Qt.ItemDataRole.UserRole) < other.data(
                Qt.ItemDataRole.UserRole
            )
        return super().__lt__(other)
