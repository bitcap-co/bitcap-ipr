# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for IPRD socket lifecycle and listening-intent guards."""

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from PySide6.QtNetwork import QAbstractSocket

from mod.lm.iprd.listener import IPRDListener


class TestIPRDListenerLifecycle(unittest.TestCase):
    def test_stop_aborts_pending_connection(self) -> None:
        socket = Mock()
        socket.state.return_value = QAbstractSocket.SocketState.ConnectingState
        reconnect_timer = Mock()
        stopped = Mock()
        subject: Any = SimpleNamespace(
            _intentional_stop=False,
            _resume_after_suspend=True,
            _reconnect_timer=reconnect_timer,
            sock=socket,
            active=True,
            stopped=stopped,
        )

        IPRDListener.stop(subject)

        self.assertTrue(subject._intentional_stop)
        self.assertFalse(subject._resume_after_suspend)
        reconnect_timer.stop.assert_called_once_with()
        socket.abort.assert_called_once_with()
        self.assertFalse(subject.active)
        stopped.emit.assert_called_once_with()

    def test_late_connected_callback_does_not_subscribe_after_stop(self) -> None:
        socket = Mock()
        subscribed = Mock()
        subject: Any = SimpleNamespace(
            _intentional_stop=True,
            _power_suspended=False,
            sock=socket,
            active=True,
            subscribed=subscribed,
        )

        IPRDListener._send_subscribe(subject)

        socket.abort.assert_called_once_with()
        socket.write.assert_not_called()
        self.assertFalse(subject.active)
        subscribed.emit.assert_not_called()

    def test_resume_restores_active_connection_without_auto_reconnect(self) -> None:
        socket = Mock()
        socket.state.return_value = QAbstractSocket.SocketState.ConnectedState
        reconnect_timer = Mock()
        reconnect_timer.isActive.return_value = False
        reset_reconnect_state = Mock()
        schedule_reconnect = Mock()
        subject: Any = SimpleNamespace(
            _power_suspended=False,
            _resume_after_suspend=False,
            _intentional_stop=False,
            _reconnect_timer=reconnect_timer,
            auto_reconnect=False,
            sock=socket,
            active=True,
            addr=SimpleNamespace(isNull=lambda: False),
            _reset_reconnect_state=reset_reconnect_state,
            _schedule_reconnect=schedule_reconnect,
        )

        IPRDListener.on_suspend(subject)

        self.assertTrue(subject._power_suspended)
        self.assertTrue(subject._resume_after_suspend)
        self.assertFalse(subject.active)
        reconnect_timer.stop.assert_called_once_with()
        socket.abort.assert_called_once_with()

        IPRDListener.on_resume(subject)

        self.assertFalse(subject._power_suspended)
        self.assertFalse(subject._resume_after_suspend)
        reset_reconnect_state.assert_called_once_with()
        schedule_reconnect.assert_called_once_with()

    def test_resume_restores_pending_reconnect(self) -> None:
        socket = Mock()
        socket.state.return_value = QAbstractSocket.SocketState.UnconnectedState
        reconnect_timer = Mock()
        reconnect_timer.isActive.return_value = True
        schedule_reconnect = Mock()
        subject: Any = SimpleNamespace(
            _power_suspended=False,
            _resume_after_suspend=False,
            _intentional_stop=False,
            _reconnect_timer=reconnect_timer,
            sock=socket,
            active=False,
            addr=SimpleNamespace(isNull=lambda: False),
            _reset_reconnect_state=Mock(),
            _schedule_reconnect=schedule_reconnect,
        )

        IPRDListener.on_suspend(subject)
        IPRDListener.on_resume(subject)

        socket.abort.assert_not_called()
        schedule_reconnect.assert_called_once_with()

    def test_idle_listener_does_not_reconnect_after_resume(self) -> None:
        socket = Mock()
        socket.state.return_value = QAbstractSocket.SocketState.UnconnectedState
        reconnect_timer = Mock()
        reconnect_timer.isActive.return_value = False
        schedule_reconnect = Mock()
        subject: Any = SimpleNamespace(
            _power_suspended=False,
            _resume_after_suspend=False,
            _intentional_stop=False,
            _reconnect_timer=reconnect_timer,
            sock=socket,
            active=False,
            addr=SimpleNamespace(isNull=lambda: False),
            _reset_reconnect_state=Mock(),
            _schedule_reconnect=schedule_reconnect,
        )

        IPRDListener.on_suspend(subject)
        IPRDListener.on_resume(subject)

        self.assertFalse(subject._resume_after_suspend)
        socket.abort.assert_not_called()
        schedule_reconnect.assert_not_called()

    def test_suspend_induced_error_is_ignored(self) -> None:
        error_signal = Mock()
        schedule_reconnect = Mock()
        subject: Any = SimpleNamespace(
            _power_suspended=True,
            _intentional_stop=False,
            active=True,
            error=error_signal,
            _schedule_reconnect=schedule_reconnect,
        )

        IPRDListener.emit_error(subject, QAbstractSocket.SocketError.OperationError)

        self.assertFalse(subject.active)
        error_signal.emit.assert_not_called()
        schedule_reconnect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
