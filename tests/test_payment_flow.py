from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from payments.models import OrderFlowState, PaymentResult, PaymentSettings, PaymentStatus
from payments.service import PaymentService
from payments.store import PaymentStore


class PaymentFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.db_path = self.root / "payments.sqlite3"
        self.log_dir = self.root / "logs"
        self._services: list[PaymentService] = []

    def tearDown(self) -> None:
        for service in self._services:
            try:
                service.close()
            except Exception:
                pass
        self._tmp.cleanup()

    def _service(self, **changes) -> PaymentService:
        settings = PaymentSettings(
            payment_enabled=True,
            simulation_delay_sec=0,
            simulation_result="approve",
        ).clone(**changes)
        service = PaymentService(settings, self.db_path, self.log_dir)
        self._services.append(service)
        return service

    def test_mock_approve(self) -> None:
        service = self._service(simulation_result="approve", simulation_delay_sec=0)
        done = threading.Event()
        results = []
        started_capture = threading.Event()

        def _complete(result):
            results.append(result)
            if result.status == PaymentStatus.APPROVED:
                started_capture.set()
            done.set()

        started, _request_ref = service.start_sale(
            order_id="ORD-APPROVE",
            amount_cents=400,
            currency="CAD",
            description="approve",
            order_state=OrderFlowState.PAYMENT_PENDING.value,
            on_complete=_complete,
        )
        self.assertTrue(started)
        self.assertTrue(done.wait(3))
        self.assertEqual(results[0].status, PaymentStatus.APPROVED)
        self.assertTrue(started_capture.is_set())

    def test_mock_decline(self) -> None:
        service = self._service(simulation_result="decline", simulation_delay_sec=0)
        done = threading.Event()
        results = []

        started, _ = service.start_sale(
            order_id="ORD-DECLINE",
            amount_cents=400,
            currency="CAD",
            description="decline",
            on_complete=lambda result: (results.append(result), done.set()),
        )
        self.assertTrue(started)
        self.assertTrue(done.wait(3))
        self.assertEqual(results[0].status, PaymentStatus.DECLINED)

    def test_mock_cancel(self) -> None:
        service = self._service(simulation_result="approve", simulation_delay_sec=2)
        done = threading.Event()
        results = []

        started, _ = service.start_sale(
            order_id="ORD-CANCEL",
            amount_cents=400,
            currency="CAD",
            description="cancel",
            on_complete=lambda result: (results.append(result), done.set()),
        )
        self.assertTrue(started)
        self.assertTrue(service.cancel_active_payment())
        self.assertTrue(done.wait(4))
        self.assertEqual(results[0].status, PaymentStatus.CANCELLED)

    def test_mock_timeout(self) -> None:
        service = self._service(simulation_result="timeout", simulation_delay_sec=0, payment_timeout_sec=1)
        done = threading.Event()
        results = []

        started, _ = service.start_sale(
            order_id="ORD-TIMEOUT",
            amount_cents=400,
            currency="CAD",
            description="timeout",
            on_complete=lambda result: (results.append(result), done.set()),
        )
        self.assertTrue(started)
        self.assertTrue(done.wait(4))
        self.assertEqual(results[0].status, PaymentStatus.TIMEOUT)

    def test_duplicate_request_blocked(self) -> None:
        service = self._service(simulation_result="approve", simulation_delay_sec=2)
        done = threading.Event()
        started, _ = service.start_sale(
            order_id="ORD-DUPLICATE",
            amount_cents=400,
            currency="CAD",
            description="duplicate",
            on_complete=lambda result: done.set(),
        )
        self.assertTrue(started)
        blocked, reason = service.start_sale(
            order_id="ORD-DUPLICATE",
            amount_cents=400,
            currency="CAD",
            description="duplicate",
        )
        self.assertFalse(blocked)
        self.assertEqual(reason, "payment_already_processing")
        self.assertTrue(service.cancel_active_payment())
        self.assertTrue(done.wait(4))

    def test_success_callback_path(self) -> None:
        service = self._service(simulation_result="approve", simulation_delay_sec=0)
        done = threading.Event()
        callback_called = threading.Event()

        def _complete(result):
            if result.status == PaymentStatus.APPROVED:
                callback_called.set()
            done.set()

        started, _ = service.start_sale(
            order_id="ORD-CALLBACK",
            amount_cents=400,
            currency="CAD",
            description="callback",
            on_complete=_complete,
        )
        self.assertTrue(started)
        self.assertTrue(done.wait(3))
        self.assertTrue(callback_called.is_set())

    def test_recovery_records_loaded_after_restart(self) -> None:
        store = PaymentStore(self.db_path)
        pending = PaymentResult(
            status=PaymentStatus.PENDING,
            order_id="ORD-PENDING",
            amount_cents=400,
            currency="CAD",
            provider=PaymentSettings().payment_provider,
            request_ref="ORD-PENDING-REQ",
            message="pending",
            order_state=OrderFlowState.PAYMENT_PROCESSING.value,
        )
        store.save_record(
            store.create_record_from_result(
                pending,
                order_state=OrderFlowState.PAYMENT_PROCESSING.value,
            )
        )
        service = self._service()
        recovery = service.get_recovery_records()
        self.assertEqual(len(recovery), 1)
        self.assertEqual(recovery[0].order_id, "ORD-PENDING")


if __name__ == "__main__":
    unittest.main()
