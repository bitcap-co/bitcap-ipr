# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for top-level listener startup state transitions."""

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import config  # noqa: F401  # initialize Pydantic before importing PySide-backed IPR
from ipr import IPR, ListenState


class TestListenState(unittest.TestCase):
    def test_suspend_preserves_active_timers_across_duplicate_notifications(
        self,
    ) -> None:
        discovery_timeout = Mock()
        discovery_timeout.isActive.side_effect = [True, False]
        inactive = Mock()
        inactive.isActive.side_effect = [True, False]
        discovery = Mock()
        listener = Mock()
        subject: Any = SimpleNamespace(
            _resume_discovery_timeout=False,
            _resume_inactive_timer=False,
            iprd_discovery_timeout=discovery_timeout,
            inactive=inactive,
            iprd_discovery=discovery,
            iprd=listener,
        )

        IPR.on_suspend(subject)
        IPR.on_suspend(subject)

        self.assertTrue(subject._resume_discovery_timeout)
        self.assertTrue(subject._resume_inactive_timer)
        self.assertEqual(discovery_timeout.stop.call_count, 2)
        self.assertEqual(inactive.stop.call_count, 2)
        self.assertEqual(discovery.on_suspend.call_count, 2)
        self.assertEqual(listener.on_suspend.call_count, 2)

    def test_resume_restarts_only_previously_active_applicable_timers(self) -> None:
        discovery_timeout = Mock()
        inactive = Mock()
        discovery = Mock()
        listener = Mock()
        subject: Any = SimpleNamespace(
            _resume_discovery_timeout=True,
            _resume_inactive_timer=True,
            _iprd_listening=True,
            _listen_state=ListenState.DISCOVERING,
            lm=SimpleNamespace(count=0),
            menu_bar=SimpleNamespace(
                actionDisableInactiveTimer=SimpleNamespace(isChecked=lambda: False)
            ),
            iprd_discovery_timeout=discovery_timeout,
            inactive=inactive,
            iprd_discovery=discovery,
            iprd=listener,
        )

        IPR.on_resume(subject)

        discovery.on_resume.assert_called_once_with()
        listener.on_resume.assert_called_once_with()
        inactive.start.assert_called_once_with()
        discovery_timeout.start.assert_called_once_with()
        self.assertFalse(subject._resume_discovery_timeout)
        self.assertFalse(subject._resume_inactive_timer)

        subject._resume_discovery_timeout = True
        subject._resume_inactive_timer = True
        subject._iprd_listening = False
        subject._listen_state = ListenState.LISTENING
        subject.lm.count = 1
        subject.menu_bar.actionDisableInactiveTimer.isChecked = lambda: True
        discovery_timeout.reset_mock()
        inactive.reset_mock()

        IPR.on_resume(subject)

        inactive.start.assert_not_called()
        discovery_timeout.start.assert_not_called()

    def test_zero_udp_listeners_is_a_complete_start_failure(self) -> None:
        listener_option = SimpleNamespace(isChecked=lambda: True)
        listener_config = SimpleNamespace(buttons=lambda: [listener_option])
        inactive = Mock()
        listener_manager = SimpleNamespace(count=0, start=Mock())
        update_controls = Mock()
        set_listen_state = Mock()
        notify = Mock()
        subject: Any = SimpleNamespace(
            listenerConfig=listener_config,
            checkEnableIPRDBackend=SimpleNamespace(isChecked=lambda: False),
            menu_bar=SimpleNamespace(
                actionDisableInactiveTimer=SimpleNamespace(isChecked=lambda: False)
            ),
            inactive=inactive,
            lm=listener_manager,
            _iprd_listening=True,
            _last_iprd_error="previous error",
            _update_listen_controls=update_controls,
            set_listen_state=set_listen_state,
            notify=notify,
        )

        IPR.start_listen(subject)

        listener_manager.start.assert_called_once_with(listener_config)
        self.assertFalse(subject._iprd_listening)
        self.assertEqual(subject._last_iprd_error, "")
        inactive.start.assert_called_once_with()
        inactive.stop.assert_called_once_with()
        set_listen_state.assert_called_once_with(ListenState.READY)
        update_controls.assert_called_once_with()
        notify.assert_called_once_with(
            "Status :: Failed to start listeners: Failed to bind or invalid configuration"
        )


if __name__ == "__main__":
    unittest.main()
