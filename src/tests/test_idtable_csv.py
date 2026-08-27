# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import unittest
from datetime import datetime

import config  # noqa: F401  # initialize Pydantic before importing miner models
from mod.ipr_asic.data import MinerType
from ui.widgets.ipr.idtable.csv import (
    MinerCSVError,
    normalize_recv_at,
    parse_miner_csv,
    serialize_csv,
)


class TestMinerCSV(unittest.TestCase):
    def test_normalize_recv_at_supports_epoch_iso_and_qt_text_dates(self) -> None:
        qt_text = "Thu Aug 27 12:34:56 2026"

        self.assertEqual(normalize_recv_at(1234), 1234)
        self.assertEqual(normalize_recv_at("5678"), 5678)
        self.assertEqual(normalize_recv_at("2026-08-27T12:34:56+00:00"), 1787834096)
        self.assertEqual(
            normalize_recv_at(qt_text),
            int(
                datetime.strptime(qt_text, "%a %b %d %H:%M:%S %Y")
                .astimezone()
                .timestamp()
            ),
        )
        self.assertIsNone(normalize_recv_at("N/A"))
        self.assertIsNone(normalize_recv_at("not a date"))

    def test_parse_accepts_partial_reordered_and_quoted_columns(self) -> None:
        text = (
            "SERIAL,HOSTNAME,IP,RECV AT,TYPE\n"
            'SERIAL-1,"rack, west",10.0.0.1,1234,antminer\n'
            "N/A,rack-east,10.0.0.2,N/A,unknown\n"
        )

        miners = parse_miner_csv(text)

        self.assertEqual(len(miners), 2)
        self.assertEqual(miners[0].ip, "10.0.0.1")
        self.assertEqual(miners[0].hostname, "rack, west")
        self.assertEqual(miners[0].recv_at, 1234)
        self.assertEqual(miners[0].type, MinerType.ANTMINER)
        self.assertIsNone(miners[1].serial)
        self.assertIsNone(miners[1].recv_at)

    def test_parse_accepts_utf8_bom_and_skips_blank_rows(self) -> None:
        miners = parse_miner_csv("\ufeffIP,MAC\n\n10.0.0.1,aa:bb:cc:dd:ee:ff\n")

        self.assertEqual(len(miners), 1)
        self.assertEqual(miners[0].ip, "10.0.0.1")

    def test_parse_rejects_csv_without_miner_columns(self) -> None:
        with self.assertRaises(MinerCSVError):
            parse_miner_csv("NAME,VALUE\nexample,1\n")

    def test_serialize_quotes_values_and_round_trips(self) -> None:
        output = serialize_csv(
            ["IP", "HOSTNAME", "SERIAL"],
            [["10.0.0.1", "rack, west", 'serial-"quoted"']],
        )

        self.assertEqual(
            output,
            'IP,HOSTNAME,SERIAL\n10.0.0.1,"rack, west","serial-""quoted"""\n',
        )
        miners = parse_miner_csv(output)
        self.assertEqual(miners[0].hostname, "rack, west")
        self.assertEqual(miners[0].serial, 'serial-"quoted"')


if __name__ == "__main__":
    unittest.main()
