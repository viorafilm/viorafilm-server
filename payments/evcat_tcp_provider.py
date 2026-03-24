from __future__ import annotations

import socket
import threading
import time
from typing import Any, Optional

from .base import PaymentProvider
from .models import (
    FlowStateResult,
    PairResult,
    PaymentProviderType,
    PaymentResult,
    PaymentSettings,
    PaymentStatus,
    PingResult,
    amount_to_major_units,
    now_iso,
)

_CH_BEL = chr(7)
_CH_ACK = chr(6)
_CH_CR = chr(13)
_CH_ETX = chr(3)
_CH_FS = chr(28)

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 26269


class EvcatTcpProvider(PaymentProvider):
    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.RLock()
        self._cancel_event = threading.Event()
        self._flow_state = FlowStateResult(provider=PaymentProviderType.EVCAT_TCP)
        self._active_socket: Optional[socket.socket] = None

    def initialize(self, settings: PaymentSettings) -> None:
        terminal_ip = str(settings.terminal_ip or "").strip() or _DEFAULT_HOST
        terminal_port = int(settings.terminal_port or 0)
        if terminal_port <= 0 or terminal_port == 55555:
            terminal_port = _DEFAULT_PORT
        currency = str(settings.currency or "").strip().upper() or "KRW"
        terminal_name = str(settings.terminal_name or "").strip() or "EVCAT3"
        self.settings = settings.clone(
            payment_provider=PaymentProviderType.EVCAT_TCP,
            terminal_ip=terminal_ip,
            terminal_port=terminal_port,
            terminal_name=terminal_name,
            currency=currency,
        )
        self._cancel_event.clear()
        self._set_flow(
            PaymentStatus.IDLE,
            is_busy=False,
            message=f"EVCAT ready ({self.settings.terminal_ip}:{self.settings.terminal_port})",
        )

    def _set_flow(
        self,
        status: PaymentStatus,
        *,
        is_busy: bool,
        message: str,
        order_id: str = "",
        cancellable: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            self._flow_state = FlowStateResult(
                provider=PaymentProviderType.EVCAT_TCP,
                status=status,
                is_busy=is_busy,
                message=str(message or ""),
                current_order_id=str(order_id or ""),
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                cancellable=cancellable,
                updated_at=now_iso(),
                metadata=dict(metadata or {}),
            )

    @staticmethod
    def _encode_text(text: str) -> bytes:
        for encoding in ("cp949", "euc-kr", "utf-8"):
            try:
                return text.encode(encoding)
            except Exception:
                continue
        return text.encode("utf-8", errors="replace")

    @staticmethod
    def _decode_bytes(payload: bytes) -> str:
        for encoding in ("cp949", "euc-kr", "utf-8"):
            try:
                return payload.decode(encoding)
            except Exception:
                continue
        return payload.decode("utf-8", errors="replace")

    @classmethod
    def _build_request(cls, control_code: str, action_code: str, fields: list[object]) -> bytes:
        normalized_fields = []
        for item in fields:
            if item is None:
                normalized_fields.append("")
            else:
                normalized_fields.append(str(item))
        body = _CH_FS.join(
            [str(control_code or "").strip(), str(action_code or "").strip(), *normalized_fields]
        )
        return cls._encode_text(f"{_CH_BEL}{_CH_ACK}{body}{_CH_ACK}{_CH_CR}")

    @staticmethod
    def _strip_envelope(text: str) -> str:
        data = str(text or "")
        if data.startswith(_CH_BEL):
            data = data[1:]
        if data.endswith(_CH_ETX):
            data = data[:-1]
        return data

    @staticmethod
    def _safe_int(value: object, default: int = 0) -> int:
        try:
            return int(str(value or "").strip())
        except Exception:
            return default

    def _request_simple(self, control_code: str, action_code: str, fields: Optional[list[object]] = None, timeout_sec: float = 5.0) -> str:
        response = self._send_and_receive(
            self._build_request(control_code, action_code, list(fields or [])),
            timeout_sec=timeout_sec,
        )
        return self._decode_bytes(response)

    def _connect_socket(self, timeout_sec: float) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(max(0.25, float(timeout_sec)))
        sock.connect((self.settings.terminal_ip, int(self.settings.terminal_port)))
        return sock

    def _send_and_receive(self, payload: bytes, *, timeout_sec: float) -> bytes:
        deadline = time.monotonic() + max(0.5, float(timeout_sec))
        chunks: list[bytes] = []
        sock: Optional[socket.socket] = None
        try:
            sock = self._connect_socket(timeout_sec=timeout_sec)
            with self._lock:
                self._active_socket = sock
            sock.sendall(payload)
            while time.monotonic() < deadline:
                if self._cancel_event.is_set():
                    raise RuntimeError("payment_cancelled")
                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    if chunks:
                        break
                    continue
                chunks.append(chunk)
                if _CH_ETX.encode("ascii") in chunk:
                    break
            if not chunks:
                raise TimeoutError("EVCAT response timeout")
            data = b"".join(chunks)
            etx_index = data.find(_CH_ETX.encode("ascii"))
            if etx_index >= 0:
                data = data[: etx_index + 1]
            return data
        finally:
            with self._lock:
                self._active_socket = None
            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass

    @classmethod
    def _parse_response(cls, raw_text: str) -> dict[str, Any]:
        body = cls._strip_envelope(raw_text)
        parts = body.split(_CH_ACK, 3)
        if len(parts) < 4:
            return {
                "kind": "unknown",
                "raw_text": raw_text,
                "body": body,
                "message": body.strip(),
            }
        user_code, status_flag, process_code, tail = parts
        status_flag = str(status_flag or "").strip()
        process_code = str(process_code or "").strip()
        if _CH_FS not in tail:
            return {
                "kind": "control",
                "raw_text": raw_text,
                "body": body,
                "user_code": str(user_code or "").strip(),
                "status_flag": status_flag,
                "process_code": process_code,
                "message": str(tail or "").strip(),
            }

        fs_fields = tail.split(_CH_FS)
        response_code = str(fs_fields[0] if fs_fields else "").strip()
        data = fs_fields[1:]

        def _field(index: int) -> str:
            if index < len(data):
                return str(data[index] or "").strip()
            return ""

        return {
            "kind": "payment",
            "raw_text": raw_text,
            "body": body,
            "user_code": str(user_code or "").strip(),
            "status_flag": status_flag,
            "process_code": process_code,
            "response_code": response_code,
            "payment_type": _field(0),
            "payment_medium": _field(1),
            "approved_date": _field(2),
            "approved_time": _field(3),
            "card_number": _field(4),
            "approval_number": _field(5),
            "merchant_number": _field(6),
            "acquirer_type": _field(7),
            "issuer_code": _field(8),
            "issuer_name": _field(9),
            "acquirer_code": _field(10),
            "acquirer_name": _field(11),
            "response_message": _field(12),
            "prepaid_balance": _field(13),
            "extra_data": _field(14),
            "echo_user_code": _field(15),
            "approved_amount": _field(16),
            "approved_vat": _field(17),
            "pos_id": _field(18),
            "message_serial": _field(19),
            "pg_transaction_id": _field(20),
            "receipt_number": _field(21),
            "installment": _field(22),
            "qr_name": _field(23),
            "qr_value": _field(24),
            "fields": data,
        }

    def _evcat_message(self, parsed: dict[str, Any]) -> str:
        return (
            str(parsed.get("response_message") or "").strip()
            or str(parsed.get("message") or "").strip()
            or str(parsed.get("body") or "").strip()
            or "EVCAT response received"
        )

    def _approval_status(self, parsed: dict[str, Any]) -> PaymentStatus:
        status_flag = str(parsed.get("status_flag") or "").strip().upper()
        response_code = str(parsed.get("response_code") or "").strip().upper()
        if status_flag == "Y" and response_code == "00":
            return PaymentStatus.APPROVED
        if status_flag == "N":
            return PaymentStatus.DECLINED
        if status_flag == "E":
            return PaymentStatus.ERROR
        return PaymentStatus.ERROR

    def _approval_fields(self, order_id: str, amount_major: int) -> list[object]:
        vat_amount = self._safe_int(self.settings.extra.get("vat_amount"), int(amount_major / 11) if amount_major > 0 else 0)
        service_charge = self._safe_int(self.settings.extra.get("service_charge"), 0)
        installment_months = self._safe_int(self.settings.extra.get("installment_months"), 0)
        installment = f"{max(0, installment_months):02d}"
        multi_id = str(self.settings.extra.get("multi_id", "") or "").strip()
        qr_value = str(self.settings.extra.get("qr_value", "") or "").strip()
        qr_discount_excluded = str(self.settings.extra.get("qr_discount_excluded_amount", "") or "").strip()
        return [
            amount_major,
            vat_amount,
            service_charge,
            installment,
            "",
            "",
            "",
            "",
            "",
            str(order_id or "").strip(),
            "",
            "",
            "",
            multi_id,
            qr_value,
            qr_discount_excluded,
        ]

    def pair_terminal(self) -> PairResult:
        try:
            raw = self._request_simple("7700", "0000", timeout_sec=max(1.0, self.settings.request_timeout_ms / 1000.0))
            parsed = self._parse_response(raw)
            message = str(parsed.get("message") or "").strip()
            pieces = message.split("\t") if message else []
            metadata = {
                "cat_id": pieces[0].strip() if len(pieces) > 0 else "",
                "biz_no": pieces[1].strip() if len(pieces) > 1 else "",
                "van_or_pg": pieces[2].strip() if len(pieces) > 2 else "",
                "biz_name": pieces[3].strip() if len(pieces) > 3 else "",
            }
            display = metadata["biz_name"] or self.settings.terminal_name
            self._set_flow(
                PaymentStatus.IDLE,
                is_busy=False,
                message=display or "EVCAT settings ok",
                metadata=metadata,
            )
            return PairResult(
                success=True,
                provider=PaymentProviderType.EVCAT_TCP,
                message=display or "EVCAT settings ok",
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                metadata=metadata,
            )
        except Exception as exc:
            error_text = str(exc or "EVCAT settings read failed")
            self._set_flow(PaymentStatus.ERROR, is_busy=False, message=error_text)
            return PairResult(
                success=False,
                provider=PaymentProviderType.EVCAT_TCP,
                message=error_text,
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                error_code="EVCAT_PAIR_FAILED",
                error_message=error_text,
            )

    def ping(self) -> PingResult:
        started = time.monotonic()
        try:
            raw = self._request_simple("8899", "0000", timeout_sec=max(1.0, self.settings.request_timeout_ms / 1000.0))
            parsed = self._parse_response(raw)
            message = str(parsed.get("message") or "").strip()
            success = message.upper() == "LIVE"
            latency_ms = int((time.monotonic() - started) * 1000)
            self._set_flow(
                PaymentStatus.IDLE if success else PaymentStatus.ERROR,
                is_busy=False,
                message=message or ("LIVE" if success else "EVCAT ping failed"),
            )
            return PingResult(
                success=success,
                provider=PaymentProviderType.EVCAT_TCP,
                message=message or ("LIVE" if success else "EVCAT ping failed"),
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                latency_ms=latency_ms,
                error_code="" if success else "EVCAT_PING_FAILED",
                error_message="" if success else (message or "EVCAT ping failed"),
                metadata=parsed,
            )
        except Exception as exc:
            error_text = str(exc or "EVCAT ping failed")
            self._set_flow(PaymentStatus.ERROR, is_busy=False, message=error_text)
            return PingResult(
                success=False,
                provider=PaymentProviderType.EVCAT_TCP,
                message=error_text,
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                error_code="EVCAT_PING_FAILED",
                error_message=error_text,
            )

    def sale(self, order_id: str, amount_cents: int, currency: str, description: str) -> PaymentResult:
        amount_major = amount_to_major_units(amount_cents, currency or self.settings.currency)
        fields = self._approval_fields(order_id=order_id, amount_major=amount_major)
        self._cancel_event.clear()
        self._set_flow(
            PaymentStatus.PENDING,
            is_busy=True,
            message="카드 입력 대기중 / Waiting for card",
            order_id=order_id,
            cancellable=True,
            metadata={"description": str(description or "")},
        )
        try:
            raw = self._send_and_receive(
                self._build_request("1000", "1100", fields),
                timeout_sec=max(5.0, float(self.settings.payment_timeout_sec) + 5.0),
            )
            parsed = self._parse_response(self._decode_bytes(raw))
        except Exception as exc:
            if self._cancel_event.is_set() or str(exc) == "payment_cancelled":
                self._cancel_event.clear()
                self._set_flow(
                    PaymentStatus.CANCELLED,
                    is_busy=False,
                    message="결제 취소됨 / Payment cancelled",
                    order_id=order_id,
                )
                return PaymentResult(
                    status=PaymentStatus.CANCELLED,
                    order_id=order_id,
                    amount_cents=amount_cents,
                    currency=str(currency or self.settings.currency),
                    provider=PaymentProviderType.EVCAT_TCP,
                    error_code="EVCAT_CANCELLED",
                    error_message="Payment cancelled",
                    message="Payment cancelled",
                )
            error_text = str(exc or "EVCAT sale failed")
            self._set_flow(PaymentStatus.ERROR, is_busy=False, message=error_text, order_id=order_id)
            return PaymentResult(
                status=PaymentStatus.ERROR,
                order_id=order_id,
                amount_cents=amount_cents,
                currency=str(currency or self.settings.currency),
                provider=PaymentProviderType.EVCAT_TCP,
                error_code="EVCAT_SALE_FAILED",
                error_message=error_text,
                message=error_text,
            )

        status = self._approval_status(parsed)
        message = self._evcat_message(parsed)
        self._set_flow(status, is_busy=False, message=message, order_id=order_id)
        return PaymentResult(
            status=status,
            order_id=order_id,
            amount_cents=self._safe_int(parsed.get("approved_amount"), amount_cents),
            currency=str(currency or self.settings.currency),
            provider=PaymentProviderType.EVCAT_TCP,
            transaction_id=str(parsed.get("approval_number") or "").strip(),
            provider_reference=str(parsed.get("pg_transaction_id") or parsed.get("message_serial") or "").strip(),
            approval_code=str(parsed.get("approval_number") or "").strip(),
            card_brand=str(parsed.get("issuer_name") or parsed.get("acquirer_name") or "").strip(),
            last4_masked=str(parsed.get("card_number") or "").strip() or None,
            error_code="" if status == PaymentStatus.APPROVED else str(parsed.get("response_code") or "").strip(),
            error_message="" if status == PaymentStatus.APPROVED else message,
            message=message,
            raw_response=parsed,
            metadata={
                "approved_date": str(parsed.get("approved_date") or "").strip(),
                "approved_time": str(parsed.get("approved_time") or "").strip(),
                "payment_medium": str(parsed.get("payment_medium") or "").strip(),
                "merchant_number": str(parsed.get("merchant_number") or "").strip(),
                "pos_id": str(parsed.get("pos_id") or "").strip(),
                "message_serial": str(parsed.get("message_serial") or "").strip(),
            },
        )

    def cancel_current(self, reason: str = "user_cancelled") -> PaymentResult:
        self._cancel_event.set()
        sock: Optional[socket.socket] = None
        with self._lock:
            sock = self._active_socket
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
        flow = self.get_flow_state()
        return PaymentResult(
            status=PaymentStatus.CANCELLED,
            order_id=flow.current_order_id,
            amount_cents=0,
            currency=self.settings.currency,
            provider=PaymentProviderType.EVCAT_TCP,
            error_code="EVCAT_CANCEL_REQUESTED",
            error_message=str(reason or "user_cancelled"),
            message="EVCAT cancellation requested",
            raw_response={"reason": str(reason or "user_cancelled")},
        )

    def void(self, transaction_id: str, amount_cents: int | None = None) -> PaymentResult:
        message = "EVCAT void requires original date/approval data and is not wired in kiosk flow yet"
        return PaymentResult(
            status=PaymentStatus.ERROR,
            order_id="",
            amount_cents=int(amount_cents or 0),
            currency=self.settings.currency,
            provider=PaymentProviderType.EVCAT_TCP,
            transaction_id=str(transaction_id or ""),
            error_code="EVCAT_VOID_NOT_IMPLEMENTED",
            error_message=message,
            message=message,
        )

    def refund(self, transaction_id: str, amount_cents: int) -> PaymentResult:
        message = "EVCAT refund requires original approval metadata and is not wired in kiosk flow yet"
        return PaymentResult(
            status=PaymentStatus.ERROR,
            order_id="",
            amount_cents=int(amount_cents),
            currency=self.settings.currency,
            provider=PaymentProviderType.EVCAT_TCP,
            transaction_id=str(transaction_id or ""),
            error_code="EVCAT_REFUND_NOT_IMPLEMENTED",
            error_message=message,
            message=message,
        )

    def get_flow_state(self) -> FlowStateResult:
        with self._lock:
            return FlowStateResult(
                provider=self._flow_state.provider,
                status=self._flow_state.status,
                is_busy=bool(self._flow_state.is_busy),
                message=str(self._flow_state.message or ""),
                current_order_id=str(self._flow_state.current_order_id or ""),
                terminal_name=str(self._flow_state.terminal_name or self.settings.terminal_name or ""),
                terminal_ip=str(self._flow_state.terminal_ip or self.settings.terminal_ip or ""),
                cancellable=bool(self._flow_state.cancellable),
                updated_at=str(self._flow_state.updated_at or now_iso()),
                metadata=dict(self._flow_state.metadata or {}),
            )

    def close(self) -> None:
        self.cancel_current("provider_closed")
        self._cancel_event.clear()
        self._set_flow(PaymentStatus.IDLE, is_busy=False, message="EVCAT provider closed")
