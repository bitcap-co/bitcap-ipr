# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for main-window IPRD retry status presentation."""

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import config  # noqa: F401  # initialize Pydantic before importing PySide-backed IPR
from ipr import IPR, ListenState


class TestIPRDRecoveryStatus(unittest.TestCase):
    def test_retry_pause_preserves_intent_and_enters_disconnected(self) -> None:
        subject: Any = SimpleNamespace(
            _iprd_listening=True,
            _listen_state=ListenState.RECONNECTING,
            _retry_cooldown_ms=0,
            set_listen_state=lambda state: setattr(subject, "_listen_state", state),
            stop_listen=Mock(),
        )

        IPR.on_iprd_retry_paused(subject, 60000)

        self.assertTrue(subject._iprd_listening)
        self.assertEqual(subject._retry_cooldown_ms, 60000)
        self.assertEqual(subject._listen_state, ListenState.DISCONNECTED)
        subject.stop_listen.assert_not_called()

    def test_disconnected_status_shows_next_retry_cycle(self) -> None:
        subject: Any = SimpleNamespace(
            _listen_state=ListenState.DISCONNECTED,
            _retry_cooldown_ms=60000,
        )

        status = IPR._base_status_text(subject)

        self.assertEqual(
            status,
            "Status :: IPR Daemon disconnected; restarting retry cycle in 60s…",
        )


if __name__ == "__main__":
    unittest.main()
