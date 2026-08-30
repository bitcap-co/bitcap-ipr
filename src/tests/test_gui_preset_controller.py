# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import os
import unittest
from typing import final, override
from unittest.mock import Mock

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QCheckBox, QLineEdit, QWidget

from config import IPRConfig, PoolPreset, SocketPreset
from ui.widgets import (
    IPRPresetSelector,
    PoolPresetController,
    PoolPresetWidgets,
    SocketPresetController,
    SocketPresetWidgets,
)

_QT_APP = QApplication.instance()
_GUI_AVAILABLE = _QT_APP is None or isinstance(_QT_APP, QApplication)
_APP = QApplication([]) if _QT_APP is None else _QT_APP


def _fields() -> tuple[QLineEdit, QLineEdit, QLineEdit]:
    return QLineEdit(), QLineEdit(), QLineEdit()


@unittest.skipUnless(_GUI_AVAILABLE, "a QCoreApplication already owns the Qt process")
@final
class TestPoolPresetController(unittest.TestCase):
    parent: QWidget
    config: IPRConfig
    selector: IPRPresetSelector
    urls: tuple[QLineEdit, QLineEdit, QLineEdit]
    users: tuple[QLineEdit, QLineEdit, QLineEdit]
    passwords: tuple[QLineEdit, QLineEdit, QLineEdit]
    write: Mock

    @override
    def setUp(self) -> None:
        self.parent = QWidget()
        self.config = IPRConfig()
        self.write = Mock()
        self.config.write = self.write
        self.selector = IPRPresetSelector()
        self.urls = _fields()
        self.users = _fields()
        self.passwords = _fields()

    def controller(self) -> PoolPresetController:
        return PoolPresetController(
            self.parent,
            self.config,
            PoolPresetWidgets(
                selector=self.selector,
                urls=self.urls,
                users=self.users,
                passwords=self.passwords,
            ),
        )

    def test_reload_populates_selected_preset_without_writing(self) -> None:
        self.config.pool_config.pool_presets = [
            PoolPreset(
                preset_name="Primary",
                pool1="stratum://pool",
                user1="account.worker",
                passwd1="x",
            )
        ]
        self.config.pool_config.selected_preset = 0

        controller = self.controller()

        self.assertEqual(controller.index, 0)
        self.assertEqual(self.selector.preset_name, "Primary")
        self.assertEqual(self.urls[0].text(), "stratum://pool")
        self.assertEqual(self.users[0].text(), "account.worker")
        self.assertEqual(self.passwords[0].text(), "x")
        self.write.assert_not_called()

    def test_create_does_not_reenter_selection_or_rename_handlers(self) -> None:
        controller = self.controller()

        controller.create()

        self.assertEqual(len(self.config.pool_config.pool_presets), 1)
        self.assertEqual(controller.index, 0)
        self.assertEqual(self.selector.preset_name, "New Preset")
        self.write.assert_called_once_with()

    def test_snapshot_includes_unsaved_visible_fields(self) -> None:
        self.config.pool_config.pool_presets = [PoolPreset(preset_name="Primary")]
        self.config.pool_config.selected_preset = 0
        controller = self.controller()
        self.urls[0].setText("stratum://updated")
        self.users[0].setText("updated.worker")

        snapshot = controller.snapshot()

        self.assertEqual(snapshot[0]["pool1"], "stratum://updated")
        self.assertEqual(snapshot[0]["user1"], "updated.worker")
        self.assertEqual(self.config.pool_config.pool_presets[0].pool1, "")

    def test_rename_with_no_selection_is_ignored(self) -> None:
        controller = self.controller()

        controller.rename("orphan")

        self.assertEqual(self.config.pool_config.pool_presets, [])
        self.write.assert_not_called()


@unittest.skipUnless(_GUI_AVAILABLE, "a QCoreApplication already owns the Qt process")
@final
class TestSocketPresetController(unittest.TestCase):
    parent: QWidget
    config: IPRConfig
    selector: IPRPresetSelector
    address: QLineEdit
    auto_discover: QCheckBox
    restart: Mock
    write: Mock

    @override
    def setUp(self) -> None:
        self.parent = QWidget()
        self.config = IPRConfig()
        self.write = Mock()
        self.config.write = self.write
        self.selector = IPRPresetSelector()
        self.address = QLineEdit()
        self.auto_discover = QCheckBox()
        self.restart = Mock()

    def controller(self) -> SocketPresetController:
        return SocketPresetController(
            self.parent,
            self.config,
            SocketPresetWidgets(
                selector=self.selector,
                address=self.address,
                auto_discover=self.auto_discover,
            ),
            self.restart,
        )

    def test_reload_does_not_restart_listener(self) -> None:
        self.config.listener.iprd.socket_presets = [
            SocketPreset(preset_name="Local", socket_addr="127.0.0.1:7788")
        ]
        self.config.listener.iprd.selected_preset = 0

        controller = self.controller()

        self.assertEqual(controller.index, 0)
        self.assertEqual(self.address.text(), "127.0.0.1:7788")
        self.restart.assert_not_called()

    def test_user_selection_updates_address_and_restarts(self) -> None:
        self.config.listener.iprd.socket_presets = [
            SocketPreset(preset_name="First", socket_addr="10.0.0.1:7788"),
            SocketPreset(preset_name="Second", socket_addr="10.0.0.2:7788"),
        ]
        self.config.listener.iprd.selected_preset = 0
        controller = self.controller()

        self.selector.combo.setCurrentIndex(1)

        self.assertEqual(controller.index, 1)
        self.assertEqual(self.address.text(), "10.0.0.2:7788")
        self.assertEqual(self.config.listener.iprd.selected_preset, 1)
        self.restart.assert_called_once_with()

    def test_remove_selects_remaining_socket_and_restarts(self) -> None:
        self.config.listener.iprd.socket_presets = [
            SocketPreset(preset_name="First", socket_addr="10.0.0.1:7788"),
            SocketPreset(preset_name="Second", socket_addr="10.0.0.2:7788"),
        ]
        self.config.listener.iprd.selected_preset = 0
        controller = self.controller()

        controller.remove()

        self.assertEqual(controller.index, 0)
        self.assertEqual(self.address.text(), "10.0.0.2:7788")
        self.restart.assert_called_once_with()

    def test_auto_discovery_snapshot_preserves_stored_address(self) -> None:
        self.config.listener.iprd.socket_presets = [
            SocketPreset(preset_name="Local", socket_addr="stored:7788")
        ]
        self.config.listener.iprd.selected_preset = 0
        controller = self.controller()
        self.address.setText("discovered:7788")
        self.auto_discover.setChecked(True)

        snapshot = controller.snapshot()

        self.assertEqual(snapshot[0]["socket_addr"], "stored:7788")


if __name__ == "__main__":
    unittest.main()
