# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Sort/filter proxy for the ID table.

Sorting uses the model's ``SortRole`` so columns sort by their real type
(epoch int, ipv4 int) instead of by display string. A row is shown only if it
passes *both* filters that may be active: the free-text needle (matched against
any backing field) and the per-column value filters set from the Excel-style
header dropdowns. Column filters are ``AND``-ed together; values are compared
via ``normalize_value`` (case- and space-insensitive) so near-duplicates share
one filter entry.
"""

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QSortFilterProxyModel, Qt

from .model import ACTION_COLUMN_COUNT, COLUMN_COUNT, IPR_SORT_ROLE, normalize_value


class IPRFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSortRole(IPR_SORT_ROLE)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._needle = ""
        # view column index -> set of casefolded allowed display values
        self._column_filters: dict[int, set[str]] = {}

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        # vertical header = 1-based row count in the current (sorted/filtered)
        # display order, rather than the underlying source row index
        if (
            orientation == Qt.Orientation.Vertical
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return section + 1
        return super().headerData(section, orientation, role)

    def set_filter_text(self, text: str) -> None:
        """Filter rows to those where any field contains ``text``."""
        self._needle = text.strip().lower()
        self.invalidateFilter()

    def set_column_filter(self, col: int, labels: list[str] | None) -> None:
        """Restrict ``col`` to rows whose value is one of ``labels``.

        ``labels`` are display strings; matching is case-insensitive. Passing
        ``None`` or an empty list clears the filter for that column (show all).
        """
        if not labels:
            self._column_filters.pop(col, None)
        else:
            self._column_filters[col] = {normalize_value(label) for label in labels}
        self.invalidateFilter()

    def clear_column_filters(self) -> None:
        """Drop every per-column filter (used by Reset View)."""
        if self._column_filters:
            self._column_filters.clear()
            self.invalidateFilter()

    def active_filter_columns(self) -> set[int]:
        """View column indices that currently have a value filter applied."""
        return set(self._column_filters)

    def column_filter(self, col: int) -> set[str] | None:
        """Normalized allowed values for ``col``, or ``None`` if unfiltered."""
        return self._column_filters.get(col)

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ) -> bool:
        model = self.sourceModel()
        # per-column value filters: every active column must match (AND)
        for col, allowed in self._column_filters.items():
            index = model.index(source_row, col, source_parent)
            value = model.data(index, Qt.ItemDataRole.DisplayRole)
            if normalize_value(str(value)) not in allowed:
                return False
        # free-text needle: match against any data column (OR)
        if self._needle:
            for col in range(ACTION_COLUMN_COUNT, COLUMN_COUNT):
                index = model.index(source_row, col, source_parent)
                value = model.data(index, Qt.ItemDataRole.DisplayRole)
                if value and self._needle in str(value).lower():
                    break
            else:
                return False
        return True
