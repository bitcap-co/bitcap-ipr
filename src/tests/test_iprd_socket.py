# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import socket
import sys
import threading
import unittest
from collections.abc import Callable, Mapping
from typing import cast

from PySide6.QtCore import QCoreApplication
from typing_extensions import Self, override

from mod.lm.iprd.socket import IPRD_CMD_STATUS, IPRDCommand, IPRDSocket

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


class OneShotServer:
    def __init__(self, response: Mapping[str, object] | bytes) -> None:
        self.request: dict[str, object] | None = None
        self._response: Mapping[str, object] | bytes = response
        self._listener: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen(1)
        self.port: int = cast(tuple[str, int], self._listener.getsockname())[1]
        self._thread: threading.Thread = threading.Thread(
            target=self._serve, daemon=True
        )

    def __enter__(self) -> Self:
        self._thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self._thread.join(timeout=1)
        self._listener.close()

    def _serve(self) -> None:
        conn = self._listener.accept()[0]
        with conn, conn.makefile("rb") as reader:
            self.request = cast(dict[str, object], json.loads(reader.readline()))
            response = (
                self._response
                if isinstance(self._response, bytes)
                else json.dumps(self._response).encode()
            )
            conn.sendall(response + b"\n")


class TestIPRDSocket(unittest.TestCase):
    client: IPRDSocket = cast(IPRDSocket, cast(object, None))
    errors: list[str] = cast(list[str], cast(object, None))

    @override
    def setUp(self) -> None:
        self.client = IPRDSocket()
        self.errors = []
        _ = self.client.error.connect(self.errors.append)

    @override
    def tearDown(self) -> None:
        self.client.close()

    def with_server(
        self,
        response: Mapping[str, object] | bytes,
        callback: Callable[[OneShotServer], None],
    ) -> None:
        with OneShotServer(response) as server:
            self.assertTrue(self.client.set_socket_addr("127.0.0.1", server.port))
            callback(server)

    def test_status_command_returns_validated_status(self) -> None:
        response = {
            "type": IPRD_CMD_STATUS,
            "requestID": "status-1",
            "timestamp": 1770000000,
            "status": {
                "state": "degraded",
                "listenersConfigured": 2,
                "listenersActive": 1,
                "activationFailures": 2,
                "reconnects": 3,
                "captureErrors": 4,
                "captureWriteErrors": 5,
                "packets": {
                    "processed": 10,
                    "reports": 6,
                    "invalid": 1,
                    "duplicates": 2,
                    "unknownFiltered": 1,
                },
                "listeners": [
                    {
                        "interface": "eth0",
                        "state": "active",
                        "activationFailures": 0,
                        "captureErrors": 0,
                        "reconnects": 0,
                    }
                ],
                "lastPacketAt": "2026-08-22T12:00:00Z",
                "lastReportAt": "2026-08-22T11:59:00Z",
            },
        }

        def run(server: OneShotServer) -> None:
            status = self.client.status()
            self.assertIsNotNone(status)
            assert status is not None
            self.assertEqual(status.state, "degraded")
            self.assertEqual(status.listeners_configured, 2)
            self.assertEqual(status.packets.unknown_filtered, 1)
            self.assertEqual(status.listeners[0].interface, "eth0")
            self.assertEqual(server.request, {"command": IPRD_CMD_STATUS})

        self.with_server(response, run)
        self.assertEqual(self.errors, [])

    def test_send_command_serializes_request_id(self) -> None:
        response = {
            "type": IPRD_CMD_STATUS,
            "requestID": "request-123",
            "timestamp": 1770000000,
            "error": "status unavailable",
        }

        def run(server: OneShotServer) -> None:
            result = self.client.send_command(
                IPRDCommand(command=IPRD_CMD_STATUS, request_id="request-123")
            )
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.request_id, "request-123")
            self.assertEqual(result.error, "status unavailable")
            self.assertEqual(
                server.request,
                {"command": IPRD_CMD_STATUS, "requestID": "request-123"},
            )

        self.with_server(response, run)

    def test_status_rejects_daemon_error(self) -> None:
        response = {
            "type": IPRD_CMD_STATUS,
            "timestamp": 1770000000,
            "error": "status unavailable",
        }
        self.with_server(response, lambda _: self.assertIsNone(self.client.status()))
        self.assertEqual(self.errors, ["status unavailable"])

    def test_send_command_rejects_invalid_response(self) -> None:
        self.with_server(b"not json", lambda _: self.assertIsNone(self.client.status()))
        self.assertEqual(len(self.errors), 1)
        self.assertIn("Invalid command response", self.errors[0])

    def test_set_socket_addr_rejects_invalid_values(self) -> None:
        self.assertFalse(self.client.set_socket_addr("not-an-ip", 7788))
        self.assertFalse(self.client.set_socket_addr("127.0.0.1", 0))
        self.assertFalse(self.client.set_socket_addr("127.0.0.1", 65536))


if __name__ == "__main__":
    _ = unittest.main()
