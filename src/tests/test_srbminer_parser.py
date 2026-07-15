# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import unittest
from pathlib import Path

from mod.ipr_asic.data import MinerAlgorithm, MinerType
from mod.ipr_asic.data.miners.srbminer import SRBMinerParser, _format_gpu_model
from mod.ipr_asic.http.srbminer import SRBMinerInfo


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
        # normalize through the client's model the same way the client does
        self.info = SRBMinerInfo.model_validate(self.payload).model_dump()
        self.parser = SRBMinerParser()
        self.parser.parse_all(self.info)
        self.parser.parse_uptime(self.info)

    def test_type_and_platform(self):
        data = self.parser.get_data()
        self.assertEqual(data["type"], str(MinerType.HIVEGPU))
        self.assertEqual(data["platform"], "HiveOS")

    def test_subtype_is_count_and_model(self):
        self.assertEqual(self.parser.get_data()["subtype"], "4x RTX 3070")

    def test_version_and_hostname_and_uptime(self):
        data = self.parser.get_data()
        # SRBMiner version is reported as the API version; the rig firmware
        # version is not exposed by the API.
        self.assertEqual(data["api_version"], "3.3.7")
        self.assertEqual(data["hostname"], "SRBMiner-Multi-Rig")
        self.assertEqual(data["uptime"], self.payload["mining_time"])

    def test_algorithm(self):
        # pearlhash resolves to the MinerAlgorithm added for GPU rigs
        self.assertEqual(
            self.parser.get_data()["algorithm"], str(MinerAlgorithm.PEARLHASH)
        )

    def test_pools(self):
        pools = [
            {"url": algo["pool"]["pool"], "user": algo["pool"]["wallet"]}
            for algo in self.info["algorithms"]
            if algo["pool"]["pool"]
        ]
        self.parser.parse_pools(pools)
        data = self.parser.get_data()
        self.assertEqual(
            data["stratum_url"], self.payload["algorithms"][0]["pool"]["pool"]
        )
        # wallet.worker is split into username/worker_name
        wallet = self.payload["algorithms"][0]["pool"]["wallet"]
        self.assertEqual(data["username"], wallet.split(".", 1)[0])


if __name__ == "__main__":
    unittest.main()
