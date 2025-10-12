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
