# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import (
    QFile,
    QIODevice,
    QItemSelectionModel,
    QModelIndex,
    QObject,
    QPoint,
    Qt,
    QTextStream,
    Signal,
)
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHeaderView,
    QLineEdit,
    QTableView,
    QToolButton,
    QWidget,
)

from mod.ipr_asic.data import MinerData, MinerFirmware, MinerType

from .contextmenu import IPRTableContextMenu
from .csv import MinerCSVError, miner_from_mapping, parse_miner_csv, serialize_csv
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


class IPRTableWidgets(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", arbitrary_types_allowed=True
    )
    table: QTableView
    text_filter: QLineEdit
    sort_column: QComboBox
    sort_order: QToolButton
    reset_view: QToolButton


class IPRTableController(QObject):
    """Owns ID-table presentation, data access, and UI action routing."""

    notification_requested: Signal = Signal(str, int)
    dashboard_requested: Signal = Signal(str, object)
    miner_action_requested: Signal = Signal(int)
    bulk_miner_action_requested: Signal = Signal(str, object)
    pool_retrieval_requested: Signal = Signal(int)
    pool_update_requested: Signal = Signal(object)
    configurator_visibility_requested: Signal = Signal(bool)

    def __init__(
        self,
        parent: QWidget,
        widgets: IPRTableWidgets,
        dashboard_url: DashboardURL,
    ) -> None:
        super().__init__(parent)
        self._window: QWidget = parent
        self._table: QTableView = widgets.table
        self._text_filter: QLineEdit = widgets.text_filter
        self._sort_column: QComboBox = widgets.sort_column
        self._sort_order: QToolButton = widgets.sort_order
        self._reset_view_button: QToolButton = widgets.reset_view
        self._dashboard_url: DashboardURL = dashboard_url

        self.model: IPRTableModel = IPRTableModel(self)
        self.proxy: IPRFilterProxyModel = IPRFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.header: FilterHeaderView = FilterHeaderView(self._table)
        self.action_delegate: IPRActionDelegate = IPRActionDelegate(self._table)
        self._context_menu: IPRTableContextMenu = IPRTableContextMenu(self._window)
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
        self.action_delegate.action_clicked.connect(self._request_miner_action)
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

        self._context_menu.contextActionOpenSelectedIPs.triggered.connect(
            self.open_selected_ips
        )
        self._context_menu.contextActionCopySelected.triggered.connect(
            self.copy_selected
        )
        self._context_menu.contextActionClearTable.triggered.connect(self.clear)
        self._context_menu.contextActionRefreshMiners.triggered.connect(
            self.request_bulk_refresh
        )
        self._context_menu.contextActionLocateMiners.triggered.connect(
            self.request_bulk_locate
        )
        self._context_menu.contextActionConfiguratorShowHide.toggled.connect(
            self.request_configurator_visibility
        )
        self._context_menu.contextActionConfigutorGetPool.triggered.connect(
            self.request_pool_retrieval
        )
        self._context_menu.contextActionConfiguratorSetPools.triggered.connect(
            self.request_pool_update
        )
        self._context_menu.contextActionTableImport.triggered.connect(self.import_table)
        self._context_menu.contextActionTableExport.triggered.connect(self.export_table)
        self._context_menu.contextActionTableResetSortOrder.triggered.connect(
            self.reset_sort
        )
        self._context_menu.contextActionTableResetView.triggered.connect(
            self.reset_view
        )

    def _on_double_click(self, index: QModelIndex) -> None:
        column = index.column()
        if column == COL_IP:
            source_row = self.proxy.mapToSource(index).row()
            miner = self.model.miner_at(source_row)
            self.dashboard_requested.emit(str(index.data()), miner.type)
        elif column == COL_SERIAL:
            self._table.edit(index)

    def append_miner(self, miner: MinerData) -> int:
        return self.model.append(miner)

    def populate_data(
        self,
        data: dict[str, Any],
        row: int | None = None,
        dedupe_key: str | None = None,
    ) -> int:
        """Insert or update miner data and return its source-model row."""
        logger.info("populate_data : write table data.")
        miner = miner_from_mapping(data)
        if row is not None:
            self.model.update_row(row, miner)
            return row

        before = self.model.rowCount()
        source_row = (
            self.model.upsert(miner, key=dedupe_key)
            if dedupe_key
            else self.model.append(miner)
        )
        if self.model.rowCount() > before:
            self._table.scrollToBottom()
        return source_row

    def miner_at(self, source_row: int) -> MinerData:
        return self.model.miner_at(source_row)

    def miner_target(self, source_row: int) -> tuple[str, MinerType, MinerFirmware]:
        miner = self.miner_at(source_row)
        miner_type = (
            miner.type
            if isinstance(miner.type, MinerType)
            else MinerType.from_value(str(miner.type or ""))
        )
        firmware = (
            miner.firmware
            if isinstance(miner.firmware, MinerFirmware)
            else MinerFirmware.from_value(str(miner.firmware or ""))
        )
        if firmware == MinerFirmware.LUX_OS:
            miner_type = MinerType.LUX_OS
        elif firmware == MinerFirmware.VNISH:
            miner_type = MinerType.VNISH
        return str(miner.ip or ""), miner_type, firmware

    def has_rows(self) -> bool:
        return self.proxy.rowCount() > 0

    def export_csv(self) -> str | None:
        """Serialize visible proxy rows in their current display order."""
        rows = self.proxy.rowCount()
        if not rows:
            return None
        columns = range(1, self.proxy.columnCount())
        headers = [
            str(
                self.model.headerData(
                    column,
                    Qt.Orientation.Horizontal,
                    Qt.ItemDataRole.DisplayRole,
                )
            ).replace(" ", "_")
            for column in columns
        ]
        data_rows = (
            [str(self.proxy.index(row, column).data()) for column in columns]
            for row in range(rows)
        )
        return serialize_csv(headers, data_rows)

    def import_table(self, *_args: object) -> None:
        logger.info("import_table : import table.")
        directory = Path(Path.home(), "Documents", "ipr").resolve()
        file_name, _ = QFileDialog.getOpenFileName(
            self._window,
            "Open .CSV",
            str(directory),
            ".CSV Files (*.csv)",
        )
        if not file_name:
            return

        csv_file = QFile(file_name)
        if not csv_file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            logger.error(f"import_table : failed to read file {file_name}.")
            self.notification_requested.emit("Status :: Failed to import table.", 5000)
            return

        try:
            miners = parse_miner_csv(QTextStream(csv_file).readAll())
        except MinerCSVError as error:
            logger.error(f"import_table : failed to parse {file_name}: {error!s}")
            self.notification_requested.emit("Status :: Failed to import table.", 5000)
            return
        finally:
            csv_file.close()

        self.clear()
        for miner in miners:
            self.append_miner(miner)

    def export_table(self, *_args: object) -> None:
        logger.info("export_table : export table.")
        output = self.export_csv()
        if output is None:
            return

        directory = Path(Path.home(), "Documents", "ipr").resolve()
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().astimezone().strftime("%Y-%m-%d")
        file_path = directory / f"id_table-{timestamp}-{int(time.time())}.csv"
        csv_file = QFile(str(file_path))
        if not csv_file.open(
            QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Truncate
        ):
            logger.error(f"export_table : failed to write file {file_path}.")
            self.notification_requested.emit("Status :: Failed to export table.", 5000)
            return

        stream = QTextStream(csv_file)
        stream << output
        stream.flush()
        csv_file.close()
        self.notification_requested.emit(
            f"Status :: Wrote table as .CSV to {directory}.", 3000
        )

    def action_anchor(self, source_row: int) -> QPoint:
        source_index = self.model.index(source_row, COL_ACTION)
        proxy_index = self.proxy.mapFromSource(source_index)
        rect = self._table.visualRect(proxy_index)
        return self._table.viewport().mapToGlobal(rect.bottomLeft())

    def _request_miner_action(self, column: int, source_row: int) -> None:
        if column == COL_ACTION:
            self.miner_action_requested.emit(source_row)

    def request_bulk_action(self, key: str) -> None:
        action = key.capitalize()
        rows = self.action_target_rows(action)
        if not rows:
            self.notification_requested.emit(
                f"Status :: Failed action: no miners to {key}.",
                5000,
            )
            return
        self.bulk_miner_action_requested.emit(key, rows)

    def request_bulk_refresh(self, *_args: object) -> None:
        self.request_bulk_action("refresh")

    def request_bulk_locate(self, *_args: object) -> None:
        self.request_bulk_action("locate")

    def request_pool_retrieval(self, *_args: object) -> None:
        rows = self.selected_source_rows(COL_IP)
        if not rows:
            self.notification_requested.emit(
                "Status :: Failed action: no selected IPs.", 5000
            )
            return
        self.pool_retrieval_requested.emit(rows[0])

    def request_pool_update(self, *_args: object) -> None:
        rows = self.selected_source_rows_for_action("update_miner_pools", column=COL_IP)
        if not rows:
            self.notification_requested.emit(
                "Status :: Failed action: no selected IPs.", 5000
            )
            return
        self.pool_update_requested.emit(rows)

    def request_configurator_visibility(self, enabled: bool) -> None:
        self.configurator_visibility_requested.emit(enabled)

    def set_configurator_visible(self, enabled: bool) -> None:
        action = self._context_menu.contextActionConfiguratorShowHide
        was_blocked = action.blockSignals(True)
        action.setChecked(enabled)
        action.blockSignals(was_blocked)
        self._context_menu.contextActionConfigutorGetPool.setEnabled(enabled)
        self._context_menu.contextActionConfiguratorSetPools.setEnabled(enabled)

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
        self._context_menu.exec(QCursor.pos())
