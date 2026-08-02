# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import unittest
from typing import cast

from mod.ipr_asic.errors import APIError
from mod.ipr_asic.http import IPolloHTTPClient
from mod.ipr_asic.miners import BaseMiner, IPolloMiner
from mod.ipr_asic.protocol import BaseHTTPClient, BaseRPCClient
from mod.ipr_asic.rpc import CGMinerRPCClient


class _FakeHTTPClient:
    def __init__(self) -> None:
        self.closed = False

    async def get_system_info(self):
        return {"mac": "00:11:22:33:44:55"}

    async def get_miner_status(self):
        return {"status": "mining"}

    def _close(self, ex=None):
        self.closed = True


class _FakeRPCClient:
    def __init__(self) -> None:
        self.closed = False

    async def version(self):
        return {"api": "3.7"}

    async def summary(self):
        return {"hashrate": 100}

    async def stats(self):
        return [{"temperature": 70}]

    async def devs(self):
        return [{"device": 0}]

    async def devdetails(self):
        return [{"model": "hashboard"}]

    async def pools(self):
        return [{"url": "stratum.example"}]

    def _close(self, ex=None):
        self.closed = True


class _FakeIPolloHTTPClient(_FakeHTTPClient):
    async def summary(self):
        return {"algo": "etc", "hashrate": 100, "version": "1.0"}

    async def pools(self):
        return [{"url": "stratum.example", "user": "worker"}]


class TestBaseMiner(unittest.IsolatedAsyncioTestCase):
    async def test_collects_http_and_rpc_data(self):
        miner = BaseMiner(
            "10.0.0.1",
            http=cast(BaseHTTPClient, _FakeHTTPClient()),
            rpc=cast(BaseRPCClient, _FakeRPCClient()),
        )

        snapshot = await miner.collect()

        self.assertTrue(snapshot.ok)
        self.assertIsNotNone(snapshot.http)
        self.assertIsNotNone(snapshot.rpc)
        assert snapshot.http is not None
        assert snapshot.rpc is not None
        self.assertEqual(
            snapshot.http.data["get_system_info"]["mac"],
            "00:11:22:33:44:55",
        )
        self.assertEqual(snapshot.rpc.data["summary"]["hashrate"], 100)
        self.assertEqual(snapshot.errors, {})

    async def test_preserves_partial_results_when_an_endpoint_fails(self):
        class FailingHTTPClient(_FakeHTTPClient):
            async def get_miner_status(self):
                raise APIError("status unavailable")

        miner = BaseMiner("10.0.0.1", http=cast(BaseHTTPClient, FailingHTTPClient()))

        snapshot = await miner.collect()

        self.assertTrue(snapshot.ok)
        self.assertIsNotNone(snapshot.http)
        assert snapshot.http is not None
        self.assertTrue(snapshot.http.partial)
        self.assertIn("get_system_info", snapshot.http.data)
        self.assertIsInstance(snapshot.errors["http.get_miner_status"], APIError)
        self.assertIsNone(snapshot.rpc)

    async def test_protocols_are_collected_in_parallel(self):
        http_started = asyncio.Event()
        rpc_started = asyncio.Event()

        class ParallelHTTPClient(_FakeHTTPClient):
            async def get_system_info(self):
                http_started.set()
                await asyncio.wait_for(rpc_started.wait(), timeout=0.1)
                return {}

        class ParallelRPCClient(_FakeRPCClient):
            async def version(self):
                rpc_started.set()
                await asyncio.wait_for(http_started.wait(), timeout=0.1)
                return {}

        miner = BaseMiner(
            "10.0.0.1",
            http=cast(BaseHTTPClient, ParallelHTTPClient()),
            rpc=cast(BaseRPCClient, ParallelRPCClient()),
        )

        snapshot = await miner.collect()

        self.assertTrue(snapshot.ok)
        self.assertTrue(http_started.is_set())
        self.assertTrue(rpc_started.is_set())

    async def test_async_context_manager_closes_clients(self):
        http = _FakeHTTPClient()
        rpc = _FakeRPCClient()

        async with BaseMiner(
            "10.0.0.1",
            http=cast(BaseHTTPClient, http),
            rpc=cast(BaseRPCClient, rpc),
        ):
            pass

        self.assertTrue(http.closed)
        self.assertTrue(rpc.closed)


class TestIPolloMiner(unittest.IsolatedAsyncioTestCase):
    def test_builds_default_vendor_clients(self):
        miner = IPolloMiner("10.0.0.1")

        self.assertIsInstance(miner.http, IPolloHTTPClient)
        self.assertIsInstance(miner.rpc, CGMinerRPCClient)
        miner.close()

    async def test_collects_ipollo_http_and_cgminer_rpc_data(self):
        miner = IPolloMiner(
            "10.0.0.1",
            http=cast(BaseHTTPClient, _FakeIPolloHTTPClient()),
            rpc=cast(BaseRPCClient, _FakeRPCClient()),
        )

        snapshot = await miner.collect()

        assert snapshot.http is not None
        assert snapshot.rpc is not None
        self.assertEqual(
            set(snapshot.http.data), {"get_system_info", "summary", "pools"}
        )
        self.assertEqual(snapshot.http.data["summary"]["algo"], "etc")
        self.assertEqual(snapshot.rpc.data["summary"]["hashrate"], 100)
        self.assertEqual(snapshot.errors, {})


if __name__ == "__main__":
    unittest.main()
