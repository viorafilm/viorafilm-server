from __future__ import annotations

from typing import Iterable, Optional

from .models import FlowStateResult, PaymentSettings, PaymentTransactionRecord, format_amount_for_display


def format_flow_state(settings: PaymentSettings, flow: FlowStateResult) -> str:
    return (
        f"provider={settings.payment_provider.value}\n"
        f"enabled={1 if settings.payment_enabled else 0}\n"
        f"terminal={settings.terminal_name or '-'}\n"
        f"endpoint={settings.terminal_ip or '-'}:{int(settings.terminal_port)}\n"
        f"flow_status={flow.status.value}\n"
        f"busy={1 if flow.is_busy else 0}\n"
        f"message={flow.message or '-'}"
    )


def format_transactions(records: Iterable[PaymentTransactionRecord]) -> str:
    lines: list[str] = []
    for record in records:
        amount = format_amount_for_display(record.amount_cents, record.currency)
        lines.append(
            f"{record.updated_at} | {record.order_id} | {record.provider} | "
            f"{record.status} | {amount} | tx={record.provider_transaction_id or '-'} | "
            f"err={record.error_message or '-'}"
        )
    return "\n".join(lines) if lines else "최근 거래 없음"


def build_diagnostics_report(
    *,
    settings: PaymentSettings,
    flow: FlowStateResult,
    recent_transactions: Iterable[PaymentTransactionRecord],
    incomplete_transactions: Iterable[PaymentTransactionRecord],
    last_error: Optional[PaymentTransactionRecord],
    log_path: str,
) -> str:
    incomplete_text = format_transactions(incomplete_transactions)
    recent_text = format_transactions(recent_transactions)
    last_error_text = "없음"
    if last_error is not None:
        last_error_text = (
            f"{last_error.updated_at} | {last_error.order_id} | "
            f"{last_error.status} | {last_error.error_message or '-'}"
        )
    return (
        "[Provider]\n"
        f"{format_flow_state(settings, flow)}\n\n"
        "[Incomplete]\n"
        f"{incomplete_text}\n\n"
        "[Recent Transactions]\n"
        f"{recent_text}\n\n"
        "[Last Error]\n"
        f"{last_error_text}\n\n"
        "[Log]\n"
        f"{log_path or '-'}"
    )
