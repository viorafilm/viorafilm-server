from __future__ import annotations

import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from .models import PaymentResult, PaymentTransactionRecord

SENSITIVE_KEYS = {
    "pan",
    "card_number",
    "cardnumber",
    "full_card_number",
    "track1",
    "track2",
    "track_data",
    "trackdata",
    "cvv",
    "cvc",
    "expiry",
    "exp_month",
    "exp_year",
}


def mask_sensitive_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        masked: dict[str, Any] = {}
        for key, value in payload.items():
            key_text = str(key or "").strip().lower()
            if key_text in SENSITIVE_KEYS:
                masked[key] = "***"
            else:
                masked[key] = mask_sensitive_payload(value)
        return masked
    if isinstance(payload, list):
        return [mask_sensitive_payload(item) for item in payload]
    if isinstance(payload, str):
        compact = re.sub(r"[\s-]+", "", payload)
        if compact.isdigit() and 12 <= len(compact) <= 19:
            return "***"
        return payload
    return payload


class PaymentStore:
    def __init__(self, db_path: str | Path, logger=None) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._logger = logger
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _connection(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._lock, self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL,
                    terminal_ip TEXT,
                    request_ref TEXT NOT NULL UNIQUE,
                    provider_transaction_id TEXT,
                    provider_reference TEXT,
                    approval_code TEXT,
                    card_brand TEXT,
                    last4_masked TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    raw_response_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    order_state TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_payment_transactions_order_id ON payment_transactions(order_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(status)"
            )
            self._ensure_column(conn, "payment_transactions", "order_state", "TEXT")
            conn.commit()

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing = {
            str(row["name"]).strip().lower()
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column.strip().lower() not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def save_record(self, record: PaymentTransactionRecord) -> PaymentTransactionRecord:
        payload = {
            "order_id": str(record.order_id or "").strip(),
            "provider": str(record.provider or "").strip(),
            "amount_cents": int(record.amount_cents),
            "currency": str(record.currency or "").strip().upper(),
            "status": str(record.status or "").strip(),
            "terminal_ip": str(record.terminal_ip or "").strip(),
            "request_ref": str(record.request_ref or "").strip(),
            "provider_transaction_id": str(record.provider_transaction_id or "").strip(),
            "provider_reference": str(record.provider_reference or "").strip(),
            "approval_code": str(record.approval_code or "").strip(),
            "card_brand": str(record.card_brand or "").strip(),
            "last4_masked": str(record.last4_masked or "").strip() or None,
            "error_code": str(record.error_code or "").strip(),
            "error_message": str(record.error_message or "").strip(),
            "raw_response_json": str(record.raw_response_json or "").strip(),
            "created_at": str(record.created_at or ""),
            "updated_at": str(record.updated_at or ""),
            "order_state": str(record.order_state or "").strip(),
        }
        if not payload["request_ref"]:
            raise ValueError("request_ref is required")
        with self._lock, self._connection() as conn:
            conn.execute(
                """
                INSERT INTO payment_transactions (
                    order_id, provider, amount_cents, currency, status, terminal_ip, request_ref,
                    provider_transaction_id, provider_reference, approval_code, card_brand, last4_masked,
                    error_code, error_message, raw_response_json, created_at, updated_at, order_state
                ) VALUES (
                    :order_id, :provider, :amount_cents, :currency, :status, :terminal_ip, :request_ref,
                    :provider_transaction_id, :provider_reference, :approval_code, :card_brand, :last4_masked,
                    :error_code, :error_message, :raw_response_json, :created_at, :updated_at, :order_state
                )
                ON CONFLICT(request_ref) DO UPDATE SET
                    order_id=excluded.order_id,
                    provider=excluded.provider,
                    amount_cents=excluded.amount_cents,
                    currency=excluded.currency,
                    status=excluded.status,
                    terminal_ip=excluded.terminal_ip,
                    provider_transaction_id=excluded.provider_transaction_id,
                    provider_reference=excluded.provider_reference,
                    approval_code=excluded.approval_code,
                    card_brand=excluded.card_brand,
                    last4_masked=excluded.last4_masked,
                    error_code=excluded.error_code,
                    error_message=excluded.error_message,
                    raw_response_json=excluded.raw_response_json,
                    updated_at=excluded.updated_at,
                    order_state=excluded.order_state
                """,
                payload,
            )
            row = conn.execute(
                "SELECT * FROM payment_transactions WHERE request_ref = ?",
                (payload["request_ref"],),
            ).fetchone()
            conn.commit()
        return self._row_to_record(row)

    def create_record_from_result(
        self,
        result: PaymentResult,
        *,
        terminal_ip: str = "",
        order_state: str = "",
    ) -> PaymentTransactionRecord:
        raw_payload = mask_sensitive_payload(result.raw_response)
        try:
            raw_json = json.dumps(raw_payload, ensure_ascii=False, sort_keys=True)
        except Exception:
            raw_json = "{}"
        return PaymentTransactionRecord(
            id=None,
            order_id=str(result.order_id or "").strip(),
            provider=str(result.provider.value),
            amount_cents=int(result.amount_cents),
            currency=str(result.currency or "").strip().upper(),
            status=str(result.status.value),
            terminal_ip=str(terminal_ip or "").strip(),
            request_ref=str(result.request_ref or "").strip(),
            provider_transaction_id=str(result.transaction_id or "").strip(),
            provider_reference=str(result.provider_reference or "").strip(),
            approval_code=str(result.approval_code or "").strip(),
            card_brand=str(result.card_brand or "").strip(),
            last4_masked=str(result.last4_masked or "").strip() or None,
            error_code=str(result.error_code or "").strip(),
            error_message=str(result.error_message or result.message or "").strip(),
            raw_response_json=raw_json,
            created_at=str(result.created_at or ""),
            updated_at=str(result.completed_at or result.created_at or ""),
            order_state=str(order_state or result.order_state or "").strip(),
        )

    def get_latest_by_order_id(self, order_id: str) -> Optional[PaymentTransactionRecord]:
        with self._lock, self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM payment_transactions
                WHERE order_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (str(order_id or "").strip(),),
            ).fetchone()
        return self._row_to_record(row) if row else None

    def get_recent_transactions(self, limit: int = 20) -> list[PaymentTransactionRecord]:
        with self._lock, self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM payment_transactions
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_incomplete_transactions(self) -> list[PaymentTransactionRecord]:
        with self._lock, self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM payment_transactions
                WHERE status IN ('PENDING', 'PROCESSING')
                ORDER BY id DESC
                """
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def get_last_error(self) -> Optional[PaymentTransactionRecord]:
        with self._lock, self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM payment_transactions
                WHERE status IN ('ERROR', 'DECLINED', 'CANCELLED', 'TIMEOUT')
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        return self._row_to_record(row) if row else None

    def update_order_state(self, order_id: str, order_state: str, *, status: Optional[str] = None) -> None:
        with self._lock, self._connection() as conn:
            if status:
                conn.execute(
                    """
                    UPDATE payment_transactions
                    SET order_state = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT id
                        FROM payment_transactions
                        WHERE order_id = ?
                        ORDER BY id DESC
                        LIMIT 1
                    )
                    """,
                    (str(order_state or "").strip(), str(status or "").strip(), str(order_id or "").strip()),
                )
            else:
                conn.execute(
                    """
                    UPDATE payment_transactions
                    SET order_state = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT id
                        FROM payment_transactions
                        WHERE order_id = ?
                        ORDER BY id DESC
                        LIMIT 1
                    )
                    """,
                    (str(order_state or "").strip(), str(order_id or "").strip()),
                )
            conn.commit()

    @staticmethod
    def _row_to_record(row: sqlite3.Row | None) -> PaymentTransactionRecord:
        if row is None:
            raise ValueError("row is required")
        return PaymentTransactionRecord(
            id=int(row["id"]) if row["id"] is not None else None,
            order_id=str(row["order_id"] or ""),
            provider=str(row["provider"] or ""),
            amount_cents=int(row["amount_cents"] or 0),
            currency=str(row["currency"] or ""),
            status=str(row["status"] or ""),
            terminal_ip=str(row["terminal_ip"] or ""),
            request_ref=str(row["request_ref"] or ""),
            provider_transaction_id=str(row["provider_transaction_id"] or ""),
            provider_reference=str(row["provider_reference"] or ""),
            approval_code=str(row["approval_code"] or ""),
            card_brand=str(row["card_brand"] or ""),
            last4_masked=str(row["last4_masked"] or "").strip() or None,
            error_code=str(row["error_code"] or ""),
            error_message=str(row["error_message"] or ""),
            raw_response_json=str(row["raw_response_json"] or ""),
            created_at=str(row["created_at"] or ""),
            updated_at=str(row["updated_at"] or ""),
            order_state=str(row["order_state"] or ""),
        )
