from socket import inet_aton

from PySide6.QtGui import Qt
from PySide6.QtWidgets import QTableWidgetItem


class IPRIPWidgetItem(QTableWidgetItem):
    def __init__(self, value: str):
        super().__init__()
        self.setData(Qt.ItemDataRole.UserRole, inet_aton(value))
        self.setText(value)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        if isinstance(other, IPRIPWidgetItem):
            return self.data(Qt.ItemDataRole.UserRole) < other.data(
                Qt.ItemDataRole.UserRole
            )
        return super().__lt__(other)
