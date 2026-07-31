# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for main-window IPRD resume recovery coordination."""

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import config  # noqa: F401  # initialize Pydantic before importing PySide-backed IPR
from ipr import IPR, ListenState


class TestIPRDRecovery(unittest.TestCase):
    def test_app_activation_refreshes_empty_resume_discovery(self) -> None:
        discovery = Mock()
        discovery.restart_after_resume.return_value = True
        auto_discover = Mock()
        auto_discover.isChecked.return_value = True
        subject: Any = SimpleNamespace(
            _iprd_listening=True,
            iprd=SimpleNamespace(active=False),
            iprd_discovery=discovery,
            checkEnableIPRDAutoDiscover=auto_discover,
            _listen_state=ListenState.DISCOVERING,
            _last_iprd_error="previous error",
            _wait_for_iprd_service=Mock(),
            start_listen=Mock(),
        )

        IPR._maybe_reconnect_iprd(subject)

        discovery.restart_after_resume.assert_called_once_with()
        self.assertEqual(subject._last_iprd_error, "")
        subject._wait_for_iprd_service.assert_called_once_with()
        subject.start_listen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
