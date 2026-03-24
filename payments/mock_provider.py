from __future__ import annotations

import threading
import time
import uuid

from .base import PaymentProvider
from .models import (
    FlowStateResult,
    PairResult,
    PaymentProviderType,
    PaymentResult,
    PaymentSettings,
    PaymentStatus,
    PingResult,
    now_iso,
)


class MockPaymentProvider(PaymentProvider):
    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.RLock()
        self._cancel_event = threading.Event()
        self._flow_state = FlowStateResult(provider=PaymentProviderType.MOCK)

    def initialize(self, settings: PaymentSettings) -> None:
        with self._lock:
            self.settings = settings.clone(payment_provider=PaymentProviderType.MOCK)
            self._cancel_event.clear()
            self._flow_state = FlowStateResult(
                provider=PaymentProviderType.MOCK,
                status=PaymentStatus.IDLE,
                is_busy=False,
                terminal_name=self.settings.terminal_name or "MOCK TERMINAL",
                terminal_ip=self.settings.terminal_ip,
            )

    def _set_flow(
        self,
        status: PaymentStatus,
        *,
        is_busy: bool,
        message: str,
        order_id: str = "",
        cancellable: bool = False,
    ) -> None:
        with self._lock:
            self._flow_state = FlowStateResult(
                provider=PaymentProviderType.MOCK,
                status=status,
                is_busy=is_busy,
                message=message,
                current_order_id=str(order_id or ""),
                terminal_name=self.settings.terminal_name or "MOCK TERMINAL",
                terminal_ip=self.settings.terminal_ip,
                cancellable=cancellable,
                updated_at=now_iso(),
            )

    def pair_terminal(self) -> PairResult:
        self._set_flow(PaymentStatus.IDLE, is_busy=False, message="MOCK terminal paired")
        return PairResult(
            success=True,
            provider=PaymentProviderType.MOCK,
            message="MOCK terminal pair succeeded",
            terminal_name=self.settings.terminal_name or "MOCK TERMINAL",
            terminal_ip=self.settings.terminal_ip,
        )

    def ping(self) -> PingResult:
        self._set_flow(PaymentStatus.IDLE, is_busy=False, message="MOCK terminal reachable")
        return PingResult(
            success=True,
            provider=PaymentProviderType.MOCK,
            message="MOCK terminal ping ok",
            terminal_name=self.settings.terminal_name or "MOCK TERMINAL",
            terminal_ip=self.settings.terminal_ip,
            latency_ms=5,
        )

    def sale(self, order_id: str, amount_cents: int, currency: str, description: str) -> PaymentResult:
        if self._cancel_event.is_set():
            self._cancel_event.clear()
            self._set_flow(
                PaymentStatus.CANCELLED,
                is_busy=False,
                message="MOCK payment cancelled",
                order_id=order_id,
            )
            return PaymentResult(
                status=PaymentStatus.CANCELLED,
                order_id=order_id,
                amount_cents=amount_cents,
                currency=currency,
                provider=PaymentProviderType.MOCK,
                message="Mock payment cancelled by operator",
                raw_response={"outcome": "cancelled_before_start"},
            )
        self._set_flow(
            PaymentStatus.PENDING,
            is_busy=True,
            message=f"MOCK processing {amount_cents} {currency}",
            order_id=order_id,
            cancellable=True,
        )
        delay_sec = max(0, int(self.settings.simulation_delay_sec))
        outcome = str(self.settings.simulation_result or "approve").strip().lower()
        if outcome not in {"approve", "decline", "cancel", "timeout"}:
            outcome = "approve"

        started_at = time.monotonic()
        target_delay = float(delay_sec)
        if outcome == "timeout":
            target_delay = float(max(delay_sec, int(self.settings.payment_timeout_sec) + 2))

        while time.monotonic() - started_at < target_delay:
            if self._cancel_event.wait(timeout=0.1):
                self._cancel_event.clear()
                self._set_flow(
                    PaymentStatus.CANCELLED,
                    is_busy=False,
                    message="MOCK payment cancelled",
                    order_id=order_id,
                )
                return PaymentResult(
                    status=PaymentStatus.CANCELLED,
                    order_id=order_id,
                    amount_cents=amount_cents,
                    currency=currency,
                    provider=PaymentProviderType.MOCK,
                    message="Mock payment cancelled by operator",
                    raw_response={"outcome": "cancelled_by_operator"},
                )

        if outcome == "approve":
            transaction_id = f"mock-{uuid.uuid4().hex[:12]}"
            provider_reference = f"MOCK-{uuid.uuid4().hex[:8].upper()}"
            approval_code = uuid.uuid4().hex[:6].upper()
            self._cancel_event.clear()
            self._set_flow(
                PaymentStatus.APPROVED,
                is_busy=False,
                message="MOCK payment approved",
                order_id=order_id,
            )
            return PaymentResult(
                status=PaymentStatus.APPROVED,
                order_id=order_id,
                amount_cents=amount_cents,
                currency=currency,
                provider=PaymentProviderType.MOCK,
                transaction_id=transaction_id,
                provider_reference=provider_reference,
                approval_code=approval_code,
                card_brand="VISA",
                last4_masked="1111",
                message="Mock payment approved",
                raw_response={
                    "outcome": "approved",
                    "transaction_id": transaction_id,
                    "provider_reference": provider_reference,
                    "approval_code": approval_code,
                    "card_brand": "VISA",
                    "last4": "1111",
                },
            )
        if outcome == "decline":
            self._cancel_event.clear()
            self._set_flow(
                PaymentStatus.DECLINED,
                is_busy=False,
                message="MOCK payment declined",
                order_id=order_id,
            )
            return PaymentResult(
                status=PaymentStatus.DECLINED,
                order_id=order_id,
                amount_cents=amount_cents,
                currency=currency,
                provider=PaymentProviderType.MOCK,
                error_code="MOCK_DECLINED",
                error_message="Mock payment declined",
                message="Mock payment declined",
                raw_response={"outcome": "declined"},
            )
        if outcome == "cancel":
            self._cancel_event.clear()
            self._set_flow(
                PaymentStatus.CANCELLED,
                is_busy=False,
                message="MOCK payment cancelled",
                order_id=order_id,
            )
            return PaymentResult(
                status=PaymentStatus.CANCELLED,
                order_id=order_id,
                amount_cents=amount_cents,
                currency=currency,
                provider=PaymentProviderType.MOCK,
                error_code="MOCK_CANCELLED",
                error_message="Mock payment cancelled",
                message="Mock payment cancelled",
                raw_response={"outcome": "cancelled"},
            )

        self._cancel_event.clear()
        self._set_flow(
            PaymentStatus.TIMEOUT,
            is_busy=False,
            message="MOCK payment timed out",
            order_id=order_id,
        )
        return PaymentResult(
            status=PaymentStatus.TIMEOUT,
            order_id=order_id,
            amount_cents=amount_cents,
            currency=currency,
            provider=PaymentProviderType.MOCK,
            error_code="MOCK_TIMEOUT",
            error_message="Mock payment timed out",
            message="Mock payment timed out",
            raw_response={"outcome": "timeout"},
        )

    def cancel_current(self, reason: str = "user_cancelled") -> PaymentResult:
        self._cancel_event.set()
        flow = self.get_flow_state()
        return PaymentResult(
            status=PaymentStatus.CANCELLED,
            order_id=flow.current_order_id,
            amount_cents=0,
            currency=self.settings.currency,
            provider=PaymentProviderType.MOCK,
            error_code="MOCK_CANCEL_REQUESTED",
            error_message=str(reason or "user_cancelled"),
            message="Mock cancellation requested",
            raw_response={"reason": str(reason or "user_cancelled")},
        )

    def void(self, transaction_id: str, amount_cents: int | None = None) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.VOIDED,
            order_id="",
            amount_cents=int(amount_cents or 0),
            currency=self.settings.currency,
            provider=PaymentProviderType.MOCK,
            transaction_id=str(transaction_id or ""),
            message="Mock void completed",
            raw_response={"action": "void", "transaction_id": str(transaction_id or "")},
        )

    def refund(self, transaction_id: str, amount_cents: int) -> PaymentResult:
        return PaymentResult(
            status=PaymentStatus.REFUNDED,
            order_id="",
            amount_cents=int(amount_cents),
            currency=self.settings.currency,
            provider=PaymentProviderType.MOCK,
            transaction_id=str(transaction_id or ""),
            message="Mock refund completed",
            raw_response={"action": "refund", "transaction_id": str(transaction_id or "")},
        )

    def get_flow_state(self) -> FlowStateResult:
        with self._lock:
            return FlowStateResult(
                provider=self._flow_state.provider,
                status=self._flow_state.status,
                is_busy=bool(self._flow_state.is_busy),
                message=str(self._flow_state.message or ""),
                current_order_id=str(self._flow_state.current_order_id or ""),
                terminal_name=str(self._flow_state.terminal_name or ""),
                terminal_ip=str(self._flow_state.terminal_ip or ""),
                cancellable=bool(self._flow_state.cancellable),
                updated_at=str(self._flow_state.updated_at or now_iso()),
                metadata=dict(self._flow_state.metadata or {}),
            )

    def close(self) -> None:
        self._cancel_event.set()
        self._set_flow(PaymentStatus.IDLE, is_busy=False, message="MOCK provider closed")
