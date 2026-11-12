# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ..titlebar import IPRTitlebar


class ExportRowScope(str, Enum):
    ALL = "all"
    CURRENT_VIEW = "current_view"
    SELECTED = "selected"


class ExportColumnScope(str, Enum):
    ALL = "all"
    VISIBLE = "visible"


class TableExportOptions(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    row_scope: ExportRowScope = ExportRowScope.ALL
    column_scope: ExportColumnScope = ExportColumnScope.ALL


class IDTableExportDialog(QDialog):
    """Select the rows and columns included in an ID-table export."""

    def __init__(
        self,
        parent: QWidget,
        *,
        total_rows: int,
        current_rows: int,
        selected_rows: int,
        total_columns: int,
        visible_columns: int,
    ) -> None:
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setObjectName("idTableExportDialog")
        self.setModal(True)
        self.setWindowTitle("Export ID Table")

        self._row_counts: dict[ExportRowScope, int] = {
            ExportRowScope.ALL: total_rows,
            ExportRowScope.CURRENT_VIEW: current_rows,
            ExportRowScope.SELECTED: selected_rows,
        }
        self._column_counts: dict[ExportColumnScope, int] = {
            ExportColumnScope.ALL: total_columns,
            ExportColumnScope.VISIBLE: visible_columns,
        }

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = IPRTitlebar(self, "Export ID Table", ["close"])
        title_bar.setFixedHeight(30)
        _ = title_bar.close_button.clicked.connect(self.reject)
        layout.addWidget(title_bar)

        body = QWidget(self)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(15, 15, 15, 15)
        body_layout.setSpacing(10)

        rows_group = QGroupBox("Rows", body)
        rows_layout = QVBoxLayout(rows_group)
        self.all_rows: QRadioButton = QRadioButton(
            f"All table rows ({total_rows})", rows_group
        )
        self.current_rows: QRadioButton = QRadioButton(
            f"Current filtered view ({current_rows})", rows_group
        )
        self.selected_rows: QRadioButton = QRadioButton(
            f"Selected rows ({selected_rows})", rows_group
        )
        self.selected_rows.setEnabled(selected_rows > 0)
        self.all_rows.setChecked(True)
        rows_layout.addWidget(self.all_rows)
        rows_layout.addWidget(self.current_rows)
        rows_layout.addWidget(self.selected_rows)
        body_layout.addWidget(rows_group)

        columns_group = QGroupBox("Columns", body)
        columns_layout = QVBoxLayout(columns_group)
        self.all_columns: QRadioButton = QRadioButton(
            f"All data columns ({total_columns})", columns_group
        )
        self.visible_columns: QRadioButton = QRadioButton(
            f"Visible columns ({visible_columns})", columns_group
        )
        self.all_columns.setChecked(True)
        columns_layout.addWidget(self.all_columns)
        columns_layout.addWidget(self.visible_columns)
        body_layout.addWidget(columns_group)

        self.summary: QLabel = QLabel(body)
        body_layout.addWidget(self.summary)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel", body)
        _ = cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.export_button: QPushButton = QPushButton("Export", body)
        self.export_button.setDefault(True)
        _ = self.export_button.clicked.connect(self.accept)
        buttons.addWidget(self.export_button)
        body_layout.addLayout(buttons)
        layout.addWidget(body)

        for option in (
            self.all_rows,
            self.current_rows,
            self.selected_rows,
            self.all_columns,
            self.visible_columns,
        ):
            _ = option.toggled.connect(self._update_summary)
        self._update_summary()

    @property
    def options(self) -> TableExportOptions:
        if self.selected_rows.isEnabled() and self.selected_rows.isChecked():
            row_scope = ExportRowScope.SELECTED
        elif self.current_rows.isChecked():
            row_scope = ExportRowScope.CURRENT_VIEW
        else:
            row_scope = ExportRowScope.ALL

        column_scope = (
            ExportColumnScope.VISIBLE
            if self.visible_columns.isChecked()
            else ExportColumnScope.ALL
        )
        return TableExportOptions(row_scope=row_scope, column_scope=column_scope)

    def _update_summary(self) -> None:
        options = self.options
        rows = self._row_counts[options.row_scope]
        columns = self._column_counts[options.column_scope]
        self.summary.setText(f"Exporting {rows} rows × {columns} columns")
        self.export_button.setEnabled(rows > 0 and columns > 0)
