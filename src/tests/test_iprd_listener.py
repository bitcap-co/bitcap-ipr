# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for IPRD socket lifecycle and listening-intent guards."""

import json
import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from PySide6.QtCore import QByteArray
from PySide6.QtNetwork import QAbstractSocket, QHostAddress

from mod.lm.iprd.listener import IPRDListener


def report_line(ip: str) -> QByteArray:
    return QByteArray(
        (
            json.dumps(
                {
                    "timestamp": 1727298000123,
                    "packetID": f"packet-{ip}",
                    "dstPort": 1314,
                    "srcIP": ip,
                    "srcMAC": "AA:BB:CC:DD:EE:FF",
                    "minerHint": "goldshell",
                }
            )
            + "\n"
        ).encode()
    )


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
        stopped = Mock()
        subject: Any = SimpleNamespace(
            _intentional_stop=False,
            sock=socket,
            active=True,
            stopped=stopped,
        )

        IPRDListener.stop(subject)

        self.assertTrue(subject._intentional_stop)
        socket.abort.assert_called_once_with()
        self.assertFalse(subject.active)
        stopped.emit.assert_called_once_with()

    def test_late_connected_callback_does_not_subscribe_after_stop(self) -> None:
        socket = Mock()
        subscribed = Mock()
        subject: Any = SimpleNamespace(
            _intentional_stop=True,
            sock=socket,
            active=True,
            subscribed=subscribed,
        )

        IPRDListener._send_subscribe(subject)

        socket.abort.assert_called_once_with()
        socket.write.assert_not_called()
        self.assertFalse(subject.active)
        subscribed.emit.assert_not_called()

    def test_partial_report_remains_buffered_until_line_is_complete(self) -> None:
        socket = Mock()
        socket.canReadLine.return_value = False
        subject: Any = SimpleNamespace(sock=socket, emit_result=Mock())

        IPRDListener._process_message(subject)

        socket.readLine.assert_not_called()
        subject.emit_result.assert_not_called()

    def test_processes_every_complete_report_in_one_ready_read(self) -> None:
        socket = Mock()
        socket.canReadLine.side_effect = [True, True, False]
        socket.readLine.side_effect = [
            report_line("192.168.1.20"),
            report_line("192.168.1.21"),
        ]
        subject: Any = SimpleNamespace(sock=socket, emit_result=Mock())

        IPRDListener._process_message(subject)

        self.assertEqual(subject.emit_result.call_count, 2)
        self.assertEqual(
            [call.args[0].src_ip for call in subject.emit_result.call_args_list],
            ["192.168.1.20", "192.168.1.21"],
        )

    def test_malformed_report_does_not_discard_following_report(self) -> None:
        socket = Mock()
        socket.canReadLine.side_effect = [True, True, False]
        socket.readLine.side_effect = [
            QByteArray(b"not json\n"),
            report_line("192.168.1.20"),
        ]
        subject: Any = SimpleNamespace(sock=socket, emit_result=Mock())

        IPRDListener._process_message(subject)

        subject.emit_result.assert_called_once()
        self.assertEqual(subject.emit_result.call_args.args[0].src_ip, "192.168.1.20")

    def test_unintentional_socket_errors_are_all_emitted(self) -> None:
        socket = Mock()
        socket.errorString.return_value = "connection refused"
        error_signal = Mock()
        subject: Any = SimpleNamespace(
            _intentional_stop=False,
            active=True,
            sock=socket,
            error=error_signal,
        )

        IPRDListener.emit_error(
            subject, QAbstractSocket.SocketError.ConnectionRefusedError
        )
        IPRDListener.emit_error(
            subject, QAbstractSocket.SocketError.RemoteHostClosedError
        )

        self.assertFalse(subject.active)
        self.assertEqual(error_signal.emit.call_count, 2)
        self.assertEqual(
            [call.args[0] for call in error_signal.emit.call_args_list],
            ["ConnectionRefusedError", "RemoteHostClosedError"],
        )

    def test_intentional_stop_suppresses_socket_error(self) -> None:
        error_signal = Mock()
        subject: Any = SimpleNamespace(
            _intentional_stop=True,
            active=True,
            sock=Mock(),
            error=error_signal,
        )

        IPRDListener.emit_error(subject, QAbstractSocket.SocketError.OperationError)

        self.assertFalse(subject.active)
        error_signal.emit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
