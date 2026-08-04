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
from mod.ipr_asic.models import MinerPool, MinerSummary
from mod.ipr_asic.protocol import BaseHTTPClient, BaseRPCClient
from mod.ipr_asic.rpc import IPolloRPCClient


class _FakeTransport:
    def __init__(self) -> None:
        self.closed = False

    def _close(self, ex=None):
        self.closed = True


class _TestMiner(BaseMiner):
    async def get_summary(self) -> MinerSummary:
        return MinerSummary(hashrate=100, hashrate_unit="MH/s")

    async def get_pools(self) -> list[MinerPool]:
        return [MinerPool(url="stratum.example", user="worker")]


class _FakeIPolloHTTPClient(_FakeTransport):
    async def get_system_info(self):
        return {"uptime": 120}

    async def summary(self):
        raise AssertionError("IPollo summary telemetry must use RPC")

    async def pools(self):
        raise AssertionError("IPollo pool telemetry must use RPC")


class _FakeIPolloRPCClient(_FakeTransport):
    def __init__(self) -> None:
        super().__init__()
        self.stats_calls = 0

    async def summary(self):
        return {
            "Elapsed": 125,
            "MHS av": 120,
            "MHS2 av": 120,
            "Accepted": 12,
            "Rejected": 3,
            "Stale": 1,
            "Hardware Errors": 2,
        }

    async def stats(self):
        self.stats_calls += 1
        return [
            {
                "STATS": 0,
                "ID": "IPollo",
                "Elapsed": 125,
                "UART ID0": (
                    "asic_count[2] chip_temp[0.00 0.00] chip_status[0 0] "
                    "asic_hash_rate[0.00 0.00] asic_accepted[0 0] "
                    "asic_rejected[0 0]"
                ),
                "UART ID1": (
                    "asic_count[3] chip_temp[55.10 51.00 44.40] "
                    "chip_status[1 1 0] asic_hash_rate[4.50 4.00 0.00] "
                    "asic_accepted[10 20 0] asic_rejected[1 2 0]"
                ),
                "UART ID2": "",
                "G-Model": "G1",
                "enable_port": "1",
                "Algo": "cuckatoo",
                "Unit": "Gh/s",
                "Hashrate": 8.5,
                "Fan": "Fan[5490 5550 5820 5699]",
                "Temp": "Temp[0.0 24.5 29.5 24.5 27.0 24.0]",
            }
        ]

    async def pools(self):
        return [
            {
                "URL": "stratum.example",
                "User": "worker",
                "Status": "Alive",
                "POOL": 0,
                "Priority": 0,
                "Accepted": 12,
                "Rejected": 3,
                "Stale": 1,
                "Diff": 8,
                "Difficulty Accepted": 96,
                "Difficulty Rejected": 24,
            }
        ]


class TestBaseMiner(unittest.IsolatedAsyncioTestCase):
    def test_rpc_hashrate_uses_common_cgminer_keys(self):
        miner = _TestMiner("10.0.0.1")

        self.assertEqual(miner._rpc_hashrate({"GHS av": "12.5"}), (12.5, "GH/s"))

    async def test_collect_builds_normalized_snapshot(self):
        snapshot = await _TestMiner("10.0.0.1").collect()

        self.assertTrue(snapshot.ok)
        self.assertFalse(snapshot.partial)
        self.assertIsNotNone(snapshot.summary)
        assert snapshot.summary is not None
        self.assertEqual(snapshot.summary.hashrate, 100)
        self.assertEqual(snapshot.pools[0].url, "stratum.example")
        self.assertEqual(snapshot.errors, {})

    async def test_collect_preserves_successful_sections(self):
        class PartialMiner(_TestMiner):
            async def get_pools(self) -> list[MinerPool]:
                raise APIError("pools unavailable")

        snapshot = await PartialMiner("10.0.0.1").collect()

        self.assertTrue(snapshot.ok)
        self.assertTrue(snapshot.partial)
        self.assertIsNotNone(snapshot.summary)
        self.assertEqual(snapshot.pools, [])
        self.assertIsInstance(snapshot.errors["pools"], APIError)

    async def test_normalized_sections_are_collected_in_parallel(self):
        summary_started = asyncio.Event()
        pools_started = asyncio.Event()

        class ParallelMiner(_TestMiner):
            async def get_summary(self) -> MinerSummary:
                summary_started.set()
                await asyncio.wait_for(pools_started.wait(), timeout=0.1)
                return await super().get_summary()

            async def get_pools(self) -> list[MinerPool]:
                pools_started.set()
                await asyncio.wait_for(summary_started.wait(), timeout=0.1)
                return await super().get_pools()

        snapshot = await ParallelMiner("10.0.0.1").collect()

        self.assertTrue(snapshot.ok)
        self.assertTrue(summary_started.is_set())
        self.assertTrue(pools_started.is_set())

    async def test_async_context_manager_closes_clients(self):
        http = _FakeTransport()
        rpc = _FakeTransport()

        async with _TestMiner(
            "10.0.0.1",
            http=cast(BaseHTTPClient, http),
            rpc=cast(BaseRPCClient, rpc),
        ):
            pass

        self.assertTrue(http.closed)
        self.assertTrue(rpc.closed)


class TestIPolloMiner(unittest.IsolatedAsyncioTestCase):
    def test_rpc_hashrate_prefers_base_hashrate_model(self):
        miner = IPolloMiner(
            "10.0.0.1",
            http=cast(BaseHTTPClient, _FakeIPolloHTTPClient()),
            rpc=cast(BaseRPCClient, _FakeIPolloRPCClient()),
        )

        self.assertEqual(
            miner._rpc_hashrate({"MHS2 av": 120, "MHS av": 10}),
            (120_000_000_000, "Gh/s"),
        )
        self.assertEqual(miner._rpc_hashrate({"MHS av": 10}), (10, "MH/s"))

    def test_builds_default_vendor_clients(self):
        miner = IPolloMiner("10.0.0.1")

        self.assertIsInstance(miner.http, IPolloHTTPClient)
        self.assertIsInstance(miner.rpc, IPolloRPCClient)
        miner.close()

    async def test_builds_normalized_telemetry_from_rpc(self):
        rpc = _FakeIPolloRPCClient()
        miner = IPolloMiner(
            "10.0.0.1",
            http=cast(BaseHTTPClient, _FakeIPolloHTTPClient()),
            rpc=cast(BaseRPCClient, rpc),
        )

        snapshot = await miner.collect()

        self.assertTrue(snapshot.ok)
        self.assertEqual(snapshot.errors, {})
        self.assertIsNotNone(snapshot.summary)
        assert snapshot.summary is not None
        self.assertEqual(snapshot.summary.elapsed, 125)
        self.assertEqual(snapshot.summary.hashrate, 120_000_000_000)
        self.assertEqual(snapshot.summary.hashrate_unit, "Gh/s")
        self.assertEqual(snapshot.summary.chip_temp, 29)
        self.assertEqual(snapshot.summary.fans, [5490, 5550, 5820, 5699])
        self.assertIsNotNone(snapshot.stats)
        assert snapshot.stats is not None
        self.assertEqual(snapshot.stats.accepted, 30)
        self.assertEqual(snapshot.stats.rejected, 3)
        self.assertEqual(len(snapshot.hashboards), 2)
        self.assertFalse(snapshot.hashboards[0].enabled)
        self.assertEqual(snapshot.hashboards[1].chip_count, 3)
        self.assertEqual(snapshot.hashboards[1].chip_count_healthy, 2)
        self.assertEqual(snapshot.hashboards[1].hashrate, 8_500_000_000)
        self.assertEqual(snapshot.hashboards[1].chip_temp, 55)
        self.assertEqual(snapshot.hashboards[1].error, "1 ASICs inactive")
        self.assertEqual(rpc.stats_calls, 1)
        self.assertEqual(len(snapshot.pools), 1)
        self.assertTrue(snapshot.pools[0].active)
        self.assertEqual(snapshot.pools[0].accepted, 12)
        self.assertEqual(snapshot.pools[0].difficulty_accepted, 96)

    async def test_does_not_fallback_to_http_telemetry(self):
        class FailingRPCClient(_FakeIPolloRPCClient):
            async def summary(self):
                raise APIError("RPC unavailable")

            async def pools(self):
                raise APIError("RPC unavailable")

            async def stats(self):
                raise APIError("RPC unavailable")

        miner = IPolloMiner(
            "10.0.0.1",
            http=cast(BaseHTTPClient, _FakeIPolloHTTPClient()),
            rpc=cast(BaseRPCClient, FailingRPCClient()),
        )

        snapshot = await miner.collect()

        self.assertFalse(snapshot.ok)
        self.assertFalse(snapshot.partial)
        self.assertIsInstance(snapshot.errors["summary"], APIError)
        self.assertIsInstance(snapshot.errors["pools"], APIError)
        self.assertIsNone(snapshot.summary)
        self.assertEqual(snapshot.pools, [])


if __name__ == "__main__":
    unittest.main()
