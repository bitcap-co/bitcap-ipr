# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Bridge test: verify the qasync integration the app cutover relies on.

Confirms that an @asyncSlot connected to a Qt signal runs its coroutine on the
asyncio-as-Qt event loop, and that it can await an ASICClient facade coroutine
end-to-end (the exact shape of ipr.process_result).
"""

import asyncio
import unittest

from PySide6.QtCore import QCoreApplication, QObject, Signal
from qasync import QEventLoop, asyncSlot

from mod.ipr_asic import ASICClient, MinerType
from mod.ipr_asic.http import SRBMinerHTTPClient

import httpx


class _Emitter(QObject):
    fired = Signal(str)


class _Receiver(QObject):
    def __init__(self, asic: ASICClient):
        super().__init__()
        self.asic = asic
        self.result = None
        self.done = asyncio.Event()

    @asyncSlot(str)
    async def on_fired(self, ip: str):
        # mirrors ipr.process_result: await a facade coroutine from a slot
        self.result = await self.asic.get_miner_data(MinerType.HIVEGPU, ip)
        self.done.set()


class TestQasyncBridge(unittest.TestCase):
    def test_asyncslot_awaits_facade_on_signal(self):
        app = QCoreApplication.instance() or QCoreApplication([])
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        payload = {
            "rig_name": "rig-1",
            "miner_version": "3.3.7",
            "mining_time": 100,
            "total_gpu_workers": 1,
            "gpu_devices": [{"model": "nvidia_geforce_rtx_3070"}],
            "algorithms": [
                {"name": "kheavyhash", "pool": {"pool": "p:1", "wallet": "w.x"}}
            ],
        }
        transport = httpx.MockTransport(lambda r: httpx.Response(200, json=payload))

        asic = ASICClient()

        async def fake_make(miner_type, ip, alt_pwd=None):
            return SRBMinerHTTPClient(ip, transport=transport)

        asic._make_client = fake_make

        emitter = _Emitter()
        receiver = _Receiver(asic)
        emitter.fired.connect(receiver.on_fired)

        async def drive():
            emitter.fired.emit("10.0.0.9")
            await asyncio.wait_for(receiver.done.wait(), timeout=5)

        try:
            with loop:
                loop.run_until_complete(drive())
        finally:
            asyncio.set_event_loop(None)

        self.assertIsNotNone(receiver.result)
        self.assertTrue(receiver.result.ok)
        self.assertEqual(receiver.result.data["hostname"], "rig-1")
        self.assertEqual(receiver.result.data["type"], str(MinerType.HIVEGPU))


if __name__ == "__main__":
    unittest.main()
