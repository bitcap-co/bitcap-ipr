# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import sys
import time
import unittest
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QUdpSocket
from PySide6.QtWidgets import QButtonGroup

from mod.lm import IPReport, Listener, ListenerError, ListenerManager, Record

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


class TestRecord(unittest.TestCase):
    def test_same_ip_and_mac_within_window_is_duplicate(self) -> None:
        record = Record(capacity=2)
        first = IPReport(
            ip="192.168.1.10",
            mac="aa:bb:cc:dd:ee:ff",
            updated_at=time.time(),
        )
        duplicate = first.model_copy()

        self.assertTrue(record.add(first))
        self.assertFalse(record.add(duplicate))
        self.assertIs(record[first.ip], first)

    def test_same_ip_with_different_mac_replaces_entry(self) -> None:
        record = Record(capacity=2)
        first = IPReport(ip="192.168.1.10", mac="aa:bb:cc:dd:ee:01")
        replacement = IPReport(ip=first.ip, mac="aa:bb:cc:dd:ee:02")

        self.assertTrue(record.add(first))
        self.assertTrue(record.add(replacement))
        self.assertIs(record[first.ip], replacement)

    def test_replacing_entry_refreshes_fifo_position(self) -> None:
        record = Record(capacity=2)
        first = IPReport(ip="192.168.1.10", mac="aa:bb:cc:dd:ee:01")
        second = IPReport(ip="192.168.1.11", mac="aa:bb:cc:dd:ee:02")
        replacement = IPReport(ip=first.ip, mac="aa:bb:cc:dd:ee:03")
        third = IPReport(ip="192.168.1.12", mac="aa:bb:cc:dd:ee:04")

        record.add(first)
        record.add(second)
        record.add(replacement)
        record.add(third)

        self.assertEqual(list(record), [replacement.ip, third.ip])


class TestListenerManager(unittest.TestCase):
    def test_common_miner_selections_create_one_listener(self) -> None:
        manager = ListenerManager(parent=app)
        ids = [1, 4, 5]
        names = ["Antminer", "Volcminer", "Hammer"]
        buttons = [
            SimpleNamespace(
                isChecked=lambda: True,
                text=lambda name=name: name,
            )
            for name in names
        ]
        button_group = cast(
            QButtonGroup,
            cast(
                object,
                SimpleNamespace(
                    buttons=lambda: buttons,
                    id=lambda button: ids[buttons.index(button)],
                ),
            ),
        )

        with patch("mod.lm.listenermanager.Listener", wraps=Listener) as listener_type:
            self.assertTrue(manager.start(button_group))

        listener_type.assert_called_once()
        self.assertEqual(manager.count, 1)
        self.assertEqual(manager.status, "Antminer, Volcminer, Hammer")
        manager.stop()

    def test_start_returns_false_when_no_listener_is_selected(self) -> None:
        manager = ListenerManager(parent=app)
        buttons = QButtonGroup(manager)

        self.assertFalse(manager.start(buttons))
        self.assertEqual(manager.count, 0)

    def test_bind_failure_forwards_native_listener_error(self) -> None:
        blocker = QUdpSocket()
        self.assertTrue(blocker.bind(QHostAddress.SpecialAddress.AnyIPv4, 0))
        port = blocker.localPort()
        manager = ListenerManager(parent=app)
        errors: list[ListenerError] = []
        manager.bind_failed.connect(errors.append)

        manager._append_listener(port)

        self.assertEqual(manager.count, 0)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].port, port)
        self.assertIsNotNone(errors[0].error_name)
        self.assertTrue(errors[0].message)
        blocker.close()
        manager.stop()

    def test_runtime_error_removes_listener_before_forwarding(self) -> None:
        manager = ListenerManager(parent=app)
        listener = Listener(port=0, parent=manager)
        self.assertTrue(listener.bound)
        manager._listeners.append(listener)
        listener.error.connect(manager.emit_error_received)
        listener.result.connect(manager.emit_report_received)
        observed_counts: list[int] = []
        errors: list[ListenerError] = []

        def capture_error(error: ListenerError) -> None:
            observed_counts.append(manager.count)
            errors.append(error)

        manager.error_received.connect(capture_error)

        listener.emit_error(QAbstractSocket.SocketError.NetworkError)

        self.assertEqual(observed_counts, [0])
        self.assertEqual(len(errors), 1)
        self.assertEqual(
            errors[0].error_name,
            QAbstractSocket.SocketError.NetworkError,
        )
        self.assertEqual(manager.count, 0)
        self.assertEqual(manager.status, "")
        manager.stop()


if __name__ == "__main__":
    unittest.main()
