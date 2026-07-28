# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""End-to-end tests for the async HTTP miner clients via httpx.MockTransport.

These exercise the full async request -> pydantic model -> dict path (and, for
SRBMiner, feeding the result into its parser) without real network I/O.
"""

import json
import unittest
from pathlib import Path

import httpx

from mod.ipr_asic.data import MinerType
from mod.ipr_asic.data.miners import SRBMinerParser
from mod.ipr_asic.errors import APIError
from mod.ipr_asic.http import (
    AntminerHTTPClient,
    AntminerOldHTTPClient,
    SRBMinerHTTPClient,
)


def read_payload(filename: str) -> dict:
    with open(Path(filename).resolve(), "r") as f:
        return json.load(f)


# a complete Antminer get_system_info payload (all required SystemInfo fields)
ANTMINER_SYSTEM_INFO = {
    "minertype": "Antminer S19j Pro",
    "nettype": "DHCP",
    "netdevice": "eth0",
    "macaddr": "AA:BB:CC:DD:EE:FF",
    "hostname": "antminer",
    "ipaddress": "10.0.0.5",
    "netmask": "255.255.255.0",
    "gateway": "10.0.0.1",
    "dnsservers": "10.0.0.1",
    "system_mode": "GNU/Linux",
    "system_kernel_version": "Linux 4.6",
    "system_filesystem_version": "2023-05-01",
    "serinum": "SER123",
}


class TestAntminerClient(unittest.IsolatedAsyncioTestCase):
    async def test_get_system_info_request_and_parse(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("cgi-bin/get_system_info.cgi"))
            return httpx.Response(200, json=ANTMINER_SYSTEM_INFO)

        client = AntminerHTTPClient("127.0.0.1", transport=httpx.MockTransport(handler))
        client.authed = True  # bypass the digest handshake for a transport-only test
        info = await client.get_system_info()
        self.assertEqual(info["hostname"], "antminer")
        self.assertEqual(info["macaddr"], "AA:BB:CC:DD:EE:FF")
        self.assertEqual(info["serinum"], "SER123")

    async def test_update_passwd_posts_expected_json_payload(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertTrue(request.url.path.endswith("cgi-bin/passwd.cgi"))
            self.assertEqual(
                json.loads(request.content),
                {
                    "curPwd": "old-secret",
                    "newPwd": "new-secret",
                    "confirmPwd": "new-secret",
                },
            )
            return httpx.Response(
                200,
                json={
                    "stats": "success",
                    "status": "success",
                    "code": "0",
                    "msg": "OK",
                },
            )

        client = AntminerHTTPClient("127.0.0.1", transport=httpx.MockTransport(handler))
        client.authed = True

        result = await client.update_passwd("old-secret", "new-secret")

        self.assertEqual(
            result,
            {
                "stats": "success",
                "status": "success",
                "code": "0",
                "msg": "OK",
            },
        )

    async def test_update_passwd_rejects_failed_action_response(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "stats": "fail",
                    "status": "fail",
                    "code": "1",
                    "msg": "FAIL!",
                },
            )

        client = AntminerHTTPClient("127.0.0.1", transport=httpx.MockTransport(handler))
        client.authed = True

        with self.assertRaises(APIError):
            await client.update_passwd("old-secret", "new-secret")


class TestAntminerOldClient(unittest.IsolatedAsyncioTestCase):
    async def test_update_passwd_posts_expected_query_params(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "POST")
            self.assertTrue(request.url.path.endswith("cgi-bin/passwd.cgi"))
            self.assertEqual(
                dict(request.url.params),
                {
                    "current_pw": "old-secret",
                    "new_pw": "new-secret",
                    "new_pw_ctrl": "new-secret",
                },
            )
            self.assertEqual(request.content, b"")
            return httpx.Response(200, json={"success": True})

        client = AntminerOldHTTPClient(
            "127.0.0.1", transport=httpx.MockTransport(handler)
        )
        client.authed = True

        result = await client.update_passwd("old-secret", "new-secret")

        self.assertEqual(result, {"success": True})


class TestSRBMinerClient(unittest.IsolatedAsyncioTestCase):
    def _client(self, payload):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=payload)

        return SRBMinerHTTPClient("127.0.0.1", transport=httpx.MockTransport(handler))

    async def test_system_info_pools_and_parser(self):
        payload = read_payload("tests/payloads/srbminer.json")
        client = self._client(payload)

        info = await client.get_system_info()
        self.assertEqual(info["rig_name"], "SRBMiner-Multi-Rig")

        pools = await client.pools()
        self.assertTrue(pools)
        self.assertEqual(pools[0]["url"], payload["algorithms"][0]["pool"]["pool"])

        # the async client output feeds the (sync) parser unchanged
        parser = SRBMinerParser()
        parser.parse_all(info)
        parser.parse_uptime(info)
        parser.parse_pools(pools)
        data = parser.get_data()
        self.assertEqual(data["type"], str(MinerType.HIVEGPU))
        self.assertEqual(data["hostname"], "SRBMiner-Multi-Rig")

    async def test_blink_unsupported(self):
        client = self._client(read_payload("tests/payloads/srbminer.json"))
        with self.assertRaises(APIError):
            await client.blink(True)


if __name__ == "__main__":
    unittest.main()
