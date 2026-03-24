from __future__ import annotations

import logging
import queue
import threading
import time
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Optional

from .base import PaymentProvider
from .evcat_tcp_provider import EvcatTcpProvider
from .diagnostics import build_diagnostics_report
from .godaddy_posbridge_provider import GoDaddyPosBridgeProvider
from .mock_provider import MockPaymentProvider
from .models import (
    FlowStateResult,
    OrderFlowState,
    PairResult,
    PaymentProviderType,
    PaymentRequest,
    PaymentResult,
    PaymentSettings,
    PaymentStatus,
    PingResult,
)
from .store import PaymentStore

PaymentUpdateCallback = Callable[[FlowStateResult], None]
PaymentCompleteCallback = Callable[[PaymentResult], None]


def _build_payment_logger(log_dir: str | Path) -> tuple[logging.Logger, Path]:
    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = target_dir / "payments.log"
    logger_name = f"payments.{str(log_path).lower()}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger, log_path


class PaymentService:
    def __init__(self, settings: PaymentSettings | dict, db_path: str | Path, log_dir: str | Path) -> None:
        self._lock = threading.RLock()
        self._logger, self._log_path = _build_payment_logger(log_dir)
        self.store = PaymentStore(db_path, logger=self._logger)
        self.settings = PaymentSettings.from_dict(settings if isinstance(settings, dict) else settings.to_dict())
        self.provider = self._create_provider(self.settings.payment_provider)
        self.provider.initialize(self.settings)
        self._active_request: Optional[PaymentRequest] = None
        self._active_thread: Optional[threading.Thread] = None
        self._active_order_state = OrderFlowState.CHECKOUT.value
        self._last_error_message = ""
        self._recovery_records = self.store.get_incomplete_transactions()
        if self._recovery_records:
            self._logger.warning(
                "payment recovery required count=%s orders=%s",
                len(self._recovery_records),
                ",".join(record.order_id for record in self._recovery_records),
            )

    @property
    def log_path(self) -> Path:
        return self._log_path

    def _create_provider(self, provider_type: PaymentProviderType) -> PaymentProvider:
        if provider_type == PaymentProviderType.GODADDY_POSBRIDGE:
            return GoDaddyPosBridgeProvider()
        if provider_type == PaymentProviderType.EVCAT_TCP:
            return EvcatTcpProvider()
        return MockPaymentProvider()

    def close(self) -> None:
        thread: Optional[threading.Thread] = None
        with self._lock:
            thread = self._active_thread
            self.provider.close()
        if thread is not None and thread.is_alive():
            try:
                thread.join(timeout=2.5)
            except Exception:
                pass
        logger = self._logger
        for handler in list(logger.handlers):
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass
            try:
                logger.removeHandler(handler)
            except Exception:
                pass

    def reconfigure(self, settings: PaymentSettings | dict) -> PaymentSettings:
        normalized = PaymentSettings.from_dict(settings if isinstance(settings, dict) else settings.to_dict())
        with self._lock:
            if self._active_request is not None:
                raise RuntimeError("payment in progress")
            try:
                self.provider.close()
            except Exception:
                pass
            self.settings = normalized
            self.provider = self._create_provider(normalized.payment_provider)
            self.provider.initialize(normalized)
        self._logger.info(
            "reconfigured provider=%s enabled=%s terminal=%s:%s",
            normalized.payment_provider.value,
            1 if normalized.payment_enabled else 0,
            normalized.terminal_ip,
            normalized.terminal_port,
        )
        return self.settings

    def get_recovery_records(self):
        return list(self._recovery_records)

    def get_recent_transactions(self, limit: int = 20):
        return self.store.get_recent_transactions(limit=limit)

    def get_last_error_record(self):
        return self.store.get_last_error()

    def get_last_error_message(self) -> str:
        return str(self._last_error_message or "")

    def pair_terminal(self) -> PairResult:
        result = self.provider.pair_terminal()
        self._logger.info(
            "pair success=%s provider=%s message=%s",
            1 if result.success else 0,
            result.provider.value,
            result.message,
        )
        return result

    def ping(self) -> PingResult:
        result = self.provider.ping()
        self._logger.info(
            "ping success=%s provider=%s message=%s latency_ms=%s",
            1 if result.success else 0,
            result.provider.value,
            result.message,
            result.latency_ms,
        )
        return result

    def get_flow_state(self) -> FlowStateResult:
        with self._lock:
            flow = self.provider.get_flow_state()
            if self._active_request is not None:
                flow.current_order_id = self._active_request.order_id
                flow.is_busy = True
                flow.cancellable = True
            return flow

    def get_diagnostics_report(self) -> str:
        return build_diagnostics_report(
            settings=self.settings,
            flow=self.get_flow_state(),
            recent_transactions=self.get_recent_transactions(limit=20),
            incomplete_transactions=self.get_recovery_records(),
            last_error=self.get_last_error_record(),
            log_path=str(self.log_path),
        )

    def read_recent_log_lines(self, limit: int = 20) -> list[str]:
        try:
            if not self.log_path.is_file():
                return []
            lines = self.log_path.read_text(encoding="utf-8").splitlines()
            return lines[-max(1, int(limit)) :]
        except Exception:
            return []

    def _notify_update(self, callback: Optional[PaymentUpdateCallback], flow_state: FlowStateResult) -> None:
        if callback is None:
            return
        try:
            callback(flow_state)
        except Exception as exc:
            self._logger.warning("update callback failed: %s", exc)

    def _notify_complete(self, callback: Optional[PaymentCompleteCallback], result: PaymentResult) -> None:
        if callback is None:
            return
        try:
            callback(result)
        except Exception as exc:
            self._logger.warning("complete callback failed: %s", exc)

    def _make_request_ref(self, order_id: str) -> str:
        return f"{str(order_id or '').strip()}-{uuid.uuid4().hex[:10]}"

    def start_sale(
        self,
        *,
        order_id: str,
        amount_cents: int,
        currency: str,
        description: str,
        session_id: Optional[str] = None,
        order_state: str = "",
        on_update: Optional[PaymentUpdateCallback] = None,
        on_complete: Optional[PaymentCompleteCallback] = None,
    ) -> tuple[bool, str]:
        normalized_order_id = str(order_id or "").strip()
        normalized_currency = str(currency or self.settings.currency).strip().upper() or self.settings.currency
        if not normalized_order_id:
            return False, "missing_order_id"
        if int(amount_cents) <= 0:
            return False, "invalid_amount"

        with self._lock:
            if not self.settings.payment_enabled:
                return False, "payment_disabled"
            if self._active_request is not None:
                return False, "payment_already_processing"
            latest = self.store.get_latest_by_order_id(normalized_order_id)
            if latest is not None and latest.status in {"APPROVED", "PENDING", "PROCESSING"}:
                return False, f"duplicate_{latest.status.lower()}"

            request = PaymentRequest(
                order_id=normalized_order_id,
                amount_cents=int(amount_cents),
                currency=normalized_currency,
                description=str(description or "").strip(),
                request_ref=self._make_request_ref(normalized_order_id),
                session_id=str(session_id or "").strip() or None,
            )
            self._active_request = request
            self._active_order_state = str(order_state or OrderFlowState.PAYMENT_PENDING.value)

            pending_result = PaymentResult(
                status=PaymentStatus.PENDING,
                order_id=request.order_id,
                amount_cents=request.amount_cents,
                currency=request.currency,
                provider=self.settings.payment_provider,
                request_ref=request.request_ref,
                message="Payment queued",
                order_state=self._active_order_state,
            )
            pending_record = self.store.create_record_from_result(
                pending_result,
                terminal_ip=self.settings.terminal_ip,
                order_state=self._active_order_state,
            )
            self.store.save_record(pending_record)

            self._logger.info(
                "sale request order=%s request_ref=%s provider=%s amount_cents=%s currency=%s",
                request.order_id,
                request.request_ref,
                self.settings.payment_provider.value,
                request.amount_cents,
                request.currency,
            )
            self._notify_update(
                on_update,
                FlowStateResult(
                    provider=self.settings.payment_provider,
                    status=PaymentStatus.PENDING,
                    is_busy=True,
                    message="결제 요청 준비중 / Preparing payment",
                    current_order_id=request.order_id,
                    terminal_name=self.settings.terminal_name,
                    terminal_ip=self.settings.terminal_ip,
                    cancellable=True,
                ),
            )

            worker = threading.Thread(
                target=self._sale_worker,
                args=(request, on_update, on_complete),
                daemon=True,
                name=f"payment-sale-{request.order_id}",
            )
            self._active_thread = worker
            worker.start()
        return True, request.request_ref

    def _run_provider_sale_with_timeout(self, request: PaymentRequest) -> PaymentResult:
        result_queue: queue.Queue[PaymentResult | Exception] = queue.Queue(maxsize=1)

        def _runner() -> None:
            try:
                result_queue.put(
                    self.provider.sale(
                        request.order_id,
                        request.amount_cents,
                        request.currency,
                        request.description,
                    )
                )
            except Exception as exc:
                result_queue.put(exc)

        thread = threading.Thread(
            target=_runner,
            daemon=True,
            name=f"payment-provider-{request.order_id}",
        )
        thread.start()

        timeout_deadline = time.monotonic() + float(self.settings.payment_timeout_sec)
        while time.monotonic() < timeout_deadline:
            try:
                value = result_queue.get(timeout=0.1)
                if isinstance(value, Exception):
                    raise value
                return value
            except queue.Empty:
                continue

        try:
            self.provider.cancel_current("timeout")
        except Exception:
            pass
        return PaymentResult(
            status=PaymentStatus.TIMEOUT,
            order_id=request.order_id,
            amount_cents=request.amount_cents,
            currency=request.currency,
            provider=self.settings.payment_provider,
            request_ref=request.request_ref,
            error_code="PAYMENT_TIMEOUT",
            error_message="Payment timed out",
            message="Payment timed out",
        )

    def _sale_worker(
        self,
        request: PaymentRequest,
        on_update: Optional[PaymentUpdateCallback],
        on_complete: Optional[PaymentCompleteCallback],
    ) -> None:
        processing_state = OrderFlowState.PAYMENT_PROCESSING.value
        self._notify_update(
            on_update,
            FlowStateResult(
                provider=self.settings.payment_provider,
                status=PaymentStatus.PENDING,
                is_busy=True,
                message="결제 대기중 / Waiting for terminal",
                current_order_id=request.order_id,
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                cancellable=True,
            ),
        )
        self.store.update_order_state(request.order_id, processing_state, status=PaymentStatus.PENDING.value)
        try:
            result = self._run_provider_sale_with_timeout(request)
        except Exception as exc:
            result = PaymentResult(
                status=PaymentStatus.ERROR,
                order_id=request.order_id,
                amount_cents=request.amount_cents,
                currency=request.currency,
                provider=self.settings.payment_provider,
                request_ref=request.request_ref,
                error_code="PAYMENT_EXCEPTION",
                error_message=str(exc),
                message=f"Payment provider raised exception: {exc}",
            )

        result.request_ref = request.request_ref
        if result.provider != self.settings.payment_provider:
            result.provider = self.settings.payment_provider
        if not result.currency:
            result.currency = request.currency
        if result.amount_cents <= 0:
            result.amount_cents = request.amount_cents
        if not result.order_id:
            result.order_id = request.order_id

        final_order_state = OrderFlowState.PAYMENT_FAILED.value
        if result.status == PaymentStatus.APPROVED:
            final_order_state = OrderFlowState.PAYMENT_APPROVED.value
        elif result.status in {PaymentStatus.CANCELLED, PaymentStatus.TIMEOUT}:
            final_order_state = OrderFlowState.ABORTED.value
        result.order_state = final_order_state

        record = self.store.create_record_from_result(
            result,
            terminal_ip=self.settings.terminal_ip,
            order_state=final_order_state,
        )
        self.store.save_record(record)

        self._logger.info(
            "sale result order=%s request_ref=%s status=%s tx=%s error=%s",
            result.order_id,
            result.request_ref,
            result.status.value,
            result.transaction_id,
            result.error_message or result.message,
        )
        if not result.is_success:
            self._last_error_message = result.error_message or result.message

        with self._lock:
            if self._active_request is not None and self._active_request.request_ref == request.request_ref:
                self._active_request = None
                self._active_thread = None
                self._active_order_state = OrderFlowState.CHECKOUT.value

        self._notify_complete(on_complete, result)

    def cancel_active_payment(self, reason: str = "user_cancelled") -> bool:
        with self._lock:
            if self._active_request is None:
                return False
            request = self._active_request
        try:
            self.provider.cancel_current(reason)
        except Exception as exc:
            self._logger.warning("cancel request failed order=%s err=%s", request.order_id, exc)
            return False
        self._logger.info("cancel requested order=%s reason=%s", request.order_id, reason)
        return True

    def mark_order_state(self, order_id: str, order_state: OrderFlowState | str) -> None:
        value = order_state.value if isinstance(order_state, OrderFlowState) else str(order_state or "").strip()
        if not value:
            return
        latest = self.store.get_latest_by_order_id(order_id)
        if latest is None:
            return
        self.store.update_order_state(order_id, value)
        self._logger.info("order state order=%s state=%s", order_id, value)

    def run_mock_diagnostic_sale(self, *, amount_cents: int = 100) -> PaymentResult:
        mock_settings = self.settings.clone(
            payment_enabled=True,
            payment_provider=PaymentProviderType.MOCK,
        )
        provider = MockPaymentProvider()
        provider.initialize(mock_settings)
        order_id = f"diag-{uuid.uuid4().hex[:8]}"
        result = provider.sale(order_id, int(amount_cents), mock_settings.currency, "Diagnostics sale")
        result.request_ref = f"{order_id}-diag"
        result.order_state = OrderFlowState.PAYMENT_APPROVED.value if result.is_success else OrderFlowState.PAYMENT_FAILED.value
        record = self.store.create_record_from_result(
            result,
            terminal_ip=mock_settings.terminal_ip,
            order_state=result.order_state,
        )
        self.store.save_record(record)
        self._logger.info(
            "diagnostic mock sale order=%s status=%s amount_cents=%s",
            order_id,
            result.status.value,
            amount_cents,
        )
        provider.close()
        return result
