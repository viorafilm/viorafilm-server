from __future__ import annotations

import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

from payments.models import PaymentProviderType, PaymentSettings, PaymentStatus
from payments.service import PaymentService


class _SingleResponseServer:
    def __init__(self, response_text: str) -> None:
        self._response_bytes = response_text.encode("cp949", errors="replace")
        self.received: list[bytes] = []
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.host = "127.0.0.1"
        self.port = 0

    def start(self) -> None:
        self._thread.start()
        if not self._ready.wait(3):
            raise RuntimeError("test server failed to start")

    def close(self) -> None:
        self._stop.set()
        try:
            with socket.create_connection((self.host, self.port), timeout=0.2):
                pass
        except Exception:
            pass
        self._thread.join(timeout=2)

    def _run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, 0))
            server.listen(2)
            self.port = int(server.getsockname()[1])
            self._ready.set()
            while not self._stop.is_set():
                try:
                    server.settimeout(0.2)
                    conn, _addr = server.accept()
                except socket.timeout:
                    continue
                with conn:
                    conn.settimeout(1.0)
                    chunks: list[bytes] = []
                    deadline = time.monotonic() + 2.0
                    while time.monotonic() < deadline:
                        try:
                            chunk = conn.recv(4096)
                        except socket.timeout:
                            continue
                        if not chunk:
                            break
                        chunks.append(chunk)
                        if b"\r" in chunk:
                            break
                    self.received.append(b"".join(chunks))
                    conn.sendall(self._response_bytes)
                    break


class EvcatProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.db_path = self.root / "payments.sqlite3"
        self.log_dir = self.root / "logs"
        self._services: list[PaymentService] = []
        self._servers: list[_SingleResponseServer] = []

    def tearDown(self) -> None:
        for service in self._services:
            try:
                service.close()
            except Exception:
                pass
        for server in self._servers:
            try:
                server.close()
            except Exception:
                pass
        self._tmp.cleanup()

    def _start_server(self, response_text: str) -> _SingleResponseServer:
        server = _SingleResponseServer(response_text)
        server.start()
        self._servers.append(server)
        return server

    def _service(self, *, port: int) -> PaymentService:
        settings = PaymentSettings(
            payment_enabled=True,
            payment_provider=PaymentProviderType.EVCAT_TCP,
            terminal_ip="127.0.0.1",
            terminal_port=int(port),
            terminal_name="EVCAT3",
            currency="KRW",
            payment_timeout_sec=5,
            request_timeout_ms=1500,
        )
        service = PaymentService(settings, self.db_path, self.log_dir)
        self._services.append(service)
        return service

    def test_ping_uses_evcat_live_probe(self) -> None:
        server = self._start_server("\x07\x06C\x06\x06LIVE\x03")
        service = self._service(port=server.port)

        result = service.ping()

        self.assertTrue(result.success)
        self.assertEqual(result.provider, PaymentProviderType.EVCAT_TCP)
        self.assertEqual(result.message, "LIVE")
        request = server.received[0].decode("cp949", errors="replace")
        self.assertEqual(request, "\x07\x061000".replace("1000", "8899") + "\x1c0000\x06\r")

    def test_sale_builds_approval_packet_and_parses_success(self) -> None:
        response = (
            "\x07ORD-001\x06Y\x06MS\x0600"
            "\x1c승인"
            "\x1cMS"
            "\x1c20260324"
            "\x1c173000"
            "\x1c55317700****530*"
            "\x1c12345678"
            "\x1c00940447923"
            "\x1cD"
            "\x1c0521"
            "\x1c하나카드"
            "\x1c0505"
            "\x1c외환"
            "\x1c정상승인"
            "\x1c"
            "\x1c"
            "\x1cORD-001"
            "\x1c4000"
            "\x1c363"
            "\x1c1100835257"
            "\x1c123456"
            "\x1cPGTX001"
            "\x1c"
            "\x1c00"
            "\x1c"
            "\x1c"
            "\x1c"
            "\x03"
        )
        server = self._start_server(response)
        service = self._service(port=server.port)

        result = service.provider.sale("ORD-001", 4000, "KRW", "Photo kiosk order")

        self.assertEqual(result.status, PaymentStatus.APPROVED)
        self.assertEqual(result.transaction_id, "12345678")
        self.assertEqual(result.amount_cents, 4000)
        self.assertEqual(result.last4_masked, "55317700****530*")
        request = server.received[0].decode("cp949", errors="replace")
        self.assertTrue(request.startswith("\x07\x061000\x1c1100\x1c4000\x1c363\x1c0\x1c00"))
        self.assertIn("\x1cORD-001\x1c", request)


if __name__ == "__main__":
    unittest.main()
