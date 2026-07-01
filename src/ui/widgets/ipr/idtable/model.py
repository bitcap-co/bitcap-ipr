# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from collections import Counter
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import (
    QAbstractTableModel,
    QDateTime,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtNetwork import QHostAddress

from mod.apiv2.data import MinerData

# action columns (icon-only, no underlying MinerData field)
COL_REFRESH = 0
COL_LOCATE = 1
# first data column / default sort column
COL_RECV_AT = 2

# custom role used by the proxy for type-aware sorting (epoch int, ip int, ...)
IPR_SORT_ROLE = Qt.ItemDataRole.UserRole + 1


class Column(BaseModel):
    """Describes one display column backed by a ``MinerData`` field."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    header: str
    field: str  # MinerData attribute name
    editable: bool = False
    # optional: value used for sorting instead of the display string
    sort_key: Callable[[MinerData], Any] | None = None
    # optional: hover hint shown via Qt.ItemDataRole.ToolTipRole
    tooltip: str | None = None
    # low-cardinality columns get an Excel-style header filter dropdown
    filterable: bool = False


def _ip_sort_key(m: MinerData) -> int:
    if not m.ip:
        return -1
    return QHostAddress(m.ip).toIPv4Address()


# index in this list == column index - 2 (action columns occupy 0 and 1)
COLUMNS: list[Column] = [
    Column(header="RECV AT", field="recv_at", sort_key=lambda m: m.recv_at or 0),
    Column(
        header="IP",
        field="ip",
        sort_key=_ip_sort_key,
        tooltip="Double-click to open in browser",
    ),
    Column(header="MAC", field="mac"),
    Column(header="TYPE", field="type", filterable=True),
    Column(header="SUBTYPE", field="subtype", filterable=True),
    Column(
        header="SERIAL",
        field="serial",
        editable=True,
        tooltip="Double-click to edit",
    ),
    Column(header="ALGORITHM", field="algorithm", filterable=True),
    Column(header="HOSTNAME", field="hostname", filterable=True),
    Column(header="STRATUM URL", field="stratum_url", filterable=True),
    Column(header="USERNAME", field="username", filterable=True),
    Column(header="WORKER NAME", field="worker_name"),
    Column(header="FIRMWARE", field="firmware", filterable=True),
    Column(header="FW VERSION", field="fw_version", filterable=True),
    Column(header="PLATFORM", field="platform", filterable=True),
]

# full header row including the two action columns
HEADERS = ["", ""] + [c.header for c in COLUMNS]
ACTION_COLUMN_COUNT = 2
COLUMN_COUNT = len(HEADERS)

# view column indices that expose a header filter dropdown
FILTERABLE_COLUMNS: set[int] = {
    i + ACTION_COLUMN_COUNT for i, c in enumerate(COLUMNS) if c.filterable
}


def _column_for(section: int) -> Column | None:
    """Map a view column index to its ``Column`` spec (None for action cols)."""
    if section < ACTION_COLUMN_COUNT:
        return None
    return COLUMNS[section - ACTION_COLUMN_COUNT]


class IPRTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[MinerData] = []

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        return 0 if parent.isValid() else COLUMN_COUNT

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return HEADERS[section]
        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        col = _column_for(index.column())
        if col is not None and col.editable:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        miner = self._rows[index.row()]
        col = _column_for(index.column())

        if role == IPR_SORT_ROLE:
            if col is None:
                return index.row()  # action cols: stable by insertion order
            if col.sort_key is not None:
                return col.sort_key(miner)
            return self._display(miner, col)

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if col is None:
                return None  # action columns render via the delegate, no text
            return self._display(miner, col)

        if role == Qt.ItemDataRole.ToolTipRole and col is not None:
            return col.tooltip

        return None

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        col = _column_for(index.column())
        if col is None or not col.editable:
            return False
        setattr(self._rows[index.row()], col.field, value)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, role])
        return True

    @staticmethod
    def _display(miner: MinerData, col: Column) -> str:
        value = getattr(miner, col.field, None)
        if value is None or value == "":
            return "N/A"
        if col.field == "recv_at":
            # recv_at is an epoch int; render like the old QDateTime string
            return QDateTime.fromSecsSinceEpoch(int(value)).toString()
        return str(value)

    def miner_at(self, row: int) -> MinerData:
        """Return the MinerData for a *source* row (caller maps proxy->source)."""
        return self._rows[row]

    def distinct_values(self, col: int) -> list[str]:
        """Distinct display labels for a column, grouped case-insensitively.

        Near-duplicate casings (e.g. ``Antminer``/``antminer``) collapse into a
        single entry; the representative label is the most frequently occurring
        casing within the group. Returned sorted case-insensitively so the
        header filter dropdown lists values in a stable, readable order.
        """
        column = _column_for(col)
        if column is None:
            return []
        counts: Counter[str] = Counter(
            self._display(miner, column) for miner in self._rows
        )
        representative: dict[str, str] = {}
        best_count: dict[str, int] = {}
        for label, count in counts.items():
            key = label.casefold()
            if count > best_count.get(key, -1):
                best_count[key] = count
                representative[key] = label
        return sorted(representative.values(), key=str.casefold)

    def append(self, miner: MinerData) -> int:
        row = len(self._rows)
        self.beginInsertRows(QModelIndex(), row, row)
        self._rows.append(miner)
        self.endInsertRows()
        return row

    def update_row(self, row: int, miner: MinerData) -> None:
        """In-place refresh (e.g. from polling) — emits dataChanged for the row."""
        self._rows[row] = miner
        top = self.index(row, 0)
        bottom = self.index(row, COLUMN_COUNT - 1)
        self.dataChanged.emit(top, bottom)

    def upsert(self, miner: MinerData, key: str = "mac") -> int:
        """Insert, or refresh in place if a row with the same key already exists.

        This is the polling-friendly path: matching by mac/serial means a fresh
        datagram for a known miner updates its row instead of duplicating it.
        """
        new_key = getattr(miner, key, None)
        if new_key:
            for i, existing in enumerate(self._rows):
                if getattr(existing, key, None) == new_key:
                    self.update_row(i, miner)
                    return i
        return self.append(miner)

    def clear(self) -> None:
        self.beginResetModel()
        self._rows.clear()
        self.endResetModel()

    def export_rows(self) -> list[MinerData]:
        return list(self._rows)
