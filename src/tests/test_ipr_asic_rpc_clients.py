# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Tests for the async RPC/TCP miner clients against ephemeral asyncio servers.

CGMiner-family clients speak JSON-RPC (one connection per command); the
Whatsminer V3 client uses the length-prefixed TCP framing. The Whatsminer V2
privileged/crypto path is not mocked here; only its plain read commands are.
"""

import asyncio
import json
import struct
import unittest

from mod.ipr_asic.errors import APIError
from mod.ipr_asic.rpc import (
    CGMinerRPCClient,
    LuxminerRPCClient,
    WhatsminerRPCClient,
    WhatsminerTCPClient,
)


def _status(msg="ok"):
    return {"STATUS": "S", "When": 0, "Code": 0, "Msg": msg, "Description": ""}


def _full_pool():
    return {
        "URL": "stratum+tcp://pool:3333",
        "Status": "Alive",
        "User": "acct.worker",
        "Diff": 1.0,
        "POOL": 0,
        "Priority": 0,
        "Quota": 1,
        "Getworks": 10,
        "Accepted": 100,
        "Rejected": 1,
        "Stale": 0,
        "Difficulty Accepted": 1.0,
        "Difficulty Rejected": 0.0,
        "Stratum Difficulty": 1.0,
        "Stratum Active": True,
    }


class _RPCDispatchServer:
    """JSON-RPC server that maps the request's ``command`` to a canned dict."""

    def __init__(self, responses: dict):
        self.responses = responses
        self.server = None

    async def __aenter__(self):
        async def handle(reader, writer):
            raw = await reader.read(4096)
            try:
                cmd = json.loads(raw.decode())["command"]
            except (json.JSONDecodeError, KeyError):
                cmd = None
            payload = json.dumps(self.responses.get(cmd, {})).encode()
            writer.write(payload)
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


class TestCGMinerClient(unittest.IsolatedAsyncioTestCase):
    async def test_version_summary_pools(self):
        responses = {
            "version": {
                "STATUS": [_status()],
                "VERSION": [{"API": "3.7", "CGMiner": "1.0.0"}],
                "id": 1,
            },
            "summary": {
                "STATUS": [_status()],
                "SUMMARY": [{"MHS av": 12345, "Elapsed": 60}],
                "id": 1,
            },
            "pools": {"STATUS": [_status()], "POOLS": [_full_pool()], "id": 1},
        }
        async with _RPCDispatchServer(responses) as srv:
            client = CGMinerRPCClient(srv.host, port=srv.port)
            version = await client.version()
            self.assertEqual(version["API"], "3.7")

            summary = await client.summary()
            self.assertEqual(summary["Elapsed"], 60)

            pools = await client.pools()
            self.assertEqual(pools[0]["URL"], "stratum+tcp://pool:3333")

    async def test_api_error_status_raises(self):
        responses = {
            "summary": {
                "STATUS": [
                    {
                        "STATUS": "E",
                        "When": 0,
                        "Code": 14,
                        "Msg": "bad",
                        "Description": "err",
                    }
                ],
                "id": 1,
            }
        }
        async with _RPCDispatchServer(responses) as srv:
            client = CGMinerRPCClient(srv.host, port=srv.port)
            with self.assertRaises(APIError):
                await client.summary()


class TestLuxminerClient(unittest.IsolatedAsyncioTestCase):
    async def test_authenticate_session_token(self):
        responses = {
            "session": {
                "STATUS": [_status()],
                "SESSION": [{"SessionID": "tok123"}],
                "id": 1,
            }
        }
        async with _RPCDispatchServer(responses) as srv:
            client = LuxminerRPCClient(srv.host, port=srv.port)
            token = await client.authenticate()
            self.assertEqual(token, "tok123")
            self.assertEqual(client.session_token, "tok123")


class TestWhatsminerV2Client(unittest.IsolatedAsyncioTestCase):
    async def test_version_plain_command(self):
        responses = {
            "get_version": {
                "STATUS": "S",
                "When": 0,
                "Code": 0,
                "Msg": {
                    "api_ver": "2.0.4",
                    "fw_ver": "20240101",
                    "platform": "H6",
                    "chip": "BM1362",
                },
                "Description": "",
            }
        }
        async with _RPCDispatchServer(responses) as srv:
            client = WhatsminerRPCClient(srv.host, port=srv.port)
            version = await client.version()
            self.assertEqual(version["api_ver"], "2.0.4")
            self.assertEqual(version["platform"], "H6")


class _TCPFramedServer:
    """V3 length-prefixed server that returns a canned response frame."""

    def __init__(self, msg_obj: dict, code: int = 0):
        self.frame = self._frame({"code": code, "when": 0, "msg": msg_obj, "desc": "OK"})
        self.server = None

    @staticmethod
    def _frame(obj: dict) -> bytes:
        body = json.dumps(obj).encode()
        return struct.pack("<I", len(body)) + body

    async def __aenter__(self):
        async def handle(reader, writer):
            # V3 keeps the connection open: respond to each request frame until
            # the client disconnects.
            try:
                while True:
                    header = await reader.readexactly(4)
                    size = struct.unpack("<I", header)[0]
                    await reader.readexactly(size)
                    writer.write(self.frame)
                    await writer.drain()
            except (asyncio.IncompleteReadError, ConnectionError):
                pass
            finally:
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


V3_SYSTEM = {
    "system": {
        "api": "3.0",
        "platform": "H6",
        "fwversion": "20250101",
        "control-board-version": "cb1",
        "apiswitch": "on",
        "ledstatus": "auto",
    }
}


class TestWhatsminerV3Client(unittest.IsolatedAsyncioTestCase):
    async def test_get_system_info(self):
        async with _TCPFramedServer(V3_SYSTEM) as srv:
            client = WhatsminerTCPClient(srv.host, port=srv.port)
            info = await client.get_system_info()
            self.assertEqual(info["system"]["api"], "3.0")
            api = await client.get_api_version()
            self.assertEqual(api, "3.0")
            client._close()

    async def test_error_code_raises(self):
        async with _TCPFramedServer({"reason": "nope"}, code=0x14) as srv:
            client = WhatsminerTCPClient(srv.host, port=srv.port)
            with self.assertRaises(APIError):
                await client.get_system_info()
            client._close()


if __name__ == "__main__":
    unittest.main()
