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
from mod.lm import IPRDControllerState, ListenerError


class TestListenState(unittest.TestCase):
    def test_suspend_preserves_active_timers_across_duplicate_notifications(
        self,
    ) -> None:
        inactive = Mock()
        inactive.isActive.side_effect = [True, False]
        controller = Mock()
        subject: Any = SimpleNamespace(
            _resume_inactive_timer=False,
            inactive=inactive,
            iprd_controller=controller,
        )

        IPR.on_suspend(subject)
        IPR.on_suspend(subject)

        self.assertTrue(subject._resume_inactive_timer)
        self.assertEqual(inactive.stop.call_count, 2)
        self.assertEqual(controller.on_suspend.call_count, 2)

    def test_resume_restarts_only_previously_active_applicable_timers(self) -> None:
        inactive = Mock()
        controller = Mock()
        subject: Any = SimpleNamespace(
            _resume_inactive_timer=True,
            _iprd_listening=True,
            lm=SimpleNamespace(count=0),
            menu_bar=SimpleNamespace(
                actionDisableInactiveTimer=SimpleNamespace(isChecked=lambda: False)
            ),
            inactive=inactive,
            iprd_controller=controller,
        )

        IPR.on_resume(subject)

        controller.on_resume.assert_called_once_with()
        inactive.start.assert_called_once_with()
        self.assertFalse(subject._resume_inactive_timer)

        subject._resume_inactive_timer = True
        subject._iprd_listening = False
        subject.lm.count = 1
        subject.menu_bar.actionDisableInactiveTimer.isChecked = lambda: True
        controller.reset_mock()
        inactive.reset_mock()

        IPR.on_resume(subject)

        controller.on_resume.assert_called_once_with()
        inactive.start.assert_not_called()

    def test_controller_retry_state_preserves_listener_cooldown_status(self) -> None:
        set_listen_state = Mock()
        subject: Any = SimpleNamespace(
            _listen_state=ListenState.DISCONNECTED,
            iprd_controller=SimpleNamespace(listening=True),
            inactive=Mock(),
            _iprd_listening=True,
            _update_listen_controls=Mock(),
            set_listen_state=set_listen_state,
        )

        IPR.on_iprd_controller_state_changed(subject, IPRDControllerState.RETRYING)

        set_listen_state.assert_not_called()

    def test_controller_waiting_state_updates_status(self) -> None:
        set_listen_state = Mock()
        subject: Any = SimpleNamespace(
            _listen_state=ListenState.CONNECTING,
            iprd_controller=SimpleNamespace(listening=True),
            inactive=Mock(),
            _iprd_listening=True,
            _update_listen_controls=Mock(),
            set_listen_state=set_listen_state,
        )

        IPR.on_iprd_controller_state_changed(
            subject, IPRDControllerState.WAITING_FOR_NETWORK
        )

        set_listen_state.assert_called_once_with(ListenState.WAITING_FOR_NETWORK)

    def test_zero_udp_listeners_is_a_complete_start_failure(self) -> None:
        listener_option = SimpleNamespace(isChecked=lambda: True)
        listener_config = SimpleNamespace(buttons=lambda: [listener_option])
        inactive = Mock()
        listener_manager = SimpleNamespace(count=0, start=Mock(return_value=False))
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
            _has_configured_listener=lambda: True,
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

    def test_no_configured_listener_does_not_start_manager(self) -> None:
        listener_manager = SimpleNamespace(start=Mock())
        inactive = Mock()
        notify = Mock()
        subject: Any = SimpleNamespace(
            lm=listener_manager,
            inactive=inactive,
            notify=notify,
            _has_configured_listener=lambda: False,
        )

        IPR.start_listen(subject)

        listener_manager.start.assert_not_called()
        inactive.start.assert_not_called()
        notify.assert_called_once_with(
            "Status :: Failed to start listeners: No listeners configured"
        )

    def test_runtime_error_refreshes_state_when_listeners_remain(self) -> None:
        inactive = Mock()
        set_listen_state = Mock()
        update_controls = Mock()
        notify = Mock()
        subject: Any = SimpleNamespace(
            lm=SimpleNamespace(count=1),
            inactive=inactive,
            set_listen_state=set_listen_state,
            _update_listen_controls=update_controls,
            notify=notify,
        )
        error = ListenerError(
            listener="Listener[Goldshell:1314]",
            port=1314,
            port_name="Goldshell",
            message="Network error",
        )

        IPR.show_listener_error(subject, error)

        inactive.stop.assert_not_called()
        set_listen_state.assert_called_once_with(ListenState.LISTENING)
        update_controls.assert_called_once_with()
        notify.assert_called_once_with(
            "Status :: Listener for Goldshell stopped: Network error; continuing without."
        )

    def test_runtime_error_returns_to_ready_when_last_listener_stops(self) -> None:
        inactive = Mock()
        set_listen_state = Mock()
        update_controls = Mock()
        notify = Mock()
        subject: Any = SimpleNamespace(
            lm=SimpleNamespace(count=0),
            inactive=inactive,
            set_listen_state=set_listen_state,
            _update_listen_controls=update_controls,
            notify=notify,
        )
        error = ListenerError(
            listener="Listener[Goldshell:1314]",
            port=1314,
            port_name="Goldshell",
            message="Network error",
        )

        IPR.show_listener_error(subject, error)

        inactive.stop.assert_called_once_with()
        set_listen_state.assert_called_once_with(ListenState.READY)
        update_controls.assert_called_once_with()
        notify.assert_called_once_with(
            "Status :: Listener for Goldshell stopped: Network error; no more active listeners."
        )

    def test_bind_error_only_displays_startup_diagnostic(self) -> None:
        notify = Mock()
        subject: Any = SimpleNamespace(notify=notify)
        error = ListenerError(
            listener="Listener[Goldshell:1314]",
            port=1314,
            port_name="Goldshell",
            message="Address already in use",
        )

        IPR.show_listener_bind_error(subject, error)

        notify.assert_called_once_with(
            "Status :: Failed to start listening for Goldshell: "
            "Address already in use; Goldshell reports will be excluded."
        )


if __name__ == "__main__":
    unittest.main()
