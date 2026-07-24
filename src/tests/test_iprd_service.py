# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import sys
import threading
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication
from zeroconf import ServiceInfo

from mod.lm.iprd.service import (
    IPRD_SERVICE_TYPE,
    IPRDService,
    IPRDServiceListener,
)

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


class FakeServiceInfo(ServiceInfo):
    def __init__(
        self,
        addresses: list[str] | None = None,
        port: int | None = 7788,
        version: str = "0.4.6",
    ) -> None:
        super().__init__(
            IPRD_SERVICE_TYPE,
            f"IPR Daemon on test-host (7788).{IPRD_SERVICE_TYPE}",
            port=port,
            properties={
                "txtvers": "1",
                "protocol": "iprd",
                "subscribe": "iprd_subscribe",
                "version": version,
            },
            server="test-host.local.",
            parsed_addresses=(
                ["fe80::1", "192.168.1.20"] if addresses is None else addresses
            ),
            interface_index=3,
        )


class FakeZeroconf:
    def __init__(self) -> None:
        self.info: FakeServiceInfo | None = FakeServiceInfo()
        self.closed = 0
        self.requests: list[tuple[str, str, int]] = []

    def get_service_info(
        self, type_: str, name: str, timeout: int
    ) -> FakeServiceInfo | None:
        self.requests.append((type_, name, timeout))
        return self.info

    def close(self) -> None:
        self.closed += 1


def wait_for(predicate, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


class BlockingFakeZeroconf(FakeZeroconf):
    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()
        self.completed = threading.Event()

    def get_service_info(
        self, type_: str, name: str, timeout: int
    ) -> FakeServiceInfo | None:
        self.entered.set()
        self.release.wait(timeout=1)
        self.completed.set()
        raise RuntimeError("zeroconf closed")

    def close(self) -> None:
        super().close()
        self.release.set()


class DeferredFakeZeroconf(FakeZeroconf):
    def __init__(self) -> None:
        super().__init__()
        self.first_entered = threading.Event()
        self.release_first = threading.Event()
        self._request_count = 0
        self._request_lock = threading.Lock()

    def get_service_info(
        self, type_: str, name: str, timeout: int
    ) -> FakeServiceInfo | None:
        with self._request_lock:
            self._request_count += 1
            request_number = self._request_count
        info = self.info
        if request_number == 1:
            self.first_entered.set()
            self.release_first.wait(timeout=1)
        return info


class FakeServiceBrowser:
    def __init__(self, zc, type_: str, listener) -> None:
        self.zc = zc
        self.type = type_
        self.listener = listener
        self.cancelled = 0

    def cancel(self) -> None:
        self.cancelled += 1


class TestIPRDService(unittest.TestCase):
    def test_service_model_prefers_ipv4_and_exposes_metadata(self) -> None:
        service = IPRDServiceListener._service_from_info(FakeServiceInfo())

        self.assertEqual(service.address, "192.168.1.20")
        self.assertEqual(service.addresses, ("192.168.1.20", "fe80::1%3"))
        self.assertEqual(service.hostname, "test-host.local")
        self.assertEqual(service.port, 7788)
        self.assertEqual(service.version, "0.4.6")
        self.assertEqual(service.subscribe_command, "iprd_subscribe")

    def test_service_model_rejects_missing_address_and_invalid_port(self) -> None:
        with self.assertRaisesRegex(ValueError, "reachable address"):
            IPRDServiceListener._service_from_info(FakeServiceInfo(addresses=[]))
        with self.assertRaisesRegex(ValueError, "invalid port"):
            IPRDServiceListener._service_from_info(FakeServiceInfo(port=0))

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", FakeZeroconf)
    def test_lifecycle_is_idempotent(self) -> None:
        listener = IPRDServiceListener()
        started: list[bool] = []
        stopped: list[bool] = []
        listener.started.connect(lambda: started.append(True))
        listener.stopped.connect(lambda: stopped.append(True))

        listener.start()
        zeroconf = listener._zeroconf
        browser = listener._browser
        listener.start()

        self.assertTrue(listener.active)
        self.assertEqual(started, [True])
        self.assertIsInstance(zeroconf, FakeZeroconf)
        self.assertIsInstance(browser, FakeServiceBrowser)
        assert isinstance(zeroconf, FakeZeroconf)
        assert isinstance(browser, FakeServiceBrowser)

        listener.stop()
        listener.stop()

        self.assertFalse(listener.active)
        self.assertEqual(stopped, [True])
        self.assertEqual(zeroconf.closed, 1)
        self.assertEqual(browser.cancelled, 1)

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", FakeZeroconf)
    def test_suspend_resume_recreates_active_discovery(self) -> None:
        listener = IPRDServiceListener()
        listener.start()
        old_zeroconf = listener._zeroconf
        old_browser = listener._browser
        assert isinstance(old_zeroconf, FakeZeroconf)
        assert isinstance(old_browser, FakeServiceBrowser)

        listener.on_suspend()

        self.assertFalse(listener.active)
        self.assertEqual(old_browser.cancelled, 1)
        self.assertEqual(old_zeroconf.closed, 1)

        listener.on_resume()

        self.assertTrue(listener.active)
        self.assertIsNot(listener._zeroconf, old_zeroconf)
        self.assertIsNot(listener._browser, old_browser)
        listener.close()

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", FakeZeroconf)
    def test_stop_while_suspended_prevents_resume(self) -> None:
        listener = IPRDServiceListener()
        listener.start()
        listener.on_suspend()

        listener.stop()
        listener.on_resume()

        self.assertFalse(listener.active)
        self.assertIsNone(listener._zeroconf)
        self.assertIsNone(listener._browser)

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", FakeZeroconf)
    def test_start_while_suspended_is_deferred_until_resume(self) -> None:
        listener = IPRDServiceListener()
        listener.on_suspend()

        listener.start()

        self.assertFalse(listener.active)
        self.assertIsNone(listener._zeroconf)
        listener.on_resume()
        self.assertTrue(listener.active)
        listener.close()

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", FakeZeroconf)
    def test_add_update_and_remove_signals(self) -> None:
        listener = IPRDServiceListener(resolve_timeout_ms=1500)
        found: list[IPRDService] = []
        updated: list[IPRDService] = []
        removed: list[str] = []
        listener.service_found.connect(found.append)
        listener.service_updated.connect(updated.append)
        listener.service_removed.connect(removed.append)
        listener.start()

        zeroconf = listener._zeroconf
        assert isinstance(zeroconf, FakeZeroconf)
        assert zeroconf.info is not None
        name = zeroconf.info.name
        listener.add_service(zeroconf, IPRD_SERVICE_TYPE, name)

        self.assertTrue(wait_for(lambda: len(found) == 1))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].address, "192.168.1.20")
        self.assertEqual(
            zeroconf.requests,
            [(IPRD_SERVICE_TYPE, name, 1500)],
        )
        self.assertEqual(listener.get_service(name), found[0])

        zeroconf.info = FakeServiceInfo(addresses=["192.168.1.21"])
        listener.update_service(zeroconf, IPRD_SERVICE_TYPE, name)

        self.assertTrue(wait_for(lambda: len(updated) == 1))
        self.assertEqual(len(updated), 1)
        self.assertEqual(updated[0].address, "192.168.1.21")
        self.assertEqual(listener.services, (updated[0],))

        listener.remove_service(zeroconf, IPRD_SERVICE_TYPE, name)

        self.assertEqual(removed, [name])
        self.assertEqual(listener.services, ())
        listener.close()

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", DeferredFakeZeroconf)
    def test_newer_update_wins_over_inflight_resolution(self) -> None:
        listener = IPRDServiceListener()
        found: list[IPRDService] = []
        updated: list[IPRDService] = []
        listener.service_found.connect(found.append)
        listener.service_updated.connect(updated.append)
        listener.start()

        zeroconf = listener._zeroconf
        assert isinstance(zeroconf, DeferredFakeZeroconf)
        assert zeroconf.info is not None
        name = zeroconf.info.name
        listener.add_service(zeroconf, IPRD_SERVICE_TYPE, name)
        self.assertTrue(zeroconf.first_entered.wait(timeout=1))

        zeroconf.info = FakeServiceInfo(addresses=["192.168.1.99"])
        listener.update_service(zeroconf, IPRD_SERVICE_TYPE, name)
        self.assertTrue(wait_for(lambda: len(found) == 1))
        zeroconf.release_first.set()
        self.assertTrue(wait_for(lambda: len(listener.services) == 1))

        self.assertEqual(found[0].address, "192.168.1.99")
        self.assertEqual(updated, [])
        self.assertEqual(listener.services[0].address, "192.168.1.99")
        listener.close()

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", DeferredFakeZeroconf)
    def test_remove_invalidates_inflight_resolution(self) -> None:
        listener = IPRDServiceListener()
        found: list[IPRDService] = []
        removed: list[str] = []
        listener.service_found.connect(found.append)
        listener.service_removed.connect(removed.append)
        listener.start()

        zeroconf = listener._zeroconf
        assert isinstance(zeroconf, DeferredFakeZeroconf)
        assert zeroconf.info is not None
        name = zeroconf.info.name
        listener.add_service(zeroconf, IPRD_SERVICE_TYPE, name)
        self.assertTrue(zeroconf.first_entered.wait(timeout=1))
        listener.remove_service(zeroconf, IPRD_SERVICE_TYPE, name)
        app.processEvents()
        zeroconf.release_first.set()
        time.sleep(0.01)
        app.processEvents()

        self.assertEqual(found, [])
        self.assertEqual(removed, [])
        self.assertEqual(listener.services, ())
        listener.close()

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", BlockingFakeZeroconf)
    def test_stop_does_not_wait_for_or_report_inflight_resolution(self) -> None:
        listener = IPRDServiceListener()
        errors: list[str] = []
        listener.error.connect(errors.append)
        listener.start()

        zeroconf = listener._zeroconf
        assert isinstance(zeroconf, BlockingFakeZeroconf)
        assert zeroconf.info is not None
        listener.add_service(zeroconf, IPRD_SERVICE_TYPE, zeroconf.info.name)
        self.assertTrue(zeroconf.entered.wait(timeout=1))

        started = time.monotonic()
        listener.stop()
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 0.5)
        self.assertTrue(wait_for(zeroconf.completed.is_set))
        app.processEvents()
        self.assertEqual(errors, [])

    @patch("mod.lm.iprd.service.ServiceBrowser", FakeServiceBrowser)
    @patch("mod.lm.iprd.service.Zeroconf", FakeZeroconf)
    def test_resolution_failure_emits_error(self) -> None:
        listener = IPRDServiceListener()
        errors: list[str] = []
        removed: list[str] = []
        listener.error.connect(errors.append)
        listener.service_removed.connect(removed.append)
        listener.start()

        zeroconf = listener._zeroconf
        assert isinstance(zeroconf, FakeZeroconf)
        zeroconf.info = None
        listener.add_service(
            zeroconf,
            IPRD_SERVICE_TYPE,
            f"missing.{IPRD_SERVICE_TYPE}",
        )

        self.assertTrue(wait_for(lambda: len(errors) == 1))
        self.assertEqual(len(errors), 1)
        self.assertIn("Failed to resolve IPRD service", errors[0])
        listener.remove_service(
            zeroconf,
            IPRD_SERVICE_TYPE,
            f"missing.{IPRD_SERVICE_TYPE}",
        )
        self.assertEqual(removed, [])
        listener.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
