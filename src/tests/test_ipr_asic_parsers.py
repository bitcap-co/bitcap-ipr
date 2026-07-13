# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Parity tests for the ported ipr_asic data layer.

The ipr_asic parsers/enums are a verbatim port of the apiv2 data layer (only the
import path changed). These tests assert the port produced identical behaviour by
comparing ipr_asic output against the apiv2 originals on identical inputs, so any
future drift in a ported parser is caught.
"""

import unittest

import mod.apiv2.data as apiv2_data
import mod.apiv2.data.miners as apiv2_miners
import mod.ipr_asic.data as ipr_data
import mod.ipr_asic.data.miners as ipr_miners

# parser class name -> (apiv2 class, ipr_asic class)
PARSER_NAMES = [
    "AntminerParser",
    "AuradineParser",
    "ElphapexParser",
    "GoldshellParser",
    "IceriverParser",
    "LuxminerParser",
    "SealminerParser",
    "SRBMinerParser",
    "VnishParser",
    "VolcminerParser",
    "WhatsminerParser",
    "WhatsminerV3Parser",
]


class TestEnumParity(unittest.TestCase):
    def test_enum_members_match(self):
        for enum_name in (
            "MinerType",
            "MinerFirmware",
            "MinerAlgorithm",
            "MinerPlatform",
        ):
            a = getattr(apiv2_data, enum_name)
            b = getattr(ipr_data, enum_name)
            self.assertEqual(
                {m.name: m.value for m in a},
                {m.name: m.value for m in b},
                f"{enum_name} members diverged",
            )

    def test_minerdata_fields_match(self):
        self.assertEqual(
            list(apiv2_data.MinerData.model_fields.keys()),
            list(ipr_data.MinerData.model_fields.keys()),
        )

    def test_minerdata_as_dict_fills_na(self):
        d = ipr_data.MinerData().as_dict()
        # empty MinerData should render every field as "N/A"
        self.assertTrue(all(v == "N/A" for v in d.values()))


class TestParserParity(unittest.TestCase):
    def test_all_parsers_present(self):
        for name in PARSER_NAMES:
            self.assertTrue(hasattr(ipr_miners, name), f"missing {name}")

    def test_initial_defaults_match(self):
        # post-__init__ defaults (type/firmware/algorithm/platform) must match apiv2
        for name in PARSER_NAMES:
            a = getattr(apiv2_miners, name)()
            b = getattr(ipr_miners, name)()
            self.assertEqual(
                a.get_data(), b.get_data(), f"{name} default data diverged"
            )

    def test_antminer_full_parse_parity(self):
        system_info = {
            "minertype": "Antminer S19j Pro",
            "macaddr": "AA:BB:CC:DD:EE:FF",
            "hostname": "antminer",
            "serinum": "SER123",
            "system_filesystem_version": "2023-05-01",
        }
        summary = {"Elapsed": 12345}
        log = {"text": "Xilinx Zynq stuff === rest"}
        pools = [{"Status": "Alive", "URL": "stratum+tcp://p:3333", "User": "acct.wrk"}]

        a = apiv2_miners.AntminerParser()
        b = ipr_miners.AntminerParser()
        for p in (a, b):
            p.parse_summary(dict(summary))
            p.parse_platform(dict(log))
            p.parse_system_info(dict(system_info))
            p.parse_pools([dict(pools[0])])
        self.assertEqual(a.get_data(), b.get_data())

    def test_whatsminer_pools_parity(self):
        pools = [{"Status": "Alive", "URL": "stratum+tcp://x:3333", "User": "u.w"}]
        a = apiv2_miners.WhatsminerParser()
        b = ipr_miners.WhatsminerParser()
        a.parse_pools([dict(pools[0])])
        b.parse_pools([dict(pools[0])])
        self.assertEqual(a.get_data(), b.get_data())


if __name__ == "__main__":
    unittest.main()
