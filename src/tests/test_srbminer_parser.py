# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import unittest
from pathlib import Path

from mod.ipr_asic.data import MinerAlgorithm, MinerType
from mod.ipr_asic.data.miners.srbminer import (
    SRBMinerModels,
    SRBMinerParser,
    _format_gpu_model,
)
from mod.ipr_asic.schemas.srbminer import SRBMinerInfo


def read_payload(filename: str) -> dict:
    with open(Path(filename).resolve(), "r") as f:
        return json.load(f)


class TestFormatGPUModel(unittest.TestCase):
    def test_strips_vendor_and_uppercases_acronym(self):
        self.assertEqual(_format_gpu_model("nvidia_geforce_rtx_3070"), "RTX 3070")

    def test_amd_radeon(self):
        self.assertEqual(_format_gpu_model("amd_radeon_rx_6800"), "RX 6800")

    def test_all_noise_falls_back_to_raw_tokens(self):
        # if every token is filtered, fall back rather than returning empty
        self.assertEqual(_format_gpu_model("nvidia"), "Nvidia")


class TestSRBMinerParser(unittest.TestCase):
    def setUp(self):
        self.payload = read_payload("tests/payloads/srbminer.json")
        self.info = SRBMinerInfo.model_validate(self.payload)
        pools = [algo.pool for algo in self.info.algorithms if algo.pool.pool]
        self.data = SRBMinerParser().parse(
            SRBMinerModels(system_info=self.info, pools=pools)
        )

    def test_type_and_platform(self):
        self.assertEqual(self.data.type, MinerType.HIVEGPU)
        self.assertEqual(self.data.platform, "HiveOS")

    def test_subtype_is_count_and_model(self):
        self.assertEqual(self.data.subtype, "4x RTX 3070")

    def test_version_and_hostname_and_uptime(self):
        # SRBMiner version is reported as the API version; the rig firmware
        # version is not exposed by the API.
        self.assertEqual(self.data.api_version, "3.3.7")
        self.assertEqual(self.data.hostname, "SRBMiner-Multi-Rig")
        self.assertEqual(self.data.uptime, self.payload["mining_time"])

    def test_algorithm(self):
        # pearlhash resolves to the MinerAlgorithm added for GPU rigs
        self.assertEqual(self.data.algorithm, MinerAlgorithm.PEARLHASH)

    def test_pools(self):
        self.assertEqual(
            self.data.stratum_url, self.payload["algorithms"][0]["pool"]["pool"]
        )
        # wallet.worker is split into username/worker_name
        wallet = self.payload["algorithms"][0]["pool"]["wallet"]
        self.assertEqual(self.data.username, wallet.split(".", 1)[0])


if __name__ == "__main__":
    unittest.main()
