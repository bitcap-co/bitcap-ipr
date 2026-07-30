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
from mod.ipr_asic.http.ipollo import IPolloHTTPClient


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


class TestIPolloClient(unittest.IsolatedAsyncioTestCase):
    async def test_get_miner_conf_parses_luci_html(self):
        html = """
        <form>
          <select id="cbid.cgminer.default.show_fan" name="cbid.cgminer.default.show_fan">
            <option value="fan1">Fan 1</option>
            <option value="fan3" selected="selected">Fan 3</option>
          </select>
          <select id="cbid.cgminer.default.show_temp" name="cbid.cgminer.default.show_temp">
            <option value="temp2" selected="selected">Temp 2</option>
          </select>
          <input name="cbid.cgminer.default.asic_alarm_temp" value="90">
          <input name="cbid.cgminer.default.fan_min" value="60">
          <input name="cbid.cgminer.default.fan_max" value="100">
          <input name="cbid.cgminer.default.pwm_default" value="60">
          <select name="cbid.cgminer.default.fan_ctrl">
            <option value="1" selected>Enabled</option>
            <option value="0">Disabled</option>
          </select>
          <select name="cbid.cgminer.default.pre_boot_time">
            <option value="3" selected="selected">3</option>
          </select>
          <input name="cbid.cgminer.default.pre_boot_fan" value="100">
          <input name="unrelated.field" value="ignored">
        </form>
        """

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertTrue(
                request.url.path.endswith("cgi-bin/luci/admin/ipollo_main/normal")
            )
            return httpx.Response(200, text=html)

        client = IPolloHTTPClient("127.0.0.1", transport=httpx.MockTransport(handler))
        client.authed = True

        config = await client.get_miner_conf()

        self.assertEqual(config["show_fan"], "fan3")
        self.assertEqual(config["show_temp"], "temp2")
        self.assertEqual(config["alarm_temp"], 90)
        self.assertEqual(config["fan_min"], 60)
        self.assertEqual(config["fan_max"], 100)
        self.assertEqual(config["default_pwm"], 60)
        self.assertEqual(config["fan_ctrl"], 1)
        self.assertEqual(config["pre_boot_time"], 3)
        self.assertEqual(config["pre_boot_fan"], 100)

    async def test_get_pool_conf_returns_selected_coin_pools(self):
        html = """
        <form>
          <select name="cbid.cgminer.default.select_coin">
            <option value="mwc">MWC</option>
            <option value="grin" selected="selected">Grin</option>
          </select>
          <input name="cbid.cgminer.default.mwc_pool1url" value="mwc.example:1">
          <input name="cbid.cgminer.default.mwc_pool1user" value="mwc-user">
          <input name="cbid.cgminer.default.mwc_pool1pw" value="mwc-pass">
          <input name="cbid.cgminer.default.grin_pool1url" value="grin.example:1">
          <input name="cbid.cgminer.default.grin_pool1user" value="grin-user-1">
          <input name="cbid.cgminer.default.grin_pool1pw" value="grin-pass-1">
          <input name="cbid.cgminer.default.grin_pool2url" value="grin.example:2">
          <input name="cbid.cgminer.default.grin_pool2user" value="grin-user-2">
          <input name="cbid.cgminer.default.grin_pool2pw" value="grin-pass-2">
          <input name="cbid.cgminer.default.grin_pool3url" value="">
          <input name="cbid.cgminer.default.grin_pool3user" value="">
          <input name="cbid.cgminer.default.grin_pool3pw" value="">
        </form>
        """

        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.method, "GET")
            self.assertTrue(
                request.url.path.endswith("cgi-bin/luci/admin/ipollo_main/pool")
            )
            return httpx.Response(200, text=html)

        client = IPolloHTTPClient("127.0.0.1", transport=httpx.MockTransport(handler))
        client.authed = True

        pools = await client.get_pool_conf()

        self.assertEqual(
            pools,
            [
                {
                    "url": "grin.example:1",
                    "user": "grin-user-1",
                    "pass": "grin-pass-1",
                },
                {
                    "url": "grin.example:2",
                    "user": "grin-user-2",
                    "pass": "grin-pass-2",
                },
                {"url": "", "user": "", "pass": ""},
            ],
        )

    async def test_update_pool_conf_posts_active_coin_and_preserves_inactive_coin(self):
        html = """
        <form>
          <select name="cbid.cgminer.default.select_coin">
            <option value="mwc" selected="selected">MWC</option>
            <option value="grin">Grin</option>
          </select>
          <input name="cbid.cgminer.default.mwc_pool1url" value="old-mwc.example">
          <input name="cbid.cgminer.default.mwc_pool1user" value="old-mwc-user">
          <input name="cbid.cgminer.default.mwc_pool1pw" value="old-mwc-pass">
          <input name="cbid.cgminer.default.grin_pool1url" value="grin.example">
          <input name="cbid.cgminer.default.grin_pool1user" value="grin-user">
          <input name="cbid.cgminer.default.grin_pool1pw" value="grin-pass">
        </form>
        """
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            self.assertTrue(
                request.url.path.endswith("cgi-bin/luci/admin/ipollo_main/pool")
            )
            if request.method == "GET":
                return httpx.Response(200, text=html)

            self.assertEqual(request.method, "POST")
            form = dict(httpx.QueryParams(request.content.decode()))
            self.assertEqual(form["cbid.cgminer.default.select_coin"], "mwc")
            self.assertEqual(form["cbid.cgminer.default.mwc_pool1url"], "new.example")
            self.assertEqual(form["cbid.cgminer.default.mwc_pool1user"], "new-user")
            self.assertEqual(form["cbid.cgminer.default.mwc_pool1pw"], "new-pass")
            self.assertEqual(form["cbid.cgminer.default.grin_pool1url"], "grin.example")
            self.assertEqual(form["cbid.cgminer.default.grin_pool1user"], "grin-user")
            self.assertEqual(form["cbid.cgminer.default.grin_pool1pw"], "grin-pass")
            self.assertEqual(form["cbi.apply"], "Save & Apply")
            return httpx.Response(200, text=html)

        client = IPolloHTTPClient("127.0.0.1", transport=httpx.MockTransport(handler))
        client.authed = True

        result = await client.update_pool_conf(
            ["new.example", "", ""],
            ["new-user", "", ""],
            ["new-pass", "", ""],
        )

        self.assertEqual(result, {"success": True, "msg": "OK"})
        self.assertEqual([request.method for request in requests], ["GET", "POST"])


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
