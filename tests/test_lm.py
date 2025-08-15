import binascii
import socket
import sys
import unittest
import zlib
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QMetaMethod
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from src.mod.lm.listener import Listener

app = QApplication(sys.argv)


def read_payload(filename: str) -> str:
    with open(Path(filename).resolve(), "r") as f:
        payload = f.read()
    return payload


def zlib_compress(filename: str) -> str:
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
        self.result: List[str] = []
        self.error: bool = False
        self.result_spy: Optional[QSignalSpy] = None
        self.error_spy: Optional[QSignalSpy] = None
        self.listener = None
        self.bound = False
        self.__init_listener()

    def __init_listener(self):
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

    def emit_result(self, result: List[str]):
        print("received result")
        print(f"{result}")
        self.result = result

    def emit_error(self):
        print("received error")
        self.error = True

    def close(self):
        self.listener.close()


class TestListeners(unittest.TestCase):
    def setUp(self):
        self.result: List[str] = []
        self.error: bool = False

    def tearDown(self) -> None:
        app.quit()

    def assertResult(
        self, listen_spy: ListenerSpy, ip: str, mac: str, type: str, sn: str
    ):
        self.assertEqual(listen_spy.result[0], ip)
        self.assertEqual(listen_spy.result[1], mac)
        self.assertEqual(listen_spy.result[2], type)
        self.assertEqual(listen_spy.result[3], sn)

    def listenFor(
        self,
        port: int,
        payload: str,
        expected_result: List[str],
        compressed: bool = False,
    ):
        listen_spy = ListenerSpy(port)
        self.assertTrue(listen_spy.bound, True)
        send_udp_dgram(port, payload, compressed)
        QTest.qWait(500)
        self.assertEqual(listen_spy.result_spy.count(), 1)
        self.assertEqual(listen_spy.error_spy.count(), 0)
        self.assertResult(listen_spy, *expected_result)
        listen_spy.close()

    def test_bitmain_common_listen(self):
        test = {
            "port": 14235,
            "payload": "10.10.1.0,ab:cd:ef:ab:cd:ef",
            "expected_result": ["10.10.1.0", "ab:cd:ef:ab:cd:ef", "bitmain-common", ""],
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_iceriver_listen(self):
        test = {
            "port": 11503,
            "payload": "addr:172.16.1.100",
            "expected_result": ["172.16.1.100", "iceriver", "iceriver", ""],
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_whatsminer_listen(self):
        test = {
            "port": 8888,
            "payload": "IP:192.168.100.10MAC:ab:cd:ef:ab:cd:ef",
            "expected_result": [
                "192.168.100.10",
                "ab:cd:ef:ab:cd:ef",
                "whatsminer",
                "",
            ],
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_sealminer_listen(self):
        test = {
            "port": 18650,
            "payload": f"{zlib_compress('tests/payloads/sealminer_a2.json')}",
            "expected_result": ["192.168.1.168", "ab:cd:ef:ab:cd:ef", "sealminer", ""],
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
            compressed=True,
        )

    def test_goldshell_listen(self):
        test = {
            "port": 1314,
            "payload": f"{read_payload('tests/payloads/goldshell.json')}",
            "expected_result": [
                "192.168.9.216",
                "ab:cd:ef:ab:cd:ef",
                "goldshell",
                "LP24BS45xxxxxxxxxx",
            ],
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )

    def test_elphapex_listen(self):
        test = {
            "port": 9999,
            "payload": "DG_IPREPORT_ONLY",
            "expected_result": ["127.0.0.1", "elphapex", "elphapex", ""],
        }
        self.listenFor(
            port=test["port"],
            payload=test["payload"],
            expected_result=test["expected_result"],
        )


if __name__ == "__main__":
    unittest.main()
