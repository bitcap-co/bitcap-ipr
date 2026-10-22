# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import sys
import unittest
from collections.abc import Callable
from typing import cast, final

from PySide6.QtCore import QCoreApplication

from mod.lm.iprd.controller import (
    IPRDController,
    IPRDControllerState,
    IPRDEndpoint,
    IPRDEndpointMode,
    select_best_discovered_endpoint,
)
from mod.lm.iprd.listener import IPRDListener
from mod.lm.iprd.service import IPRDService, IPRDServiceListener
from mod.networkmonitor import (
    NetworkAddress,
    NetworkMonitor,
    NetworkSnapshot,
    build_network_snapshot,
)

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


@final
class FakeSignal:
    def __init__(self) -> None:
        self._slots: list[Callable[..., object]] = []

    def connect(self, slot: Callable[..., object]) -> None:
        self._slots.append(slot)

    def emit(self, *args: object) -> None:
        for slot in tuple(self._slots):
            _ = slot(*args)


@final
class FakeNetworkMonitor:
    def __init__(self, snapshot: NetworkSnapshot) -> None:
        self.snapshot_updated = FakeSignal()
        self.error = FakeSignal()
        self.snapshot = snapshot
        self.active = False
        self.start_calls = 0
        self.stop_calls = 0
        self.refresh_calls = 0

    def start(self) -> None:
        self.active = True
        self.start_calls += 1
        self.snapshot_updated.emit(self.snapshot, True)

    def stop(self) -> None:
        self.active = False
        self.stop_calls += 1

    def refresh(self) -> None:
        self.refresh_calls += 1
        self.snapshot_updated.emit(self.snapshot, False)

    def publish(self, snapshot: NetworkSnapshot) -> None:
        changed = snapshot != self.snapshot
        self.snapshot = snapshot
        self.snapshot_updated.emit(snapshot, changed)

    def close(self) -> None:
        self.stop()


@final
class FakeDiscovery:
    def __init__(self) -> None:
        self.service_found = FakeSignal()
        self.service_updated = FakeSignal()
        self.service_removed = FakeSignal()
        self.error = FakeSignal()
        self.active = False
        self.start_calls = 0
        self.stop_calls = 0

    def start(self) -> None:
        self.active = True
        self.start_calls += 1

    def stop(self) -> None:
        self.active = False
        self.stop_calls += 1

    def close(self) -> None:
        self.stop()


@final
class FakeListener:
    def __init__(self) -> None:
        self.subscribed = FakeSignal()
        self.result = FakeSignal()
        self.error = FakeSignal()
        self.active = False
        self.host = ""
        self.port = 7788
        self.start_calls = 0
        self.stop_calls = 0

    def set_socket_addr(self, host: str, port: int) -> bool:
        self.host = host
        self.port = port
        return bool(host) and 1 <= port <= 65535

    def start(self) -> None:
        self.active = True
        self.start_calls += 1

    def stop(self) -> None:
        self.active = False
        self.stop_calls += 1

    def close(self) -> None:
        self.stop()


def snapshot(interface: str, host: str, prefix: int = 24) -> NetworkSnapshot:
    return snapshots((interface, host, prefix))


def snapshots(*entries: tuple[str, str, int]) -> NetworkSnapshot:
    return build_network_snapshot(
        NetworkAddress(interface=interface, address=host, prefix_length=prefix)
        for interface, host, prefix in entries
    )


def service(name: str, *addresses: str) -> IPRDService:
    return IPRDService(
        name=name,
        instance_name=name,
        hostname=f"{name}.local",
        addresses=addresses,
        port=7788,
        properties={},
    )


@final
class ControllerHarness:
    def __init__(self, initial_snapshot: NetworkSnapshot) -> None:
        self.network = FakeNetworkMonitor(initial_snapshot)
        self.discovery = FakeDiscovery()
        self.listener = FakeListener()
        self.controller = IPRDController(
            listener=cast(IPRDListener, cast(object, self.listener)),
            discovery=cast(IPRDServiceListener, cast(object, self.discovery)),
            network_monitor=cast(NetworkMonitor, cast(object, self.network)),
        )


class TestEndpointSelection(unittest.TestCase):
    def test_prefers_service_address_on_directly_attached_subnet(self) -> None:
        current_network = snapshot("eth0", "192.168.1.50")
        remote = service("a-remote", "10.0.0.20")
        direct = service("z-direct", "192.168.1.20", "172.16.0.20")

        endpoint = select_best_discovered_endpoint((remote, direct), current_network)

        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.host, "192.168.1.20")
        self.assertEqual(endpoint.service_name, "z-direct")

    def test_preserves_current_endpoint_among_equally_ranked_candidates(self) -> None:
        current_network = snapshot("eth0", "192.168.1.50")
        first = service("a", "192.168.1.10")
        selected = service("z", "192.168.1.20")
        current = IPRDEndpoint(
            host="192.168.1.20",
            port=7788,
            mode=IPRDEndpointMode.DISCOVERED,
            service_name="z",
            network_fingerprint="old",
        )

        endpoint = select_best_discovered_endpoint(
            (first, selected), current_network, current
        )

        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.host, current.host)
        self.assertEqual(endpoint.service_name, current.service_name)
        self.assertEqual(endpoint.network_fingerprint, current_network.fingerprint)


class TestIPRDController(unittest.TestCase):
    def test_auto_mode_starts_discovery_on_usable_network(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))

        harness.controller.start_discovery()

        self.assertTrue(harness.controller.listening)
        self.assertEqual(harness.controller.state, IPRDControllerState.DISCOVERING)
        self.assertEqual(harness.discovery.start_calls, 1)
        self.assertEqual(harness.listener.start_calls, 0)

    def test_explicit_mode_change_reapplies_policy_on_same_network(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        harness.controller.start_discovery()

        harness.controller.start_manual("192.168.1.20", 7788)

        endpoint = harness.controller.endpoint
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.mode, IPRDEndpointMode.MANUAL)
        self.assertEqual(harness.listener.host, "192.168.1.20")
        self.assertEqual(harness.controller.state, IPRDControllerState.CONNECTING)

    def test_discovered_service_is_internal_and_stops_browser(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        harness.controller.start_discovery()
        discovered = service("iprd", "10.0.0.20", "192.168.1.20")

        harness.discovery.service_found.emit(discovered)
        harness.controller._select_discovered_endpoint()

        endpoint = harness.controller.endpoint
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.host, "192.168.1.20")
        self.assertEqual(endpoint.mode, IPRDEndpointMode.DISCOVERED)
        self.assertEqual(harness.listener.host, "192.168.1.20")
        self.assertEqual(harness.controller.state, IPRDControllerState.CONNECTING)
        self.assertFalse(harness.discovery.active)

    def test_manual_endpoint_waits_for_usable_network(self) -> None:
        link_local = snapshot("eth0", "169.254.10.20", 16)
        harness = ControllerHarness(link_local)

        harness.controller.start_manual("192.168.1.20", 7788)

        self.assertEqual(
            harness.controller.state, IPRDControllerState.WAITING_FOR_NETWORK
        )
        self.assertEqual(harness.listener.start_calls, 0)
        endpoint = harness.controller.endpoint
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.host, "192.168.1.20")

    def test_added_vpn_interface_keeps_equal_ranked_active_lan_endpoint(self) -> None:
        initial = snapshot("eth0", "192.168.1.50")
        harness = ControllerHarness(initial)
        harness.controller.start_discovery()
        harness.discovery.service_found.emit(
            service("iprd", "192.168.1.20", "10.8.0.20")
        )
        harness.controller._select_discovered_endpoint()
        harness.listener.subscribed.emit()
        stops_before_vpn = harness.listener.stop_calls
        vpn_added = build_network_snapshot(
            (
                NetworkAddress(
                    interface="eth0",
                    address="192.168.1.50",
                    prefix_length=24,
                ),
                NetworkAddress(
                    interface="tun0",
                    address="10.8.0.2",
                    prefix_length=24,
                    lan=False,
                ),
            )
        )

        harness.network.publish(vpn_added)

        endpoint = harness.controller.endpoint
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.host, "192.168.1.20")
        self.assertEqual(harness.listener.stop_calls, stops_before_vpn)
        self.assertEqual(harness.controller.state, IPRDControllerState.CONNECTED)

    def test_local_source_address_change_reconnects_same_preferred_endpoint(
        self,
    ) -> None:
        harness = ControllerHarness(snapshot("wlan0", "192.168.1.50"))
        harness.controller.start_discovery()
        harness.discovery.service_found.emit(service("iprd", "192.168.1.20"))
        harness.controller._select_discovered_endpoint()
        harness.listener.subscribed.emit()
        starts_before_change = harness.listener.start_calls
        changed = snapshot("wlan0", "192.168.1.51")

        harness.network.publish(changed)

        self.assertEqual(
            harness.controller.state, IPRDControllerState.WAITING_FOR_NETWORK
        )
        self.assertFalse(harness.listener.active)
        self.assertIsNotNone(harness.controller.endpoint)

        harness.network.publish(changed)

        endpoint = harness.controller.endpoint
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.host, "192.168.1.20")
        self.assertEqual(endpoint.network_fingerprint, changed.fingerprint)
        self.assertGreater(harness.listener.start_calls, starts_before_change)
        self.assertFalse(harness.discovery.active)
        self.assertEqual(harness.controller.state, IPRDControllerState.CONNECTING)

    def test_same_interface_move_to_different_subnet_rediscovers(self) -> None:
        harness = ControllerHarness(snapshot("wlan0", "192.168.1.50"))
        harness.controller.start_discovery()
        harness.discovery.service_found.emit(service("iprd", "192.168.1.20"))
        harness.controller._select_discovered_endpoint()
        harness.listener.subscribed.emit()
        changed = snapshot("wlan0", "10.0.0.50")

        harness.network.publish(changed)
        harness.network.publish(changed)

        self.assertIsNone(harness.controller.endpoint)
        self.assertTrue(harness.discovery.active)
        self.assertEqual(harness.controller.state, IPRDControllerState.DISCOVERING)

    def test_unrelated_ipv6_address_change_retains_active_ipv4_connection(
        self,
    ) -> None:
        initial = snapshots(
            ("wlan0", "192.168.1.50", 24),
            ("wlan0", "fd00::50", 64),
        )
        harness = ControllerHarness(initial)
        harness.controller.start_discovery()
        harness.discovery.service_found.emit(service("iprd", "192.168.1.20"))
        harness.controller._select_discovered_endpoint()
        harness.listener.subscribed.emit()
        stops_before_change = harness.listener.stop_calls
        changed = snapshots(
            ("wlan0", "192.168.1.50", 24),
            ("wlan0", "fd00::51", 64),
        )

        harness.network.publish(changed)

        self.assertEqual(harness.listener.stop_calls, stops_before_change)
        self.assertTrue(harness.listener.active)
        self.assertEqual(harness.controller.state, IPRDControllerState.CONNECTED)

    def test_higher_ranked_candidate_can_replace_active_endpoint(self) -> None:
        initial = snapshot("eth0", "172.16.1.50")
        harness = ControllerHarness(initial)
        harness.controller.start_discovery()
        harness.discovery.service_found.emit(service("a-current", "192.168.1.20"))
        harness.discovery.service_found.emit(service("z-better", "10.8.0.20"))
        harness.controller._select_discovered_endpoint()
        harness.listener.subscribed.emit()
        improved = snapshots(
            ("eth0", "172.16.1.50", 24),
            ("eth1", "10.8.0.2", 24),
        )

        harness.network.publish(improved)

        self.assertEqual(
            harness.controller.state, IPRDControllerState.WAITING_FOR_NETWORK
        )
        self.assertFalse(harness.listener.active)

        harness.network.publish(improved)

        self.assertIsNone(harness.controller.endpoint)
        self.assertEqual(harness.controller.state, IPRDControllerState.DISCOVERING)

    def test_network_change_discards_discovered_endpoint_after_stabilizing(
        self,
    ) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        harness.controller.start_discovery()
        harness.discovery.service_found.emit(service("iprd", "192.168.1.20"))
        harness.controller._select_discovered_endpoint()
        changed = snapshot("wlan0", "10.0.0.50")

        harness.network.publish(changed)

        self.assertIsNotNone(harness.controller.endpoint)
        self.assertEqual(
            harness.controller.state, IPRDControllerState.WAITING_FOR_NETWORK
        )

        harness.network.publish(changed)

        self.assertIsNone(harness.controller.endpoint)
        self.assertEqual(harness.controller.state, IPRDControllerState.DISCOVERING)
        self.assertTrue(harness.discovery.active)

    def test_network_change_retains_manual_endpoint(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        harness.controller.start_manual("192.168.1.20", 7788)
        changed = snapshot("wlan0", "10.0.0.50")
        starts_before_change = harness.listener.start_calls

        harness.network.publish(changed)
        harness.network.publish(changed)

        endpoint = harness.controller.endpoint
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.host, "192.168.1.20")
        self.assertEqual(endpoint.mode, IPRDEndpointMode.MANUAL)
        self.assertGreater(harness.listener.start_calls, starts_before_change)
        self.assertEqual(harness.controller.state, IPRDControllerState.CONNECTING)

    def test_resume_waits_for_two_stable_network_samples(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        harness.controller.start_manual("192.168.1.20", 7788)
        starts_before_suspend = harness.listener.start_calls

        harness.controller.on_suspend()
        harness.controller.on_resume()

        self.assertEqual(
            harness.controller.state, IPRDControllerState.WAITING_FOR_NETWORK
        )
        self.assertEqual(harness.listener.start_calls, starts_before_suspend)

        harness.network.publish(harness.network.snapshot)

        self.assertGreater(harness.listener.start_calls, starts_before_suspend)
        self.assertEqual(harness.controller.state, IPRDControllerState.CONNECTING)

    def test_reconnect_backoff_starts_at_one_second_and_caps_at_thirty(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        retries: list[tuple[int, int]] = []
        harness.controller.reconnecting.connect(
            lambda attempt, delay: retries.append((attempt, delay))
        )
        harness.controller.configure_reconnect(True, 10)
        harness.controller.start_manual("192.168.1.20", 7788)

        for _ in range(7):
            harness.listener.error.emit("ConnectionRefusedError")
            harness.controller._reconnect_timer.stop()
            harness.controller._attempt_reconnect()

        self.assertEqual(
            retries,
            [
                (1, 1000),
                (2, 2000),
                (3, 4000),
                (4, 8000),
                (5, 16000),
                (6, 30000),
                (7, 30000),
            ],
        )

    def test_exhausted_retry_cycle_enters_cooldown(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        cooldowns: list[int] = []
        harness.controller.retry_paused.connect(cooldowns.append)
        harness.controller.configure_reconnect(True, 1)
        harness.controller.start_manual("192.168.1.20", 7788)

        harness.listener.error.emit("ConnectionRefusedError")
        harness.controller._reconnect_timer.stop()
        harness.controller._attempt_reconnect()
        harness.listener.error.emit("ConnectionRefusedError")

        self.assertEqual(cooldowns, [60000])
        self.assertTrue(harness.controller._retry_cooldown_timer.isActive())
        self.assertEqual(harness.controller.state, IPRDControllerState.RETRYING)

    def test_cooldown_starts_a_new_retry_cycle(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        retries: list[tuple[int, int]] = []
        harness.controller.reconnecting.connect(
            lambda attempt, delay: retries.append((attempt, delay))
        )
        harness.controller.configure_reconnect(True, 1)
        harness.controller.start_manual("192.168.1.20", 7788)
        harness.listener.error.emit("ConnectionRefusedError")
        harness.controller._reconnect_timer.stop()
        harness.controller._attempt_reconnect()
        harness.listener.error.emit("ConnectionRefusedError")
        harness.controller._retry_cooldown_timer.stop()

        harness.controller._restart_retry_cycle()

        self.assertEqual(retries, [(1, 1000), (1, 1000)])
        self.assertTrue(harness.controller._reconnect_timer.isActive())

    def test_successful_subscription_resets_retry_cycle(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        connection_errors: list[str] = []
        retries: list[tuple[int, int]] = []
        harness.controller.connection_error.connect(connection_errors.append)
        harness.controller.reconnecting.connect(
            lambda attempt, delay: retries.append((attempt, delay))
        )
        harness.controller.start_manual("192.168.1.20", 7788)
        harness.listener.error.emit("ConnectionRefusedError")

        harness.listener.subscribed.emit()
        harness.listener.error.emit("RemoteHostClosedError")

        self.assertEqual(
            connection_errors,
            ["ConnectionRefusedError", "RemoteHostClosedError"],
        )
        self.assertEqual(retries, [(1, 1000), (1, 1000)])
        self.assertEqual(harness.controller._reconnect_attempts, 1)

    def test_stop_and_suspend_cancel_retry_timers(self) -> None:
        for action in ("stop", "suspend"):
            with self.subTest(action=action):
                harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
                harness.controller.start_manual("192.168.1.20", 7788)
                harness.listener.error.emit("ConnectionRefusedError")
                harness.controller._retry_cooldown_timer.start(60000)

                if action == "stop":
                    harness.controller.stop()
                else:
                    harness.controller.on_suspend()

                self.assertFalse(harness.controller._reconnect_timer.isActive())
                self.assertFalse(harness.controller._retry_cooldown_timer.isActive())
                self.assertFalse(harness.listener.active)

    def test_auto_reconnect_disabled_only_emits_connection_error(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        connection_errors: list[str] = []
        harness.controller.connection_error.connect(connection_errors.append)
        harness.controller.configure_reconnect(False, 3)
        harness.controller.start_manual("192.168.1.20", 7788)

        harness.listener.error.emit("ConnectionRefusedError")

        self.assertEqual(connection_errors, ["ConnectionRefusedError"])
        self.assertFalse(harness.controller._reconnect_timer.isActive())
        self.assertFalse(harness.controller._retry_cooldown_timer.isActive())

    def test_connection_error_is_emitted_once_while_retries_continue(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        connection_errors: list[str] = []
        retries: list[tuple[int, int]] = []
        harness.controller.connection_error.connect(connection_errors.append)
        harness.controller.reconnecting.connect(
            lambda attempt, delay: retries.append((attempt, delay))
        )
        harness.controller.start_manual("192.168.1.20", 7788)

        harness.listener.error.emit("ConnectionRefusedError")
        harness.controller._reconnect_timer.stop()
        harness.controller._attempt_reconnect()
        harness.listener.error.emit("ConnectionRefusedError")

        self.assertEqual(connection_errors, ["ConnectionRefusedError"])
        self.assertEqual(retries, [(1, 1000), (2, 2000)])

    def test_stop_cancels_intent_and_clears_discovered_endpoint(self) -> None:
        harness = ControllerHarness(snapshot("eth0", "192.168.1.50"))
        harness.controller.start_discovery()
        harness.discovery.service_found.emit(service("iprd", "192.168.1.20"))
        harness.controller._select_discovered_endpoint()

        harness.controller.stop()

        self.assertFalse(harness.controller.listening)
        self.assertIsNone(harness.controller.endpoint)
        self.assertEqual(harness.controller.state, IPRDControllerState.STOPPED)
        self.assertFalse(harness.network.active)


if __name__ == "__main__":
    unittest.main()
