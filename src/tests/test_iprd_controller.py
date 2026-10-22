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
        self.suspend_calls = 0
        self.resume_calls = 0

    def start(self) -> None:
        self.active = True
        self.start_calls += 1

    def stop(self) -> None:
        self.active = False
        self.stop_calls += 1

    def on_suspend(self) -> None:
        self.active = False
        self.suspend_calls += 1

    def on_resume(self) -> None:
        self.resume_calls += 1

    def close(self) -> None:
        self.stop()


@final
class FakeListener:
    def __init__(self) -> None:
        self.subscribed = FakeSignal()
        self.result = FakeSignal()
        self.error = FakeSignal()
        self.reconnecting = FakeSignal()
        self.retry_paused = FakeSignal()
        self.active = False
        self.host = ""
        self.port = 7788
        self.start_calls = 0
        self.stop_calls = 0
        self.suspend_calls = 0
        self.resume_calls = 0

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

    def on_suspend(self) -> None:
        self.active = False
        self.suspend_calls += 1

    def on_resume(self) -> None:
        self.resume_calls += 1

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
        vpn_added = snapshots(
            ("eth0", "192.168.1.50", 24),
            ("tun0", "10.8.0.2", 24),
        )

        harness.network.publish(vpn_added)

        endpoint = harness.controller.endpoint
        self.assertIsNotNone(endpoint)
        assert endpoint is not None
        self.assertEqual(endpoint.host, "192.168.1.20")
        self.assertEqual(harness.listener.stop_calls, stops_before_vpn)
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
            ("tun0", "10.8.0.2", 24),
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
        self.assertEqual(harness.listener.resume_calls, 0)

        harness.network.publish(harness.network.snapshot)

        self.assertEqual(harness.listener.resume_calls, 1)
        self.assertGreater(harness.listener.start_calls, starts_before_suspend)
        self.assertEqual(harness.controller.state, IPRDControllerState.CONNECTING)

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
