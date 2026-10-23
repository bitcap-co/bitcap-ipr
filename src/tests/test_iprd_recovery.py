# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for main-window IPRD retry status presentation."""

import unittest
from types import SimpleNamespace
from typing import Any

import config  # noqa: F401  # initialize Pydantic before importing PySide-backed IPR
from ipr import IPR, ListenState


class TestIPRDRecoveryStatus(unittest.TestCase):
    def test_reconnecting_updates_delay_and_preserves_listening_intent(self) -> None:
        subject: Any = SimpleNamespace(
            _iprd_listening=True,
            _listen_state=ListenState.CONNECTING,
            _reconnect_delay_ms=0,
            set_listen_state=lambda state: setattr(subject, "_listen_state", state),
        )

        IPR.on_iprd_reconnecting(subject, 30000)

        self.assertTrue(subject._iprd_listening)
        self.assertEqual(subject._reconnect_delay_ms, 30000)
        self.assertEqual(subject._listen_state, ListenState.RECONNECTING)

    def test_reconnecting_status_shows_capped_delay(self) -> None:
        subject: Any = SimpleNamespace(
            _listen_state=ListenState.RECONNECTING,
            _reconnect_delay_ms=30000,
            _last_iprd_error="ConnectionRefusedError",
        )

        status = IPR._base_status_text(subject)

        self.assertEqual(
            status,
            "Status :: Connection lost (ConnectionRefusedError); reconnecting in 30s…",
        )


if __name__ == "__main__":
    unittest.main()
