# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from collections.abc import Callable

from PySide6.QtCore import QItemSelectionModel, QModelIndex, QObject, QPoint, Qt, Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHeaderView,
    QLineEdit,
    QTableView,
    QToolButton,
    QWidget,
)

from mod.ipr_asic.data import MinerType

from .contextmenu import IPRTableContextMenu
from .delegate import IPRActionDelegate
from .filterpopup import ColumnFilterPopup
from .header import FilterHeaderView
from .model import (
    COL_ACTION,
    COL_FWVERSION,
    COL_IP,
    COL_RECV_AT,
    COL_SERIAL,
    COL_URL,
    COL_USER,
    FILTERABLE_COLUMNS,
    IPRTableModel,
)
from .proxy import IPRFilterProxyModel

logger = logging.getLogger(__name__)

DashboardURL = Callable[[str, MinerType | str | None], str]


class IPRTableController(QObject):
    """Owns passive ID-table presentation and interaction behavior."""

    notification_requested: Signal = Signal(str, int)
    dashboard_requested: Signal = Signal(str, object)
    row_action_requested: Signal = Signal(int, int)

    def __init__(
        self,
        parent: QWidget,
        table: QTableView,
        text_filter: QLineEdit,
        sort_column: QComboBox,
        sort_order: QToolButton,
        reset_view: QToolButton,
        dashboard_url: DashboardURL,
    ) -> None:
        super().__init__(parent)
        self._window: QWidget = parent
        self._table: QTableView = table
        self._text_filter: QLineEdit = text_filter
        self._sort_column: QComboBox = sort_column
        self._sort_order: QToolButton = sort_order
        self._reset_view_button: QToolButton = reset_view
        self._dashboard_url: DashboardURL = dashboard_url

        self.model: IPRTableModel = IPRTableModel(self)
        self.proxy: IPRFilterProxyModel = IPRFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.header: FilterHeaderView = FilterHeaderView(self._table)
        self.action_delegate: IPRActionDelegate = IPRActionDelegate(self._table)
        self.context_menu: IPRTableContextMenu = IPRTableContextMenu(self._window)
        self.filter_popup: ColumnFilterPopup | None = None
        self._sort_icons: dict[bool, QIcon] = {
            False: QIcon(":theme/icons/rc/arrow_up.png"),
            True: QIcon(":theme/icons/rc/arrow_down.png"),
        }

        self._configure_view()
        self._connect_signals()
        self.reset_sort()

    def _configure_view(self) -> None:
        self._table.setModel(self.proxy)
        self._table.setHorizontalHeader(self.header)
        self.header.setMinimumSectionSize(15)
        self.header.setDefaultSectionSize(150)
        self.header.setSortIndicatorShown(False)
        self.header.set_filterable_columns(FILTERABLE_COLUMNS)
        self.header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self._table.setItemDelegateForColumn(COL_ACTION, self.action_delegate)
        self._table.setColumnWidth(COL_ACTION, 15)
        self._table.setColumnWidth(COL_RECV_AT, 180)
        self._table.setColumnWidth(COL_SERIAL, 180)
        self._table.setColumnWidth(COL_URL, 400)
        self._table.setColumnWidth(COL_USER, 300)
        self._table.setColumnWidth(COL_FWVERSION, 180)
        self._table.setSortingEnabled(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        vertical_header = self._table.verticalHeader()
        vertical_header.setVisible(True)
        vertical_header.setSectionsClickable(True)
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        for column in range(self.model.columnCount()):
            header = self.model.headerData(
                column,
                Qt.Orientation.Horizontal,
                Qt.ItemDataRole.DisplayRole,
            )
            if header:
                self._sort_column.addItem(str(header), column)

        self._reset_view_button.setIcon(QIcon(":theme/icons/rc/clear.png"))

    def _connect_signals(self) -> None:
        self.action_delegate.action_clicked.connect(self.row_action_requested.emit)
        self._table.doubleClicked.connect(self._on_double_click)
        self.header.customContextMenuRequested.connect(self.toggle_column_at)
        self.header.filter_clicked.connect(self.open_column_filter)
        self._table.verticalHeader().customContextMenuRequested.connect(
            self.toggle_row_at
        )
        self._text_filter.textChanged.connect(self.proxy.set_filter_text)
        self._sort_column.currentIndexChanged.connect(self.apply_sort)
        self._sort_order.toggled.connect(self.apply_sort)
        self._reset_view_button.clicked.connect(self.reset_view)
        self._table.customContextMenuRequested.connect(self.show_context_menu)

        self.context_menu.contextActionOpenSelectedIPs.triggered.connect(
            self.open_selected_ips
        )
        self.context_menu.contextActionCopySelected.triggered.connect(
            self.copy_selected
        )
        self.context_menu.contextActionClearTable.triggered.connect(self.clear)
        self.context_menu.contextActionTableResetSortOrder.triggered.connect(
            self.reset_sort
        )
        self.context_menu.contextActionTableResetView.triggered.connect(self.reset_view)

    def _on_double_click(self, index: QModelIndex) -> None:
        column = index.column()
        if column == COL_IP:
            source_row = self.proxy.mapToSource(index).row()
            miner = self.model.miner_at(source_row)
            self.dashboard_requested.emit(str(index.data()), miner.type)
        elif column == COL_SERIAL:
            self._table.edit(index)

    def selected_source_rows(self, column: int | None = None) -> list[int]:
        if not self.proxy.rowCount():
            return []
        selected = self._table.selectionModel().selectedIndexes()
        if column is not None and column != COL_ACTION:
            selected = [index for index in selected if index.column() == column]
        return [self.proxy.mapToSource(index).row() for index in selected]

    def selected_source_rows_for_action(
        self, action: str, column: int | None = None
    ) -> list[int]:
        if not self.proxy.rowCount():
            return []
        selected = self._table.selectionModel().selectedIndexes()
        if column is not None and column != COL_ACTION:
            selected = [index for index in selected if index.column() == column]
        if not selected:
            return []
        selected_text = [str(index.data()) for index in selected]
        logger.info(f"{action} : running action for {selected_text}...")
        status = (
            f"Status :: Running action: {action} for "
            f"[{','.join(selected_text[0:3])}...]..."
        )
        self.notification_requested.emit(status, 3000)
        return [self.proxy.mapToSource(index).row() for index in selected]

    def action_target_rows(self, action: str) -> list[int]:
        rows = self.proxy.rowCount()
        if not rows:
            return []
        source_rows = self.selected_source_rows(COL_IP)
        if source_rows:
            selected = True
        else:
            selected = False
            source_rows = [
                self.proxy.mapToSource(self.proxy.index(row, COL_IP)).row()
                for row in range(rows)
            ]
        scope = "selected" if selected else "all"
        logger.info(
            f"{action} : running action for {len(source_rows)} ({scope}) miners..."
        )
        self.notification_requested.emit(
            f"Status :: Running action: {action} for "
            f"{len(source_rows)} ({scope}) miners...",
            3000,
        )
        return source_rows

    def open_selected_ips(self) -> None:
        if not self.proxy.rowCount():
            return
        selected = [
            index
            for index in self._table.selectionModel().selectedIndexes()
            if index.column() == COL_IP
        ]
        for index in selected:
            source_row = self.proxy.mapToSource(index).row()
            miner = self.model.miner_at(source_row)
            self.dashboard_requested.emit(str(index.data()), miner.type)

    def copy_selected(self) -> None:
        logger.info(" copy selected elements.")
        rows = self.proxy.rowCount()
        if not rows:
            return
        output = ""
        selected = self._table.selectionModel().selectedIndexes()
        for row in range(rows):
            row_indexes = [index for index in selected if index.row() == row]
            if not row_indexes:
                continue
            for index in range(len(row_indexes)):
                separator = "," if len(row_indexes) > 1 else ""
                cell = row_indexes[index]
                column = cell.column()
                if column == COL_ACTION:
                    continue
                if column == COL_IP:
                    source_row = self.proxy.mapToSource(cell).row()
                    miner = self.model.miner_at(source_row)
                    output += f"{self._dashboard_url(str(cell.data()), miner.type)}{separator}"
                else:
                    output += f"{cell.data()}{separator}"
            output += "\n"
        logger.info("copy_selected : copy elements to clipboard.")
        clipboard = QApplication.clipboard()
        clipboard.clear(mode=clipboard.Mode.Clipboard)
        clipboard.setText(output.strip(), mode=clipboard.Mode.Clipboard)
        self.notification_requested.emit(
            "Status :: Copied elements to clipboard.", 3000
        )

    def _toggle_selection(self, indexes: list[QModelIndex]) -> None:
        if not indexes:
            return
        selection_model = self._table.selectionModel()
        fully_selected = all(selection_model.isSelected(index) for index in indexes)
        flag = (
            QItemSelectionModel.SelectionFlag.Deselect
            if fully_selected
            else QItemSelectionModel.SelectionFlag.Select
        )
        for index in indexes:
            selection_model.select(index, flag)

    def toggle_column_at(self, position: QPoint) -> None:
        section = self.header.logicalIndexAt(position)
        if section < COL_RECV_AT:
            return
        self._toggle_selection(
            [self.proxy.index(row, section) for row in range(self.proxy.rowCount())]
        )

    def toggle_row_at(self, position: QPoint) -> None:
        row = self._table.verticalHeader().logicalIndexAt(position)
        if row < 0:
            return
        self._toggle_selection(
            [
                self.proxy.index(row, column)
                for column in range(self.proxy.columnCount())
            ]
        )

    def open_column_filter(self, section: int) -> None:
        title = self.model.headerData(
            section,
            Qt.Orientation.Horizontal,
            Qt.ItemDataRole.DisplayRole,
        )
        values = self.model.distinct_values(section)
        popup = ColumnFilterPopup(
            str(title),
            values,
            self.proxy.column_filter(section),
            self._window,
        )
        popup.applied.connect(
            lambda labels, col=section, choices=values: self._apply_column_filter(
                col, labels, choices
            )
        )
        popup.cleared.connect(lambda col=section: self._apply_column_filter(col, None))
        self.filter_popup = popup
        popup.show_at(self.header.filter_anchor(section))

    def _apply_column_filter(
        self,
        section: int,
        labels: list[str] | None,
        choices: list[tuple[str, int]] | None = None,
    ) -> None:
        if labels is not None and choices is not None and len(labels) == len(choices):
            labels = None
        self.proxy.set_column_filter(section, labels)
        self.header.set_active_columns(self.proxy.active_filter_columns())

    def apply_sort(self, *_args: object) -> None:
        column = self._sort_column.currentData()
        if not isinstance(column, int):
            return
        descending = self._sort_order.isChecked()
        order = (
            Qt.SortOrder.DescendingOrder if descending else Qt.SortOrder.AscendingOrder
        )
        self._sort_order.setIcon(self._sort_icons[descending])
        self.proxy.sort(column, order)

    def reset_sort(self) -> None:
        self._sort_column.setCurrentIndex(self._sort_column.findData(COL_RECV_AT))
        self._sort_order.setChecked(False)
        self.apply_sort()

    def reset_view(self) -> None:
        self._text_filter.clear()
        self.proxy.clear_column_filters()
        self.header.set_active_columns(self.proxy.active_filter_columns())
        self.reset_sort()

    def clear(self) -> None:
        self.reset_view()
        self.model.clear()

    def show_context_menu(self, _position: QPoint | None = None) -> None:
        self.context_menu.exec(QCursor.pos())
