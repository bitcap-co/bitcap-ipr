# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import os
import unittest
from typing import final, override
from unittest.mock import Mock

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QTableView, QToolButton, QWidget

from config import IDTablePreset, IPRConfig
from ui.widgets import (
    COL_ACTION,
    IDTablePresetController,
    IDTablePresetWidgets,
    IPRPresetSelector,
    IPRTableModel,
    column_for_field,
    configurable_columns,
)

_QT_APP = QApplication.instance()
_GUI_AVAILABLE = _QT_APP is None or isinstance(_QT_APP, QApplication)
_APP = QApplication([]) if _QT_APP is None else _QT_APP


@unittest.skipUnless(_GUI_AVAILABLE, "a QCoreApplication already owns the Qt process")
@final
class TestIDTablePresetController(unittest.TestCase):
    parent: QWidget
    config: IPRConfig
    table: QTableView
    selector: IPRPresetSelector
    columns_button: QToolButton
    write: Mock

    @override
    def setUp(self) -> None:
        self.parent = QWidget()
        self.config = IPRConfig()
        self.write = Mock()
        self.config.write = self.write
        self.table = QTableView()
        self.table.setModel(IPRTableModel(self.table))
        self.selector = IPRPresetSelector()
        self.columns_button = QToolButton()

    def controller(self) -> IDTablePresetController:
        return IDTablePresetController(
            self.parent,
            self.config,
            IDTablePresetWidgets(
                table=self.table,
                selector=self.selector,
                columns_button=self.columns_button,
            ),
        )

    def test_column_helpers_use_stable_fields_and_exclude_action_column(self) -> None:
        columns = configurable_columns()

        self.assertTrue(columns)
        self.assertNotIn(COL_ACTION, [index for index, _ in columns])
        self.assertEqual(column_for_field("ip"), 2)
        self.assertIsNone(column_for_field("removed_column"))

    def test_reload_applies_selected_preset_and_ignores_unknown_fields(self) -> None:
        self.config.instance.views.table_presets = [
            IDTablePreset(
                preset_name="Network",
                hiddenColumns=["serial", "removed_column"],
            )
        ]

        controller = self.controller()

        serial = column_for_field("serial")
        ip = column_for_field("ip")
        assert serial is not None and ip is not None
        self.assertEqual(controller.index, 0)
        self.assertTrue(self.table.isColumnHidden(serial))
        self.assertFalse(self.table.isColumnHidden(ip))
        self.assertFalse(self.table.isColumnHidden(COL_ACTION))
        self.write.assert_not_called()

    def test_select_applies_and_persists_preset(self) -> None:
        self.config.instance.views.table_presets = [
            IDTablePreset(preset_name="All"),
            IDTablePreset(preset_name="Compact", hiddenColumns=["serial"]),
        ]
        controller = self.controller()

        self.selector.combo.setCurrentIndex(1)

        serial = column_for_field("serial")
        assert serial is not None
        self.assertEqual(self.config.instance.views.selected_table_preset, 1)
        self.assertTrue(self.table.isColumnHidden(serial))
        self.write.assert_called_once_with()

    def test_toggling_column_updates_selected_preset(self) -> None:
        controller = self.controller()

        controller.set_column_visible("serial", False)

        serial = column_for_field("serial")
        assert serial is not None
        self.assertTrue(self.table.isColumnHidden(serial))
        self.assertEqual(
            self.config.instance.views.table_presets[0].hidden_columns,
            ["serial"],
        )
        self.write.assert_called_once_with()

        controller.set_column_visible("serial", True)

        self.assertFalse(self.table.isColumnHidden(serial))
        self.assertEqual(self.config.instance.views.table_presets[0].hidden_columns, [])

    def test_create_captures_current_visibility(self) -> None:
        controller = self.controller()
        serial = column_for_field("serial")
        assert serial is not None
        self.table.setColumnHidden(serial, True)

        controller.create()

        self.assertEqual(controller.index, 1)
        self.assertEqual(
            self.config.instance.views.table_presets[1].hidden_columns,
            ["serial"],
        )
        self.assertEqual(self.selector.preset_name, "New Preset")
        self.write.assert_called_once_with()

    def test_remove_applies_remaining_preset(self) -> None:
        self.config.instance.views.table_presets = [
            IDTablePreset(preset_name="Compact", hiddenColumns=["serial"]),
            IDTablePreset(preset_name="All"),
        ]
        controller = self.controller()

        controller.remove()

        serial = column_for_field("serial")
        assert serial is not None
        self.assertEqual(controller.index, 0)
        self.assertEqual(self.selector.preset_name, "All")
        self.assertFalse(self.table.isColumnHidden(serial))
        self.write.assert_called_once_with()

    def test_snapshot_uses_configuration_aliases(self) -> None:
        self.config.instance.views.table_presets = [
            IDTablePreset(preset_name="Compact", hiddenColumns=["serial"])
        ]
        controller = self.controller()

        self.assertEqual(
            controller.snapshot(),
            [{"preset_name": "Compact", "hiddenColumns": ["serial"]}],
        )


if __name__ == "__main__":
    unittest.main()
