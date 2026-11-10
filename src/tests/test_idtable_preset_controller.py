# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import os
import unittest
from typing import final, override
from unittest.mock import Mock

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QSignalBlocker
from PySide6.QtTest import QTest
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

    def test_default_preset_hides_uptime(self) -> None:
        self.controller()

        uptime = column_for_field("uptime")
        assert uptime is not None
        self.assertTrue(self.table.isColumnHidden(uptime))
        menu = self.columns_button.menu()
        assert menu is not None
        uptime_action = next(
            action for action in menu.actions() if action.text() == "UPTIME"
        )
        self.assertFalse(uptime_action.isChecked())
        url = column_for_field("stratum_url")
        assert url is not None
        self.assertEqual(self.table.columnWidth(url), 400)
        default = self.config.instance.views.table_presets[0]
        self.assertEqual(default.hidden_columns, [])
        self.assertEqual(default.column_widths, {})
        self.assertFalse(self.selector.remove_button.isEnabled())
        line_edit = self.selector.combo.lineEdit()
        assert line_edit is not None
        self.assertTrue(line_edit.isReadOnly())
        self.write.assert_not_called()

    def test_default_preset_ignores_stored_visibility_changes(self) -> None:
        self.config.instance.views.table_presets = [
            IDTablePreset(
                preset_name="Default",
                hiddenColumns=["serial"],
                columnWidths={"serial": 275},
            )
        ]

        self.controller()

        serial = column_for_field("serial")
        uptime = column_for_field("uptime")
        assert serial is not None and uptime is not None
        self.assertFalse(self.table.isColumnHidden(serial))
        self.assertTrue(self.table.isColumnHidden(uptime))
        self.assertEqual(self.table.columnWidth(serial), 180)

    def test_resizing_default_preset_creates_custom_preset(self) -> None:
        controller = self.controller()
        serial = column_for_field("serial")
        assert serial is not None

        self.table.setColumnWidth(serial, 275)

        default, created = self.config.instance.views.table_presets
        self.assertEqual(default.column_widths, {})
        self.assertEqual(created.column_widths["serial"], 275)
        self.assertEqual(controller.index, 1)
        self.assertEqual(created.preset_name, "New Preset")
        self.write.assert_called_once_with()

    def test_custom_widths_restore_and_resize_writes_are_debounced(self) -> None:
        self.config.instance.views.table_presets = [
            IDTablePreset(preset_name="Default"),
            IDTablePreset(
                preset_name="Wide Serial",
                hiddenColumns=[],
                columnWidths={"serial": 260},
            ),
        ]
        self.config.instance.views.selected_table_preset = 1
        controller = self.controller()
        serial = column_for_field("serial")
        assert serial is not None
        self.assertEqual(self.table.columnWidth(serial), 260)

        self.table.setColumnWidth(serial, 290)

        preset = self.config.instance.views.table_presets[1]
        self.assertEqual(preset.column_widths["serial"], 290)
        self.write.assert_not_called()
        QTest.qWait(300)
        self.write.assert_called_once_with()
        self.assertEqual(controller.index, 1)

    def test_default_preset_cannot_be_renamed_or_removed(self) -> None:
        controller = self.controller()

        controller.rename("Changed")
        controller.remove()

        self.assertEqual(len(self.config.instance.views.table_presets), 1)
        self.assertEqual(
            self.config.instance.views.table_presets[0].preset_name,
            "Default",
        )
        self.write.assert_not_called()

    def test_explicitly_enabling_default_hidden_column_creates_preset(self) -> None:
        controller = self.controller()
        uptime = column_for_field("uptime")
        assert uptime is not None

        controller.set_column_visible("uptime", True)
        controller.reload()

        default, created = self.config.instance.views.table_presets
        self.assertNotIn("hidden_columns", default.model_fields_set)
        self.assertEqual(default.hidden_columns, [])
        self.assertIn("hidden_columns", created.model_fields_set)
        self.assertEqual(created.hidden_columns, ["api_version"])
        self.assertEqual(controller.index, 1)
        self.assertEqual(created.preset_name, "New Preset")
        self.assertFalse(self.table.isColumnHidden(uptime))

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
        default, created = self.config.instance.views.table_presets
        self.assertEqual(default.hidden_columns, [])
        self.assertEqual(created.hidden_columns, ["serial", "uptime", "api_version"])
        self.assertEqual(created.column_widths["serial"], 180)
        self.assertEqual(controller.index, 1)
        self.write.assert_called_once_with()

        controller.set_column_visible("serial", True)

        self.assertFalse(self.table.isColumnHidden(serial))
        self.assertEqual(default.hidden_columns, [])
        self.assertEqual(created.hidden_columns, ["uptime", "api_version"])

    def test_create_captures_current_visibility(self) -> None:
        controller = self.controller()
        serial = column_for_field("serial")
        assert serial is not None
        blocker = QSignalBlocker(self.table.horizontalHeader())
        self.table.setColumnHidden(serial, True)
        del blocker

        controller.create()

        self.assertEqual(controller.index, 1)
        self.assertEqual(
            self.config.instance.views.table_presets[1].hidden_columns,
            ["serial", "uptime", "api_version"],
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
            [
                {
                    "preset_name": "Compact",
                    "hiddenColumns": ["serial"],
                    "columnWidths": {},
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
