# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for IPRD socket lifecycle and listening-intent guards."""

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from PySide6.QtNetwork import QAbstractSocket, QHostAddress

from mod.lm.iprd.listener import IPRDListener


class TestIPRDListenerLifecycle(unittest.TestCase):
    def test_set_socket_addr_rejects_invalid_values_atomically(self) -> None:
        subject: Any = SimpleNamespace(
            addr=QHostAddress("192.168.1.10"),
            port=7788,
        )

        for addr, port in (
            ("not-an-ip", 7788),
            ("192.168.1.20", 0),
            ("192.168.1.20", 65536),
        ):
            with self.subTest(addr=addr, port=port):
                self.assertFalse(IPRDListener.set_socket_addr(subject, addr, port))
                self.assertEqual(subject.addr.toString(), "192.168.1.10")
                self.assertEqual(subject.port, 7788)

    def test_set_socket_addr_accepts_valid_ipv4_and_ipv6(self) -> None:
        subject: Any = SimpleNamespace(addr=QHostAddress(), port=7788)

        self.assertTrue(IPRDListener.set_socket_addr(subject, "192.168.1.20", 1234))
        self.assertEqual(subject.addr.toString(), "192.168.1.20")
        self.assertEqual(subject.port, 1234)

        self.assertTrue(IPRDListener.set_socket_addr(subject, "::1", 65535))
        self.assertEqual(subject.addr.toString(), "::1")
        self.assertEqual(subject.port, 65535)

    def test_stop_aborts_pending_connection(self) -> None:
        socket = Mock()
        socket.state.return_value = QAbstractSocket.SocketState.ConnectingState
        reconnect_timer = Mock()
        retry_cooldown_timer = Mock()
        stopped = Mock()
        subject: Any = SimpleNamespace(
            _intentional_stop=False,
            _resume_after_suspend=True,
            _reconnect_timer=reconnect_timer,
            _retry_cooldown_timer=retry_cooldown_timer,
            sock=socket,
            active=True,
            stopped=stopped,
        )

        IPRDListener.stop(subject)

        self.assertTrue(subject._intentional_stop)
        self.assertFalse(subject._resume_after_suspend)
        reconnect_timer.stop.assert_called_once_with()
        retry_cooldown_timer.stop.assert_called_once_with()
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
        retry_cooldown_timer = Mock()
        retry_cooldown_timer.isActive.return_value = False
        reset_reconnect_state = Mock()
        schedule_reconnect = Mock()
        subject: Any = SimpleNamespace(
            _power_suspended=False,
            _resume_after_suspend=False,
            _intentional_stop=False,
            _reconnect_timer=reconnect_timer,
            _retry_cooldown_timer=retry_cooldown_timer,
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
        retry_cooldown_timer = Mock()
        retry_cooldown_timer.isActive.return_value = False
        schedule_reconnect = Mock()
        subject: Any = SimpleNamespace(
            _power_suspended=False,
            _resume_after_suspend=False,
            _intentional_stop=False,
            _reconnect_timer=reconnect_timer,
            _retry_cooldown_timer=retry_cooldown_timer,
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
        retry_cooldown_timer = Mock()
        retry_cooldown_timer.isActive.return_value = False
        schedule_reconnect = Mock()
        subject: Any = SimpleNamespace(
            _power_suspended=False,
            _resume_after_suspend=False,
            _intentional_stop=False,
            _reconnect_timer=reconnect_timer,
            _retry_cooldown_timer=retry_cooldown_timer,
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

    def test_exhausted_retry_cycle_starts_cooldown_without_stopping(self) -> None:
        reconnect_timer = Mock()
        retry_cooldown_timer = Mock()
        retry_paused = Mock()
        socket = Mock()
        subject: Any = SimpleNamespace(
            _power_suspended=False,
            _intentional_stop=False,
            _reconnect_attempts=3,
            max_reconnect_attempts=3,
            _retry_cooldown_ms=60000,
            _reconnect_timer=reconnect_timer,
            _retry_cooldown_timer=retry_cooldown_timer,
            retry_paused=retry_paused,
            sock=socket,
        )

        IPRDListener._schedule_reconnect(subject)

        self.assertFalse(subject._intentional_stop)
        reconnect_timer.stop.assert_called_once_with()
        socket.abort.assert_called_once_with()
        retry_paused.emit.assert_called_once_with(60000)
        retry_cooldown_timer.start.assert_called_once_with(60000)

    def test_cooldown_restarts_retry_cycle(self) -> None:
        reset_reconnect_state = Mock()
        schedule_reconnect = Mock()
        subject: Any = SimpleNamespace(
            _intentional_stop=False,
            _power_suspended=False,
            _reset_reconnect_state=reset_reconnect_state,
            _schedule_reconnect=schedule_reconnect,
        )

        IPRDListener._restart_retry_cycle(subject)

        reset_reconnect_state.assert_called_once_with()
        schedule_reconnect.assert_called_once_with()

    def test_start_cancels_pending_cooldown(self) -> None:
        retry_cooldown_timer = Mock()
        reset_reconnect_state = Mock()
        socket = Mock()
        subject: Any = SimpleNamespace(
            addr=SimpleNamespace(isNull=lambda: False),
            port=7788,
            _intentional_stop=True,
            _retry_cooldown_timer=retry_cooldown_timer,
            _reset_reconnect_state=reset_reconnect_state,
            active=False,
            sock=socket,
        )

        IPRDListener.start(subject)

        self.assertFalse(subject._intentional_stop)
        retry_cooldown_timer.stop.assert_called_once_with()
        reset_reconnect_state.assert_called_once_with()
        socket.connectToHost.assert_called_once_with(subject.addr, 7788)

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
