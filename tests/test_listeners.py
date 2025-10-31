import binascii
import socket
import sys
import unittest
import zlib
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import QMetaMethod
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from src.mod.lm.listener import Listener, Record

app = QApplication(sys.argv)


def read_payload(filename: str) -> str:
    with open(Path(filename).resolve(), "r") as f:
        payload = f.read()
    return payload


def compress_paylaod(filename: str) -> str:
    with open(Path(filename).resolve(), "rb") as f:
        data = f.read()
    return binascii.hexlify(zlib.compress(data)).decode("utf-8")


def send_udp_dgram(port: int, msg: str, compressed: bool = False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ip_addr = "127.0.0.1"
    if compressed:
        sock.sendto(bytes.fromhex(msg), (ip_addr, port))
    else:
        sock.sendto(bytes(msg, "utf-8"), (ip_addr, port))
    sock.close()


class ListenerSpy:
    def __init__(self, port: int):
        self.port = port
        self.result: Dict[str, Any]
        self.error: str = ""
        self.result_spy: QSignalSpy
        self.error_spy: QSignalSpy
        self.listener: Listener
        self.bound = False
        self.record: Record
        self._create_listener()

    def _create_listener(self):
        self.listener = Listener(port=self.port, parent=None)
        self.listener.result.connect(self.emit_result)
        self.listener.error.connect(self.emit_error)
        self.result_spy = QSignalSpy(
            self.listener, QMetaMethod.fromSignal(self.listener.result)
        )
        self.error_spy = QSignalSpy(
            self.listener, QMetaMethod.fromSignal(self.listener.error)
        )
        self.bound = self.listener.bound
        self.record = self.listener.record

    def emit_result(self, result: Dict[str, Any]):
        self.result = result

    def emit_error(self, err: str):
        self.error = err

    def close(self):
        self.listener.close()


class TestListeners(unittest.TestCase):
    def tearDown(self) -> None:
        app.quit()

    def assertResult(self, listener: ListenerSpy, miner_type: str, ip: str, mac: str):
        self.assertEqual(listener.result["ip"], ip)
        self.assertEqual(listener.result["mac"], mac)
        self.assertEqual(listener.result["miner_type"], miner_type)

    def listenFor(
        self,
        port: int,
        payload: str,
        expected_result: Dict[str, Any],
        compressed: bool = False,
    ):
        listener = ListenerSpy(port)
        self.assertTrue(listener.bound, True)
        self.assertEqual(listener.error, "")
        send_udp_dgram(port, payload, compressed)
        QTest.qWait(500)
        self.assertEqual(listener.result_spy.count(), 1)
        self.assertEqual(listener.error_spy.count(), 0)
        self.assertEqual(len(listener.record), 1)
        self.assertResult(listener, **expected_result)
        listener.close()

    def test_common_listen(self):
        """Test common payload (port 14235)"""
        test = {
            "port": 14235,
            "payload": "10.10.1.0,ab:cd:ef:ab:cd:ef",
            "expected_result": {
                "ip": "10.10.1.0",
                "mac": "ab:cd:ef:ab:cd:ef",
                "miner_type": "common",
            },
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_iceriver_listen(self):
        """Test iceriver payload (port 11503)"""
        test = {
            "port": 11503,
            "payload": "addr:172.16.1.100",
            "expected_result": {
                "ip": "172.16.1.100",
                "mac": "iceriver",
                "miner_type": "iceriver",
            },
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_whatsminer_listen(self):
        """Test whatsminer payload (port 8888)"""
        test = {
            "port": 8888,
            "payload": "IP:192.168.100.10MAC:ab:cd:ef:ab:cd:ef",
            "expected_result": {
                "ip": "192.168.100.10",
                "mac": "ab:cd:ef:ab:cd:ef",
                "miner_type": "whatsminer",
            },
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_sealminer_listen(self):
        """Test sealminer payload (port 18650)"""
        test = {
            "port": 18650,
            "payload": f"{compress_paylaod('tests/payloads/sealminer_a2.json')}",
            "expected_result": {
                "ip": "192.168.1.168",
                "mac": "ab:cd:ef:ab:cd:ef",
                "miner_type": "sealminer",
            },
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
            compressed=True,
        )

    def test_goldshell_listen(self):
        """Test goldshell payload (port 1314)"""
        test = {
            "port": 1314,
            "payload": f"{read_payload('tests/payloads/goldshell.json')}",
            "expected_result": {
                "ip": "192.168.9.216",
                "mac": "ab:cd:ef:ab:cd:ef",
                "miner_type": "goldshell",
            },
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_elphapex_listen(self):
        "Test elphapex payload (port 9999)"
        test = {
            "port": 9999,
            "payload": "DG_IPREPORT_ONLY",
            "expected_result": {
                "ip": "127.0.0.1",
                "mac": "elphapex",
                "miner_type": "elphapex",
            },
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_duplicate_datagram(self):
        """Test duplicate datagrams"""
        port = 14235
        payload = "10.10.1.0,ab:cd:ef:ab:cd:ef"
        listener = ListenerSpy(port)
        self.assertTrue(listener.bound, True)
        self.assertEqual(listener.error, "")
        send_udp_dgram(port, payload)
        QTest.qWait(500)
        send_udp_dgram(port, payload)
        QTest.qWait(500)
        self.assertEqual(listener.result_spy.count(), 1)
        self.assertEqual(listener.error_spy.count(), 0)
        self.assertEqual(len(listener.record), 1)
        listener.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
