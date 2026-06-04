# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Sort/filter proxy for the ID table.

Sorting uses the model's ``SortRole`` so columns sort by their real type
(epoch int, ipv4 int) instead of by display string. Filtering matches a
free-text needle against every backing field of a row.
"""

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QSortFilterProxyModel, Qt

from .model import ACTION_COLUMN_COUNT, COLUMN_COUNT, IPR_SORT_ROLE


class IPRFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSortRole(IPR_SORT_ROLE)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._needle = ""

    def set_filter_text(self, text: str) -> None:
        """Filter rows to those where any field contains ``text``."""
        self._needle = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ) -> bool:
        if not self._needle:
            return True
        model = self.sourceModel()
        # skip action columns; match against the data columns only
        for col in range(ACTION_COLUMN_COUNT, COLUMN_COUNT):
            index = model.index(source_row, col, source_parent)
            value = model.data(index, Qt.ItemDataRole.DisplayRole)
            if value and self._needle in str(value).lower():
                return True
        return False
