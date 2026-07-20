# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for the async ASICClient facade.

Client creation is stubbed (via _make_client) so the facade's dispatch,
result handling, identify branching, and locate flow can be verified without
real network I/O; the SRBMiner path additionally runs a real client over
httpx.MockTransport to exercise the parser dispatch end-to-end.
"""

import json
import unittest
from pathlib import Path

import httpx

from mod.ipr_asic import ASICClient, MinerType
from mod.ipr_asic.errors import APIError, UnknownClientError
from mod.ipr_asic.http import SRBMinerHTTPClient
from mod.lm.ipreport import MinerTypeHint


def read_payload(filename: str) -> dict:
    with open(Path(filename).resolve(), "r") as f:
        return json.load(f)


class _FakeClient:
    """Stand-in client for facade operations that don't need a real transport."""

    def __init__(self, **behaviours):
        self._behaviours = behaviours
        self.closed = False
        self.blinks: list[bool] = []
        self.controls: list[str] = []
        self._ex = None

    def error(self):
        return self._ex

    def _close(self, ex=None):
        self.closed = True
        if ex:
            self._ex = ex

    async def get_pool_conf(self):
        if "pool_conf" in self._behaviours:
            return self._behaviours["pool_conf"]
        raise self._behaviours.get("error", APIError("boom"))

    async def update_pool_conf(self, urls, users, passwds):
        if "update_error" in self._behaviours:
            raise self._behaviours["update_error"]
        return {"success": True}

    async def blink(self, enabled: bool, *a, **k):
        self.blinks.append(enabled)
        return {}

    async def _control(self, action: str):
        self.controls.append(action)
        error = self._behaviours.get(f"{action}_error")
        if error is not None:
            raise error
        return {"action": action}

    async def start(self):
        return await self._control("start")

    async def stop(self):
        return await self._control("stop")

    async def restart(self):
        return await self._control("restart")

    async def reboot(self):
        return await self._control("reboot")


class TestIdentify(unittest.IsolatedAsyncioTestCase):
    async def test_port_hint_maps_directly(self):
        asic = ASICClient()
        self.assertEqual(
            await asic.identify(MinerTypeHint.GOLDSHELL, "1.2.3.4"),
            MinerType.GOLDSHELL,
        )

    async def test_common_hint_uses_http_probe(self):
        asic = ASICClient()

        async def fake_probe(ip):
            return MinerType.ANTMINER

        asic._parse_http_type = fake_probe
        self.assertEqual(
            await asic.identify(MinerTypeHint.COMMON, "1.2.3.4"), MinerType.ANTMINER
        )

    async def test_common_hint_disambiguates_hammer_vs_volcminer(self):
        asic = ASICClient()

        async def fake_probe(ip):
            return MinerType.HAMMER

        async def fake_model(ip):
            return "VolcMiner D1"

        asic._parse_http_type = fake_probe
        asic._get_volcminer_model = fake_model
        self.assertEqual(
            await asic.identify(MinerTypeHint.COMMON, "1.2.3.4"), MinerType.VOLCMINER
        )

    async def test_unknown_hint(self):
        asic = ASICClient()
        self.assertEqual(
            await asic.identify(MinerTypeHint.UNKNOWN, "1.2.3.4"), MinerType.UNKNOWN
        )


class TestGetMinerData(unittest.IsolatedAsyncioTestCase):
    async def test_srbminer_end_to_end(self):
        payload = read_payload("tests/payloads/srbminer.json")
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
        asic = ASICClient()

        async def fake_make(miner_type, ip, alt_pwd=None):
            return SRBMinerHTTPClient(ip, transport=transport)

        asic._make_client = fake_make
        result = await asic.get_miner_data(MinerType.HIVEGPU, "10.0.0.1")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["type"], str(MinerType.HIVEGPU))
        self.assertEqual(result.data["hostname"], "SRBMiner-Multi-Rig")
        self.assertEqual(result.data["subtype"], "4x RTX 3070")

    async def test_unknown_client_returns_error_result(self):
        asic = ASICClient()
        result = await asic.get_miner_data(MinerType.IPOLLO, "10.0.0.1")
        self.assertFalse(result.ok)
        self.assertIsInstance(result.error, UnknownClientError)
        # still returns a filled MinerData dict
        self.assertEqual(result.data["type"], "N/A")


class TestPoolConf(unittest.IsolatedAsyncioTestCase):
    async def test_get_pool_conf_padded_to_three(self):
        asic = ASICClient()
        client = _FakeClient(pool_conf=[{"url": "u1", "user": "acct", "pass": "x"}])

        async def fake_make(miner_type, ip, alt_pwd=None):
            return client

        asic._make_client = fake_make
        result = await asic.get_miner_pool_conf(MinerType.ANTMINER, "10.0.0.1")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data.urls), 3)
        self.assertEqual(result.data.urls[0], "u1")
        self.assertEqual(result.data.urls[1], "")
        self.assertTrue(client.closed)

    async def test_get_pool_conf_error_captured(self):
        asic = ASICClient()
        client = _FakeClient(error=APIError("down"))

        async def fake_make(miner_type, ip, alt_pwd=None):
            return client

        asic._make_client = fake_make
        result = await asic.get_miner_pool_conf(MinerType.ANTMINER, "10.0.0.1")
        self.assertFalse(result.ok)
        self.assertIsInstance(result.error, APIError)

    async def test_update_pools_success(self):
        asic = ASICClient()
        client = _FakeClient()

        async def fake_make(miner_type, ip, alt_pwd=None):
            return client

        asic._make_client = fake_make
        result = await asic.update_miner_pools(
            MinerType.ANTMINER, "10.0.0.1", ["u"] * 3, ["w"] * 3, ["p"] * 3
        )
        self.assertTrue(result.ok)
        self.assertTrue(client.closed)


class TestMinerControl(unittest.IsolatedAsyncioTestCase):
    async def test_control_methods_dispatch_and_close_client(self):
        asic = ASICClient()

        for action in ("start", "stop", "restart", "reboot"):
            with self.subTest(action=action):
                client = _FakeClient()

                async def fake_make(miner_type, ip, alt_pwd=None):
                    return client

                asic._make_client = fake_make
                operation = getattr(asic, f"{action}_miner")
                result = await operation(MinerType.ANTMINER, "10.0.0.1")

                self.assertTrue(result.ok)
                self.assertEqual(result.data, {"action": action})
                self.assertEqual(client.controls, [action])
                self.assertTrue(client.closed)

    async def test_control_error_is_returned_and_client_is_closed(self):
        asic = ASICClient()
        error = APIError("control failed")
        client = _FakeClient(reboot_error=error)

        async def fake_make(miner_type, ip, alt_pwd=None):
            return client

        asic._make_client = fake_make
        result = await asic.reboot_miner(MinerType.ANTMINER, "10.0.0.1")

        self.assertFalse(result.ok)
        self.assertIs(result.error, error)
        self.assertTrue(client.closed)

    async def test_unsupported_control_returns_error_and_closes_client(self):
        asic = ASICClient()
        client = _FakeClient()
        client.start = None

        async def fake_make(miner_type, ip, alt_pwd=None):
            return client

        asic._make_client = fake_make
        result = await asic.start_miner(MinerType.LUX_OS, "10.0.0.1")

        self.assertFalse(result.ok)
        self.assertIsInstance(result.error, NotImplementedError)
        self.assertTrue(client.closed)

    async def test_unknown_client_returns_error_result(self):
        asic = ASICClient()
        result = await asic.start_miner(MinerType.IPOLLO, "10.0.0.1")

        self.assertFalse(result.ok)
        self.assertIsInstance(result.error, UnknownClientError)


class TestLocate(unittest.IsolatedAsyncioTestCase):
    async def test_locate_blinks_on_then_off(self):
        asic = ASICClient()
        client = _FakeClient()

        async def fake_make(miner_type, ip, alt_pwd=None):
            return client

        asic._make_client = fake_make
        result = await asic.locate_miner(MinerType.ANTMINER, "10.0.0.1", duration_ms=1)
        self.assertTrue(result.ok)
        self.assertEqual(client.blinks, [True, False])
        self.assertTrue(client.closed)


if __name__ == "__main__":
    unittest.main()
