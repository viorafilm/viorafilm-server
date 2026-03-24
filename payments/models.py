from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class PaymentStatus(str, Enum):
    IDLE = "IDLE"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    REFUNDED = "REFUNDED"
    VOIDED = "VOIDED"


class PaymentProviderType(str, Enum):
    MOCK = "mock"
    GODADDY_POSBRIDGE = "godaddy_posbridge"
    EVCAT_TCP = "evcat_tcp"


class OrderFlowState(str, Enum):
    CART = "CART"
    CHECKOUT = "CHECKOUT"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    PAYMENT_APPROVED = "PAYMENT_APPROVED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PHOTO_SESSION = "PHOTO_SESSION"
    PRINTING = "PRINTING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


@dataclass
class PaymentSettings:
    payment_enabled: bool = False
    payment_provider: PaymentProviderType = PaymentProviderType.MOCK
    terminal_ip: str = ""
    terminal_port: int = 55555
    terminal_name: str = ""
    pairing_code_or_key: str = ""
    currency: str = "CAD"
    request_timeout_ms: int = 5000
    payment_timeout_sec: int = 60
    simulation_auto_approve: bool = True
    simulation_delay_sec: int = 2
    simulation_result: str = "approve"
    auto_print_receipt: bool = False
    enable_diagnostics_panel: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: object) -> "PaymentSettings":
        data = payload if isinstance(payload, dict) else {}

        raw_provider = str(data.get("payment_provider", PaymentProviderType.MOCK.value)).strip().lower()
        provider = PaymentProviderType.MOCK
        if raw_provider == PaymentProviderType.GODADDY_POSBRIDGE.value:
            provider = PaymentProviderType.GODADDY_POSBRIDGE
        elif raw_provider == PaymentProviderType.EVCAT_TCP.value:
            provider = PaymentProviderType.EVCAT_TCP

        try:
            terminal_port = int(data.get("terminal_port", 55555))
        except Exception:
            terminal_port = 55555
        terminal_port = max(1, min(65535, terminal_port))

        try:
            request_timeout_ms = int(data.get("request_timeout_ms", 5000))
        except Exception:
            request_timeout_ms = 5000
        request_timeout_ms = max(250, min(300000, request_timeout_ms))

        try:
            payment_timeout_sec = int(data.get("payment_timeout_sec", 60))
        except Exception:
            payment_timeout_sec = 60
        payment_timeout_sec = max(1, min(600, payment_timeout_sec))

        try:
            simulation_delay_sec = int(data.get("simulation_delay_sec", 2))
        except Exception:
            simulation_delay_sec = 2
        simulation_delay_sec = max(0, min(120, simulation_delay_sec))

        simulation_result = str(data.get("simulation_result", "approve")).strip().lower()
        if simulation_result not in {"approve", "decline", "cancel", "timeout"}:
            simulation_result = "approve"

        extra = data.get("extra")
        if not isinstance(extra, dict):
            extra = {}

        return cls(
            payment_enabled=bool(data.get("payment_enabled", False)),
            payment_provider=provider,
            terminal_ip=str(data.get("terminal_ip", "")).strip(),
            terminal_port=terminal_port,
            terminal_name=str(data.get("terminal_name", "")).strip(),
            pairing_code_or_key=str(data.get("pairing_code_or_key", "")).strip(),
            currency=str(data.get("currency", "CAD")).strip().upper() or "CAD",
            request_timeout_ms=request_timeout_ms,
            payment_timeout_sec=payment_timeout_sec,
            simulation_auto_approve=bool(data.get("simulation_auto_approve", True)),
            simulation_delay_sec=simulation_delay_sec,
            simulation_result=simulation_result,
            auto_print_receipt=bool(data.get("auto_print_receipt", False)),
            enable_diagnostics_panel=bool(data.get("enable_diagnostics_panel", True)),
            extra=dict(extra),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_enabled": bool(self.payment_enabled),
            "payment_provider": str(self.payment_provider.value),
            "terminal_ip": str(self.terminal_ip or ""),
            "terminal_port": int(self.terminal_port),
            "terminal_name": str(self.terminal_name or ""),
            "pairing_code_or_key": str(self.pairing_code_or_key or ""),
            "currency": str(self.currency or "CAD").upper(),
            "request_timeout_ms": int(self.request_timeout_ms),
            "payment_timeout_sec": int(self.payment_timeout_sec),
            "simulation_auto_approve": bool(self.simulation_auto_approve),
            "simulation_delay_sec": int(self.simulation_delay_sec),
            "simulation_result": str(self.simulation_result or "approve"),
            "auto_print_receipt": bool(self.auto_print_receipt),
            "enable_diagnostics_panel": bool(self.enable_diagnostics_panel),
            "extra": dict(self.extra or {}),
        }

    def clone(self, **changes: Any) -> "PaymentSettings":
        payload = self.to_dict()
        payload.update(changes)
        return PaymentSettings.from_dict(payload)


ZERO_DECIMAL_CURRENCIES = {
    "BIF",
    "CLP",
    "DJF",
    "GNF",
    "JPY",
    "KMF",
    "KRW",
    "MGA",
    "PYG",
    "RWF",
    "UGX",
    "VND",
    "VUV",
    "XAF",
    "XOF",
    "XPF",
}


def is_zero_decimal_currency(currency: object) -> bool:
    return str(currency or "").strip().upper() in ZERO_DECIMAL_CURRENCIES


def amount_to_major_units(amount_cents: int, currency: object) -> int:
    value = max(0, int(amount_cents or 0))
    if is_zero_decimal_currency(currency):
        return value
    return int(round(value / 100.0))


def format_amount_for_display(amount_cents: int, currency: object) -> str:
    value = max(0, int(amount_cents or 0))
    code = str(currency or "").strip().upper()
    if is_zero_decimal_currency(code):
        return f"{value} {code}".strip()
    return f"{value / 100:.2f} {code}".strip()


@dataclass
class PaymentRequest:
    order_id: str
    amount_cents: int
    currency: str
    description: str
    request_ref: str
    session_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymentResult:
    status: PaymentStatus
    order_id: str
    amount_cents: int
    currency: str
    provider: PaymentProviderType
    request_ref: str = ""
    transaction_id: str = ""
    provider_reference: str = ""
    approval_code: str = ""
    card_brand: str = ""
    last4_masked: Optional[str] = None
    error_code: str = ""
    error_message: str = ""
    message: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    order_state: str = ""
    created_at: str = field(default_factory=now_iso)
    completed_at: str = field(default_factory=now_iso)

    @property
    def is_success(self) -> bool:
        return self.status == PaymentStatus.APPROVED

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            PaymentStatus.APPROVED,
            PaymentStatus.DECLINED,
            PaymentStatus.CANCELLED,
            PaymentStatus.TIMEOUT,
            PaymentStatus.ERROR,
            PaymentStatus.REFUNDED,
            PaymentStatus.VOIDED,
        }


@dataclass
class PairResult:
    success: bool
    provider: PaymentProviderType
    message: str = ""
    terminal_name: str = ""
    terminal_ip: str = ""
    error_code: str = ""
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PingResult:
    success: bool
    provider: PaymentProviderType
    message: str = ""
    terminal_name: str = ""
    terminal_ip: str = ""
    latency_ms: Optional[int] = None
    error_code: str = ""
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowStateResult:
    provider: PaymentProviderType
    status: PaymentStatus = PaymentStatus.IDLE
    is_busy: bool = False
    message: str = ""
    current_order_id: str = ""
    terminal_name: str = ""
    terminal_ip: str = ""
    cancellable: bool = False
    updated_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymentTransactionRecord:
    id: Optional[int]
    order_id: str
    provider: str
    amount_cents: int
    currency: str
    status: str
    terminal_ip: str
    request_ref: str
    provider_transaction_id: str = ""
    provider_reference: str = ""
    approval_code: str = ""
    card_brand: str = ""
    last4_masked: Optional[str] = None
    error_code: str = ""
    error_message: str = ""
    raw_response_json: str = ""
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    order_state: str = ""
