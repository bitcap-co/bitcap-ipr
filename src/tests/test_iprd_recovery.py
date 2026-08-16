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
from ipr import IPR, ListenState, _select_iprd_service_address
from mod.lm import IPRDService


def make_service(name: str, addresses: tuple[str, ...]) -> IPRDService:
    return IPRDService(
        name=name,
        instance_name=name,
        hostname="iprd-host.local",
        addresses=addresses,
        port=7788,
        properties={},
    )


class TestIPRDRecovery(unittest.TestCase):
    def test_invalid_endpoint_does_not_start_or_enter_connecting(self) -> None:
        listener = SimpleNamespace(
            auto_reconnect=False,
            max_reconnect_attempts=3,
            set_socket_addr=Mock(return_value=False),
            start=Mock(),
        )
        subject: Any = SimpleNamespace(
            iprd=listener,
            iprd_discovery_timeout=SimpleNamespace(stop=Mock()),
            checkIPRDAutoReconnect=SimpleNamespace(isChecked=lambda: True),
            spinIPRDMaxRetries=SimpleNamespace(value=lambda: 5),
            stop_listen=Mock(),
            notify=Mock(),
            set_listen_state=Mock(),
        )

        started = IPR._start_iprd_connection(subject, "invalid", 7788)

        self.assertFalse(started)
        listener.set_socket_addr.assert_called_once_with("invalid", 7788)
        listener.start.assert_not_called()
        subject.set_listen_state.assert_not_called()
        subject.stop_listen.assert_called_once_with()
        subject.notify.assert_called_once_with(
            "Status :: Failed to start IPRD Listener: Invalid socket address."
        )

    def test_valid_endpoint_starts_and_enters_connecting(self) -> None:
        listener = SimpleNamespace(
            auto_reconnect=False,
            max_reconnect_attempts=3,
            set_socket_addr=Mock(return_value=True),
            start=Mock(),
        )
        subject: Any = SimpleNamespace(
            iprd=listener,
            iprd_discovery_timeout=SimpleNamespace(stop=Mock()),
            checkIPRDAutoReconnect=SimpleNamespace(isChecked=lambda: True),
            spinIPRDMaxRetries=SimpleNamespace(value=lambda: 5),
            _last_iprd_error="previous",
            stop_listen=Mock(),
            notify=Mock(),
            set_listen_state=Mock(),
        )

        started = IPR._start_iprd_connection(subject, "192.168.1.20", 7788)

        self.assertTrue(started)
        listener.start.assert_called_once_with()
        self.assertEqual(subject._last_iprd_error, "")
        subject.set_listen_state.assert_called_once_with(ListenState.CONNECTING)
        subject.stop_listen.assert_not_called()
        subject.notify.assert_not_called()

    def test_reconnect_giveup_preserves_intent_and_controls(self) -> None:
        start_button = Mock()
        stop_button = Mock()
        inactive = Mock()
        subject: Any = SimpleNamespace(
            _iprd_listening=True,
            _last_iprd_error="connection refused",
            _listen_state=ListenState.RECONNECTING,
            lm=SimpleNamespace(count=0, stop=Mock()),
            iprd=SimpleNamespace(stop=Mock()),
            iprd_discovery_timeout=SimpleNamespace(stop=Mock()),
            inactive=inactive,
            pushIPRListenStart=start_button,
            pushIPRListenStop=stop_button,
            checkEnableSysTray=SimpleNamespace(isChecked=lambda: False),
            _update_listen_controls=lambda: IPR._update_listen_controls(subject),
            set_listen_state=lambda state: setattr(subject, "_listen_state", state),
            is_minimized_to_tray=lambda: False,
        )

        IPR.stop_listen(subject, from_giveup=True)

        self.assertTrue(subject._iprd_listening)
        self.assertEqual(subject._listen_state, ListenState.DISCONNECTED)
        start_button.setEnabled.assert_called_once_with(False)
        stop_button.setEnabled.assert_called_once_with(True)
        inactive.stop.assert_not_called()

    def test_disconnected_status_describes_preserved_intent(self) -> None:
        subject: Any = SimpleNamespace(_listen_state=ListenState.DISCONNECTED)

        status = IPR._base_status_text(subject)

        self.assertEqual(
            status, "Status :: IPR Daemon disconnected; listening remains enabled."
        )

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

    def test_sticky_address_survives_advertisement_reordering(self) -> None:
        service = make_service(
            "IPR Daemon._iprd._tcp.local.",
            ("192.168.122.1", "192.168.1.107"),
        )

        address = _select_iprd_service_address(
            service,
            service.name,
            "192.168.1.107",
        )

        self.assertEqual(address, "192.168.1.107")

    def test_sticky_address_falls_back_when_no_longer_advertised(self) -> None:
        service = make_service(
            "IPR Daemon._iprd._tcp.local.",
            ("192.168.122.1",),
        )

        address = _select_iprd_service_address(
            service,
            service.name,
            "192.168.1.107",
        )

        self.assertEqual(address, "192.168.122.1")

    def test_service_update_does_not_interrupt_active_sticky_endpoint(self) -> None:
        service = make_service(
            "IPR Daemon._iprd._tcp.local.",
            ("192.168.122.1", "192.168.1.107"),
        )
        address_field = Mock()
        address_field.text.return_value = "192.168.1.107:7788"
        listener = SimpleNamespace(active=True, stop=Mock())
        subject: Any = SimpleNamespace(
            _discovered_iprd_service_name=service.name,
            _discovered_iprd_address="192.168.1.107",
            _iprd_listening=True,
            lineIPRDSocketAddress=address_field,
            iprd=listener,
            _start_iprd_connection=Mock(),
        )

        IPR._connect_to_iprd_service(subject, service)

        self.assertEqual(subject._discovered_iprd_address, "192.168.1.107")
        address_field.setText.assert_called_once_with("192.168.1.107:7788")
        listener.stop.assert_not_called()
        subject._start_iprd_connection.assert_not_called()

    def test_service_update_reconnects_when_sticky_endpoint_disappears(self) -> None:
        service = make_service(
            "IPR Daemon._iprd._tcp.local.",
            ("192.168.122.1",),
        )
        address_field = Mock()
        address_field.text.return_value = "192.168.1.107:7788"
        listener = SimpleNamespace(active=True, stop=Mock())
        subject: Any = SimpleNamespace(
            _discovered_iprd_service_name=service.name,
            _discovered_iprd_address="192.168.1.107",
            _iprd_listening=True,
            lineIPRDSocketAddress=address_field,
            iprd=listener,
            _start_iprd_connection=Mock(),
        )

        IPR._connect_to_iprd_service(subject, service)

        self.assertEqual(subject._discovered_iprd_address, "192.168.122.1")
        address_field.setText.assert_called_once_with("192.168.122.1:7788")
        listener.stop.assert_called_once_with()
        subject._start_iprd_connection.assert_called_once_with("192.168.122.1", 7788)


if __name__ == "__main__":
    unittest.main()
