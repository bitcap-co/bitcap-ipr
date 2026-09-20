# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import unittest
from json.decoder import JSONDecodeError
from typing import override
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QMessageBox

from config import IPRConfig
from main import Main


class TestMainConfiguration(unittest.TestCase):
    main: Main
    config: IPRConfig

    @override
    def setUp(self) -> None:
        self.main = Main.__new__(Main)
        self.config = IPRConfig()
        self.main.config = self.config

    @patch("main.QMessageBox.critical")
    def test_restore_defaults_continues_startup(self, critical: Mock):
        critical.return_value = QMessageBox.StandardButton.RestoreDefaults

        with (
            patch.object(
                self.config,
                "read",
                side_effect=JSONDecodeError("invalid JSON", "", 0),
            ),
            patch.object(self.config, "write_default") as write_default,
        ):
            initialized = self.main._init_conf()

        self.assertTrue(initialized)
        write_default.assert_called_once_with()

    @patch("main.QMessageBox.critical")
    def test_dismissing_invalid_configuration_stops_startup(self, critical: Mock):
        critical.return_value = QMessageBox.StandardButton.Ok

        with (
            patch.object(
                self.config,
                "read",
                side_effect=JSONDecodeError("invalid JSON", "", 0),
            ),
            patch.object(self.config, "write_default") as write_default,
        ):
            initialized = self.main._init_conf()

        self.assertFalse(initialized)
        write_default.assert_not_called()


if __name__ == "__main__":
    unittest.main()
