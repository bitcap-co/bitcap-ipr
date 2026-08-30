# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from pydantic import ValidationError
from PySide6.QtCore import QByteArray
from PySide6.QtNetwork import QHostAddress, QNetworkDatagram

from mod.lm.iprd.listener import IPRDListener, IPRDPacketData
from mod.lm.ipreport import IPReport, IPReportDatagram, MinerTypeHint
from mod.lm.ipreport.patterns import GoldshellIPReport, SealMinerIPReport

IP_REPORT_FIELDS = {
    "created_at",
    "updated_at",
    "hint",
    "miner_hint",
    "sort_ip",
    "ip",
    "mac",
    "serial",
}
LEGACY_IP_REPORT_FIELDS = {
    "port_type",
    "src_addr",
    "src_ip",
    "src_mac",
    "miner_type",
    "miner_sn",
}


class ResultCollector:
    def __init__(self) -> None:
        self.reports: list[IPReport] = []

    def emit(self, report: IPReport) -> None:
        self.reports.append(report)


class TestIPReportSchema(unittest.TestCase):
    def assertIPReportSchema(self, report: IPReport) -> None:
        dumped = report.model_dump()
        self.assertEqual(set(dumped), IP_REPORT_FIELDS)
        self.assertTrue(LEGACY_IP_REPORT_FIELDS.isdisjoint(dumped))
        self.assertIsInstance(report.hint, MinerTypeHint)
        self.assertIsInstance(report.sort_ip, int)

    def test_udp_datagram_uses_current_schema(self) -> None:
        datagram = QNetworkDatagram(
            QByteArray(b"10.10.1.7,AA:BB:CC:DD:EE:FF"),
            QHostAddress("127.0.0.1"),
            MinerTypeHint.COMMON,
        )
        datagram.setSender(QHostAddress("192.0.2.10"), 1234)

        parsed = IPReportDatagram(datagram)

        self.assertTrue(parsed.valid)
        report = parsed.ip_report
        self.assertIPReportSchema(report)
        self.assertEqual(report.hint, MinerTypeHint.COMMON)
        self.assertEqual(report.miner_hint, "antminer")
        self.assertEqual(report.ip, "10.10.1.7")
        self.assertEqual(report.mac, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(report.serial, "")

    def test_iprd_result_uses_same_schema(self) -> None:
        emitted = ResultCollector()
        listener = cast(IPRDListener, cast(object, SimpleNamespace(result=emitted)))
        packet = IPRDPacketData.model_validate(
            {
                "timestamp": 1234567890,
                "packetID": "packet-1",
                "dstPort": MinerTypeHint.GOLDSHELL,
                "srcIP": "192.168.1.20",
                "srcMAC": "AA:BB:CC:DD:EE:FF",
                "minerHint": "goldshell",
            }
        )

        IPRDListener.emit_result(listener, packet)

        self.assertEqual(len(emitted.reports), 1)
        report = emitted.reports[0]
        self.assertIPReportSchema(report)
        self.assertEqual(report.created_at, 1234567890.0)
        self.assertGreaterEqual(report.updated_at, report.created_at)
        self.assertEqual(report.hint, MinerTypeHint.GOLDSHELL)
        self.assertEqual(report.miner_hint, "goldshell")
        self.assertEqual(report.ip, "192.168.1.20")
        self.assertEqual(report.mac, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(report.serial, "")


class TestIPReportParsingRegressions(unittest.TestCase):
    def test_failed_decompression_probe_preserves_payload(self) -> None:
        payload = QByteArray(b"12345678x-not-a-zlib-stream")
        parsed = IPReportDatagram.__new__(IPReportDatagram)
        parsed.src_addr = QHostAddress("192.0.2.10")
        parsed.data = QByteArray(payload)
        parsed.report = IPReport()

        self.assertFalse(parsed._decompress_payload())
        self.assertEqual(parsed.data, payload)

    def test_invalid_utf8_datagrams_are_rejected_without_raising(self) -> None:
        for payload in (b"\xd0", b"x\xd0"):
            with self.subTest(payload=payload):
                datagram = QNetworkDatagram(
                    QByteArray(payload),
                    QHostAddress("127.0.0.1"),
                    MinerTypeHint.ELPHAPEX,
                )
                datagram.setSender(QHostAddress("192.168.1.23"), 9999)

                parsed = IPReportDatagram(datagram)

                self.assertFalse(parsed.valid)

    def test_sealminer_checks_every_reported_interface(self) -> None:
        payload_path = Path(__file__).parent / "payloads" / "sealminer_a2.json"
        payload = cast(
            list[dict[str, object]],
            json.loads(f"[{payload_path.read_text()}]"),
        )
        for interface in payload[2:5]:
            interface["Active"] = False
        payload[4]["Active"] = True
        payload[4]["IPV4"] = "192.168.1.204"

        report = SealMinerIPReport.model_validate(payload)

        self.assertEqual(report.ip, "192.168.1.204")

    def test_object_models_reject_invalid_report_addresses(self) -> None:
        payload_path = Path(__file__).parent / "payloads" / "goldshell.json"
        payload = cast(dict[str, object], json.loads(payload_path.read_text()))
        payload["ip"] = "999.999.999.999"

        with self.assertRaises(ValidationError):
            _ = GoldshellIPReport.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
