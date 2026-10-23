# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import sys
import unittest

from PySide6.QtCore import QCoreApplication

from mod.networkmonitor import (
    NetworkAddress,
    NetworkMonitor,
    NetworkSnapshot,
    build_network_snapshot,
)

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


def address(
    interface: str,
    host: str,
    prefix_length: int = 24,
    *,
    lan: bool = True,
) -> NetworkAddress:
    return NetworkAddress(
        interface=interface,
        address=host,
        prefix_length=prefix_length,
        lan=lan,
    )


class SnapshotProvider:
    def __init__(self, snapshots: list[NetworkSnapshot]) -> None:
        self.snapshots: list[NetworkSnapshot] = snapshots
        self.calls: int = 0

    def __call__(self) -> NetworkSnapshot:
        snapshot = self.snapshots[min(self.calls, len(self.snapshots) - 1)]
        self.calls += 1
        return snapshot


class TestNetworkSnapshot(unittest.TestCase):
    def test_fingerprint_is_stable_across_input_order_and_duplicates(self) -> None:
        ethernet = address("eth0", "192.168.1.20")
        wifi = address("wlan0", "10.0.0.8")

        first = build_network_snapshot((ethernet, wifi, ethernet))
        second = build_network_snapshot((wifi, ethernet))

        self.assertEqual(first, second)
        self.assertEqual(
            tuple(item.interface for item in first.addresses),
            ("eth0", "wlan0"),
        )
        self.assertTrue(first.available)
        self.assertTrue(first.usable)
        self.assertTrue(first.fingerprint)

    def test_link_local_only_snapshot_is_available_but_not_usable(self) -> None:
        snapshot = build_network_snapshot(
            (
                address("eth0", "169.254.10.20", 16),
                address("eth0", "fe80::1234%eth0", 64),
            )
        )

        self.assertTrue(snapshot.available)
        self.assertFalse(snapshot.usable)

    def test_vpn_only_is_available_but_not_usable_for_iprd(self) -> None:
        snapshot = build_network_snapshot((address("tun0", "10.8.0.2", lan=False),))

        self.assertTrue(snapshot.available)
        self.assertFalse(snapshot.usable)
        self.assertEqual(snapshot.fingerprint, "")
        self.assertEqual(snapshot.addresses, ())

    def test_adding_vpn_does_not_change_lan_snapshot(self) -> None:
        ethernet = address("eth0", "192.168.1.20")
        without_vpn = build_network_snapshot((ethernet,))
        with_vpn = build_network_snapshot(
            (ethernet, address("tun0", "10.8.0.2", lan=False))
        )

        self.assertEqual(with_vpn, without_vpn)

    def test_usable_address_changes_link_local_fingerprint(self) -> None:
        transitional = build_network_snapshot((address("wlan0", "169.254.10.20", 16),))
        configured = build_network_snapshot((address("wlan0", "192.168.1.20", 24),))

        self.assertNotEqual(transitional.fingerprint, configured.fingerprint)
        self.assertFalse(transitional.usable)
        self.assertTrue(configured.usable)

    def test_loopback_unspecified_and_invalid_prefixes_are_excluded(self) -> None:
        snapshot = build_network_snapshot(
            (
                address("lo", "127.0.0.1", 8),
                address("eth0", "0.0.0.0", 0),
                address("eth0", "192.168.1.20", 64),
            )
        )

        self.assertEqual(snapshot, NetworkSnapshot())


class TestNetworkMonitor(unittest.TestCase):
    def test_start_emits_initial_snapshot_and_tracks_material_changes(self) -> None:
        first = build_network_snapshot((address("eth0", "192.168.1.20"),))
        second = build_network_snapshot((address("eth0", "192.168.2.20"),))
        provider = SnapshotProvider([first, first, second])
        monitor = NetworkMonitor(snapshot_provider=provider)
        updates: list[tuple[NetworkSnapshot, bool]] = []
        changes: list[NetworkSnapshot] = []
        monitor.snapshot_updated.connect(
            lambda snapshot, changed: updates.append((snapshot, changed))
        )
        monitor.network_changed.connect(changes.append)

        monitor.start()
        monitor.refresh()
        monitor.refresh()
        monitor.stop()

        self.assertEqual(updates, [(first, True), (first, False), (second, True)])
        self.assertEqual(changes, [first, second])
        self.assertEqual(monitor.snapshot, second)
        self.assertEqual(monitor.generation, 2)
        self.assertFalse(monitor.active)
        self.assertFalse(monitor.initialized)

    def test_provider_error_preserves_last_snapshot(self) -> None:
        expected = build_network_snapshot((address("eth0", "192.168.1.20"),))
        calls = 0

        def provider() -> NetworkSnapshot:
            nonlocal calls
            calls += 1
            if calls == 1:
                return expected
            raise RuntimeError("inventory unavailable")

        monitor = NetworkMonitor(snapshot_provider=provider)
        errors: list[str] = []
        monitor.error.connect(errors.append)

        monitor.start()
        monitor.refresh()
        monitor.stop()

        self.assertEqual(monitor.snapshot, expected)
        self.assertEqual(monitor.generation, 1)
        self.assertEqual(
            errors,
            ["Failed to inspect local network interfaces: inventory unavailable"],
        )

    def test_start_and_stop_are_idempotent(self) -> None:
        provider = SnapshotProvider([NetworkSnapshot()])
        monitor = NetworkMonitor(snapshot_provider=provider)
        active: list[bool] = []
        monitor.active_changed.connect(active.append)

        monitor.start()
        monitor.start()
        monitor.stop()
        monitor.stop()

        self.assertEqual(provider.calls, 1)
        self.assertEqual(active, [True, False])

    def test_poll_interval_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "poll_interval_ms must be positive"):
            NetworkMonitor(poll_interval_ms=0)


if __name__ == "__main__":
    unittest.main()
