# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import os
import unittest
from typing import final, override

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QWidget

from ui.widgets import (
    ExportColumnScope,
    ExportRowScope,
    IDTableExportDialog,
)

_QT_APP = QApplication.instance()
_GUI_AVAILABLE = _QT_APP is None or isinstance(_QT_APP, QApplication)
_APP = QApplication([]) if _QT_APP is None else _QT_APP


@unittest.skipUnless(_GUI_AVAILABLE, "a QCoreApplication already owns the Qt process")
@final
class TestIDTableExportDialog(unittest.TestCase):
    parent: QWidget

    @override
    def setUp(self) -> None:
        self.parent = QWidget()

    def dialog(self, selected_rows: int = 2) -> IDTableExportDialog:
        return IDTableExportDialog(
            self.parent,
            total_rows=10,
            current_rows=4,
            selected_rows=selected_rows,
            total_columns=16,
            visible_columns=9,
        )

    def test_defaults_to_all_rows_and_columns(self) -> None:
        dialog = self.dialog()

        self.assertEqual(dialog.options.row_scope, ExportRowScope.ALL)
        self.assertEqual(dialog.options.column_scope, ExportColumnScope.ALL)
        self.assertEqual(dialog.summary.text(), "Exporting 10 rows × 16 columns")
        self.assertTrue(dialog.export_button.isEnabled())

    def test_current_view_and_visible_columns_update_options(self) -> None:
        dialog = self.dialog()

        dialog.current_rows.setChecked(True)
        dialog.visible_columns.setChecked(True)

        self.assertEqual(dialog.options.row_scope, ExportRowScope.CURRENT_VIEW)
        self.assertEqual(dialog.options.column_scope, ExportColumnScope.VISIBLE)
        self.assertEqual(dialog.summary.text(), "Exporting 4 rows × 9 columns")

    def test_selected_rows_is_disabled_when_selection_is_empty(self) -> None:
        dialog = self.dialog(selected_rows=0)

        self.assertFalse(dialog.selected_rows.isEnabled())
        dialog.selected_rows.setChecked(True)

        self.assertEqual(dialog.options.row_scope, ExportRowScope.ALL)


if __name__ == "__main__":
    unittest.main()
