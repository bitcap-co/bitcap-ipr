# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

from mod.updater import IPRReleaseInfo, UpdateController


class TestUpdateController(unittest.TestCase):
    @patch("mod.updater.controller.UpdateChecker")
    def test_check_uses_current_prerelease_setting_and_wires_worker(
        self, checker_type: Mock
    ) -> None:
        checker = checker_type.return_value
        subject: Any = SimpleNamespace(
            _checker=None,
            _check_silent=False,
            _current_version="1.2.3",
            _include_prereleases=Mock(return_value=True),
            check_enabled_changed=Mock(),
            notification_requested=Mock(),
            _on_update_available=Mock(),
            _on_up_to_date=Mock(),
            _on_update_error=Mock(),
        )

        UpdateController.check_for_updates(subject, silent=True)

        checker_type.assert_called_once_with("1.2.3", True, subject)
        subject.check_enabled_changed.emit.assert_called_once_with(False)
        checker.update_available.connect.assert_called_once_with(
            subject._on_update_available
        )
        checker.up_to_date.connect.assert_called_once_with(subject._on_up_to_date)
        checker.error.connect.assert_called_once_with(subject._on_update_error)
        checker.finished.connect.assert_called_once()
        subject.notification_requested.emit.assert_called_once_with(
            "Status :: Checking for updates...", 3000
        )
        checker.start.assert_called_once_with()
        self.assertTrue(subject._check_silent)

    @patch("mod.updater.controller.webbrowser.open")
    @patch("mod.updater.controller.select_asset", return_value=None)
    @patch("mod.updater.controller.get_platform", return_value=("linux", False))
    def test_download_without_matching_asset_opens_release_page(
        self, _platform: Mock, _select_asset: Mock, open_browser: Mock
    ) -> None:
        release = IPRReleaseInfo(
            tag="v2.0.0",
            url="https://example.com/releases/v2.0.0",
        )

        subject: Any = SimpleNamespace()
        UpdateController.download_update(subject, release)

        open_browser.assert_called_once_with(
            "https://example.com/releases/v2.0.0", new=2
        )

    def test_stop_cancels_and_waits_for_active_workers(self) -> None:
        downloader = Mock()
        downloader.isRunning.return_value = True
        downloader.wait.return_value = True
        checker = Mock()
        checker.isRunning.return_value = True
        checker.wait.return_value = True
        installer = Mock()
        installer.isRunning.return_value = True
        installer.wait.return_value = True
        subject: Any = SimpleNamespace(
            _downloader=downloader,
            _checker=checker,
            _installer=installer,
        )

        UpdateController.stop(subject)

        downloader.cancel.assert_called_once_with()
        downloader.wait.assert_called_once_with(5000)
        checker.wait.assert_called_once_with(3000)
        installer.wait.assert_called_once_with(3000)
        downloader.terminate.assert_not_called()
        checker.terminate.assert_not_called()
        installer.terminate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
