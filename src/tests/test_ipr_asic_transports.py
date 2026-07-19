# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Transport-layer tests for the async ipr_asic protocol clients.

HTTP is exercised via httpx.MockTransport; JSON-RPC and the length-prefixed V3
TCP transport are exercised against ephemeral asyncio servers. All stay on the
stdlib unittest runner via IsolatedAsyncioTestCase.
"""

import asyncio
import json
import struct
import unittest
from string import Template

import httpx

from mod.ipr_asic.errors import APIError, FailedConnectionError
from mod.ipr_asic.protocol import BaseHTTPClient, BaseRPCClient, BaseTCPClient


class _HTTPClient(BaseHTTPClient):
    """Minimal concrete HTTP client for transport testing.

    Only the transport plumbing (send_command/_do_http) is under test here, so
    the abstract op surface is filled with trivial stubs to make the class
    concrete.
    """

    def __init__(self, ip, transport):
        super().__init__(ip, transport=transport)
        self.command_path = Template("api/${command}")
        self.authed = True  # bypass auth for transport-only tests

    async def authenticate(self) -> None:
        self.authed = True

    async def get_hostname(self) -> str:
        return ""

    async def get_mac_addr(self) -> str:
        return ""

    async def get_api_version(self) -> str:
        return ""

    async def get_system_info(self) -> dict:
        return {}

    async def get_network_info(self) -> dict:
        return {}

    async def log(self, *args, **kwargs) -> dict:
        return {}

    async def summary(self) -> dict:
        return {}

    async def get_miner_conf(self) -> dict:
        return {}

    async def set_miner_conf(self, *args, **kwargs) -> dict:
        return {}

    async def pools(self) -> list[dict]:
        return []

    async def get_pool_conf(self) -> list[dict]:
        return []

    async def get_miner_status(self) -> dict:
        return {}

    async def get_blink_status(self) -> dict:
        return {}

    async def blink(self, enabled: bool, *args, **kwargs) -> dict:
        return {}

    async def set_miner_mode(self, *args, **kwargs) -> dict:
        return {}

    async def start(self) -> dict:
        return {}

    async def stop(self) -> dict:
        return {}

    async def restart(self) -> dict:
        return {}

    async def reboot(self) -> dict:
        return {}

    async def update_pool_conf(self, urls, users, passwds) -> dict:
        return {}


class _RPCClient(BaseRPCClient):
    pass


class _TCPClient(BaseTCPClient):
    pass


class TestHTTPTransport(unittest.IsolatedAsyncioTestCase):
    def _client(self, handler):
        return _HTTPClient("127.0.0.1", transport=httpx.MockTransport(handler))

    async def test_json_response(self):
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertTrue(request.url.path.endswith("/api/status"))
            return httpx.Response(200, json={"ok": True, "val": 7})

        client = self._client(handler)
        resp = await client.send_command("GET", "status")
        self.assertEqual(resp, {"ok": True, "val": 7})

    async def test_non_json_text_fallback(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"not-json")

        client = self._client(handler)
        resp = await client.send_command("GET", "status")
        self.assertEqual(resp, {"text": "not-json"})

    async def test_http_error_status_raises_apierror(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401)

        client = self._client(handler)
        with self.assertRaises(APIError):
            await client.send_command("GET", "status")

    async def test_timeout_returns_empty(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timed out", request=request)

        client = self._client(handler)
        resp = await client.send_command("GET", "status")
        self.assertEqual(resp, {})


class TestRPCLoadApiData(unittest.TestCase):
    """The btminer/bmminer JSON-repair heuristics (sync, ported verbatim)."""

    def setUp(self):
        self.client = _RPCClient("127.0.0.1")

    def test_strips_trailing_null_byte(self):
        self.assertEqual(self.client._load_api_data(b'{"a": 1}\x00'), {"a": 1})

    def test_fixes_trailing_comma(self):
        self.assertEqual(self.client._load_api_data(b'{"a": 1,}'), {"a": 1})

    def test_fixes_whatsminer_list_as_dict(self):
        # whatsminer API v2.0.4 returns error_code as a list of colon-pairs
        # (invalid JSON); the heuristic rewrites the [ ] to { }.
        raw = b'{"error_code":["0":"data"]}'
        self.assertEqual(self.client._load_api_data(raw), {"error_code": {"0": "data"}})

    def test_fixes_bmminer_missing_comma_between_objects(self):
        # "}{" between two objects in an array becomes "},{"
        self.assertEqual(
            self.client._load_api_data(b'{"a": [{"x": 1}{"y": 2}]}'),
            {"a": [{"x": 1}, {"y": 2}]},
        )

    def test_invalid_json_raises(self):
        with self.assertRaises(APIError):
            self.client._load_api_data(b"totally not json")


class _RPCServer:
    """Ephemeral asyncio server that writes canned bytes then closes."""

    def __init__(self, payload: bytes):
        self.payload = payload
        self.server = None

    async def __aenter__(self):
        async def handle(reader, writer):
            # consume the client's request before responding (avoids RST)
            await reader.read(4096)
            writer.write(self.payload)
            await writer.drain()
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

        self.server = await asyncio.start_server(handle, "127.0.0.1", 0)
        self.host, self.port = self.server.sockets[0].getsockname()[:2]
        return self

    async def __aexit__(self, *exc):
        self.server.close()
        await self.server.wait_closed()


class TestRPCTransport(unittest.IsolatedAsyncioTestCase):
    async def test_send_command_roundtrip(self):
        payload = json.dumps({"STATUS": [{"STATUS": "S"}], "id": 1}).encode()
        async with _RPCServer(payload) as srv:
            client = _RPCClient(srv.host, port=srv.port)
            resp = await client.send_command("summary")
            self.assertEqual(resp["id"], 1)

    async def test_connection_refused_message(self):
        async with _RPCServer(b"Socket connect failed: Connection refused\n") as srv:
            client = _RPCClient(srv.host, port=srv.port)
            with self.assertRaises(APIError):
                await client.send_command("summary")

    async def test_connect_failure_raises(self):
        # nothing is listening on this port
        client = _RPCClient("127.0.0.1", port=1)
        client._timeout = 1.0
        with self.assertRaises(FailedConnectionError):
            await client.send_command("summary")


class _TCPServer:
    """Ephemeral asyncio server for the V3 length-prefixed framing."""

    def __init__(self, frame: bytes):
        self.frame = frame
        self.server = None

    async def __aenter__(self):
        async def handle(reader, writer):
            # consume the client's request frame before responding (avoids RST)
            await reader.read(4096)
            writer.write(self.frame)
            await writer.drain()
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

        self.server = await asyncio.start_server(handle, "127.0.0.1", 0)
        self.host, self.port = self.server.sockets[0].getsockname()[:2]
        return self

    async def __aexit__(self, *exc):
        self.server.close()
        await self.server.wait_closed()


def _v3_frame(obj: dict) -> bytes:
    body = json.dumps(obj).encode()
    return struct.pack("<I", len(body)) + body


class TestTCPTransport(unittest.IsolatedAsyncioTestCase):
    async def test_btv3_roundtrip(self):
        frame = _v3_frame({"code": 0, "msg": {"salt": "abc"}})
        async with _TCPServer(frame) as srv:
            client = _TCPClient(srv.host, port=srv.port)
            msg = "get.device.info"
            resp = await client.btv3_send(msg, len(msg))
            self.assertEqual(resp["code"], 0)
            self.assertEqual(resp["msg"]["salt"], "abc")
            client._close()

    async def test_oversized_length_raises(self):
        # advertise a body length above the 8192 cap
        frame = struct.pack("<I", 99999) + b"xxxx"
        async with _TCPServer(frame) as srv:
            client = _TCPClient(srv.host, port=srv.port)
            with self.assertRaises(APIError):
                await client.btv3_send("x", 1)
            client._close()


if __name__ == "__main__":
    unittest.main()
