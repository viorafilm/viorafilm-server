from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .models import (
    FlowStateResult,
    PairResult,
    PaymentResult,
    PaymentSettings,
    PingResult,
)


class PaymentProvider(ABC):
    def __init__(self) -> None:
        self.settings = PaymentSettings()

    @abstractmethod
    def initialize(self, settings: PaymentSettings) -> None:
        raise NotImplementedError

    @abstractmethod
    def pair_terminal(self) -> PairResult:
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> PingResult:
        raise NotImplementedError

    @abstractmethod
    def sale(self, order_id: str, amount_cents: int, currency: str, description: str) -> PaymentResult:
        raise NotImplementedError

    @abstractmethod
    def void(self, transaction_id: str, amount_cents: int | None = None) -> PaymentResult:
        raise NotImplementedError

    @abstractmethod
    def refund(self, transaction_id: str, amount_cents: int) -> PaymentResult:
        raise NotImplementedError

    @abstractmethod
    def get_flow_state(self) -> FlowStateResult:
        raise NotImplementedError

    def cancel_current(self, reason: str = "user_cancelled") -> Optional[PaymentResult]:
        return None

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
