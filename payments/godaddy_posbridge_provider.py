from __future__ import annotations

import json
import platform
import subprocess
import tempfile
from pathlib import Path
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
    now_iso,
)


class GoDaddyPosBridgeProvider(PaymentProvider):
    def __init__(self) -> None:
        super().__init__()
        self._flow_state = FlowStateResult(provider=PaymentProviderType.GODADDY_POSBRIDGE)
        self._sdk_dir: Optional[Path] = None
        self._bridge_script = Path(__file__).resolve().with_name("poynt_posbridge_bridge.ps1")

    def initialize(self, settings: PaymentSettings) -> None:
        self.settings = settings.clone(payment_provider=PaymentProviderType.GODADDY_POSBRIDGE)
        self._sdk_dir = self._ensure_sdk_dir(auto_extract=True)
        self._flow_state = FlowStateResult(
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            status=PaymentStatus.IDLE,
            is_busy=False,
            terminal_name=self.settings.terminal_name,
            terminal_ip=self.settings.terminal_ip,
            message=self._bridge_status_message(),
        )

    def _bridge_status_message(self) -> str:
        if platform.system().lower() != "windows":
            return "GoDaddy Smart Terminal provider is Windows-only. MOCK is available."
        if self._ensure_sdk_dir(auto_extract=False) is None and self._bridge_command("sale_command") is None:
            return (
                "Official GoDaddy/Poynt Windows SDK was not found. "
                "MOCK is available until PoyntPOSBridge.dll is installed or extracted."
            )
        if not self._bridge_script.is_file():
            return "Official SDK found but local PowerShell bridge script is missing."
        return "Official Poynt POS Bridge SDK detected"

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _vendor_sdk_dir(self) -> Path:
        return self._repo_root() / "vendor" / "poynt-pos-connector-windows-sdk" / "extracted" / "PoyntPOSBridgeSample"

    def _vendor_msi_path(self) -> Path:
        return self._repo_root() / "vendor" / "poynt-pos-connector-windows-sdk" / "PoyntPOSBridgeSampleInstaller-1.0.180.msi"

    def _installed_sdk_dir(self) -> Path:
        return Path(r"C:\Program Files (x86)\PoyntPOSBridgeSample")

    def _ensure_sdk_dir(self, *, auto_extract: bool) -> Optional[Path]:
        if self._sdk_dir is not None and (self._sdk_dir / "PoyntPOSBridge.dll").is_file():
            return self._sdk_dir
        explicit = str(self.settings.extra.get("sdk_dir", "")).strip()
        if explicit:
            candidate = Path(explicit)
            if (candidate / "PoyntPOSBridge.dll").is_file():
                self._sdk_dir = candidate
                return candidate
        for candidate in (self._vendor_sdk_dir(), self._installed_sdk_dir()):
            if (candidate / "PoyntPOSBridge.dll").is_file():
                self._sdk_dir = candidate
                return candidate
        if auto_extract and self._vendor_msi_path().is_file():
            target_root = self._vendor_sdk_dir().parent
            try:
                target_root.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    [
                        "msiexec.exe",
                        "/a",
                        str(self._vendor_msi_path()),
                        "/qn",
                        f"TARGETDIR={target_root}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=max(30, int(self.settings.request_timeout_ms / 1000) + 30),
                    check=False,
                )
            except Exception:
                pass
            if (self._vendor_sdk_dir() / "PoyntPOSBridge.dll").is_file():
                self._sdk_dir = self._vendor_sdk_dir()
                return self._sdk_dir
        return None

    def _bridge_executable(self) -> Optional[Path]:
        raw = str(self.settings.extra.get("bridge_executable", "")).strip()
        if not raw:
            return None
        candidate = Path(raw)
        return candidate if candidate.is_file() else None

    def _bridge_command(self, key: str) -> Optional[Any]:
        command = self.settings.extra.get(key)
        if isinstance(command, str) and command.strip():
            return command.strip()
        if isinstance(command, list):
            parts = [str(item).strip() for item in command if str(item).strip()]
            if parts:
                return parts
        return None

    def _execute_configured_command(
        self,
        *,
        command_key: str,
        payload: dict[str, Any],
        timeout_ms: int,
    ) -> tuple[bool, dict[str, Any], str]:
        command_template = self._bridge_command(command_key)
        if command_template is None:
            return False, {}, f"Missing configured bridge command: {command_key}"

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            payload_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)

        mapping = {
            "payload_path": str(payload_path),
            "terminal_ip": str(self.settings.terminal_ip or ""),
            "terminal_port": int(self.settings.terminal_port),
            "terminal_name": str(self.settings.terminal_name or ""),
            "pairing_key": str(self.settings.pairing_code_or_key or ""),
        }
        try:
            if isinstance(command_template, list):
                command = [str(part).format(**mapping) for part in command_template]
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=max(1, int(timeout_ms / 1000)),
                    shell=False,
                    check=False,
                )
            else:
                command = str(command_template).format(**mapping)
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=max(1, int(timeout_ms / 1000)),
                    shell=True,
                    check=False,
                )
            stdout = str(completed.stdout or "").strip()
            stderr = str(completed.stderr or "").strip()
            if completed.returncode != 0:
                return False, {}, stderr or stdout or f"Bridge exit code {completed.returncode}"
            if not stdout:
                return True, {}, ""
            try:
                parsed = json.loads(stdout)
            except Exception:
                parsed = {"message": stdout}
            return True, parsed if isinstance(parsed, dict) else {"payload": parsed}, stderr
        except Exception as exc:
            return False, {}, str(exc)
        finally:
            try:
                payload_path.unlink(missing_ok=True)
            except Exception:
                pass

    def _execute_official_sdk_command(
        self,
        *,
        operation: str,
        payload: dict[str, Any],
        timeout_ms: int,
    ) -> tuple[bool, dict[str, Any], str]:
        sdk_dir = self._ensure_sdk_dir(auto_extract=True)
        if sdk_dir is None:
            return False, {}, self._bridge_status_message()
        if not self._bridge_script.is_file():
            return False, {}, "Local PowerShell bridge script is missing"

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
            payload_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        try:
            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(self._bridge_script),
                    "-Command",
                    str(operation),
                    "-PayloadPath",
                    str(payload_path),
                    "-SdkDir",
                    str(sdk_dir),
                ],
                capture_output=True,
                text=True,
                timeout=max(5, int(timeout_ms / 1000) + 10),
                check=False,
            )
            stdout = str(completed.stdout or "").strip()
            stderr = str(completed.stderr or "").strip()
            parsed: dict[str, Any] = {}
            if stdout:
                try:
                    loaded = json.loads(stdout)
                    if isinstance(loaded, dict):
                        parsed = loaded
                    else:
                        parsed = {"payload": loaded}
                except Exception:
                    parsed = {"message": stdout}
            if completed.returncode != 0:
                return False, parsed, str(parsed.get("error") or parsed.get("message") or stderr or stdout or f"Bridge exit code {completed.returncode}")
            if not stdout:
                return True, {}, ""
            return True, parsed, stderr
        except Exception as exc:
            return False, {}, str(exc)
        finally:
            try:
                payload_path.unlink(missing_ok=True)
            except Exception:
                pass

    def _execute_bridge_operation(
        self,
        *,
        operation: str,
        payload: dict[str, Any],
        timeout_ms: int,
    ) -> tuple[bool, dict[str, Any], str]:
        command_key_map = {
            "pair": "pair_command",
            "ping": "ping_command",
            "sale": "sale_command",
            "void": "void_command",
            "refund": "refund_command",
            "flow": "flow_command",
        }
        command_key = command_key_map.get(operation)
        if command_key and self._bridge_command(command_key) is not None:
            return self._execute_configured_command(
                command_key=command_key,
                payload=payload,
                timeout_ms=timeout_ms,
            )
        return self._execute_official_sdk_command(
            operation=operation,
            payload=payload,
            timeout_ms=timeout_ms,
        )

    @staticmethod
    def _normalize_sale_status(payload: dict[str, Any]) -> PaymentStatus:
        status_text = str(
            payload.get("status")
            or payload.get("raw_payment_status")
            or payload.get("processor_status")
            or ""
        ).strip().upper()
        if any(token in status_text for token in ("AUTHORIZED", "APPROVED", "CAPTURED", "COMPLETE", "SUCCESS")):
            return PaymentStatus.APPROVED
        if "CANCEL" in status_text:
            return PaymentStatus.CANCELLED
        if "TIMEOUT" in status_text:
            return PaymentStatus.TIMEOUT
        if any(token in status_text for token in ("DECLIN", "DENIED", "FAIL")):
            return PaymentStatus.DECLINED
        return PaymentStatus.ERROR

    def _not_ready_result(self, *, status: PaymentStatus, order_id: str = "", amount_cents: int = 0) -> PaymentResult:
        message = self._bridge_status_message()
        self._flow_state = FlowStateResult(
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            status=status,
            is_busy=False,
            message=message,
            current_order_id=str(order_id or ""),
            terminal_name=self.settings.terminal_name,
            terminal_ip=self.settings.terminal_ip,
            updated_at=now_iso(),
        )
        return PaymentResult(
            status=status,
            order_id=str(order_id or ""),
            amount_cents=int(amount_cents),
            currency=self.settings.currency,
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            error_code="GODADDY_BRIDGE_UNAVAILABLE",
            error_message=message,
            message=message,
            raw_response={"message": message},
        )

    def pair_terminal(self) -> PairResult:
        if platform.system().lower() != "windows":
            return PairResult(
                success=False,
                provider=PaymentProviderType.GODADDY_POSBRIDGE,
                message=self._bridge_status_message(),
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                error_code="WINDOWS_ONLY",
                error_message=self._bridge_status_message(),
            )
        ok, payload, err = self._execute_bridge_operation(
            operation="pair",
            payload=self.settings.to_dict(),
            timeout_ms=self.settings.request_timeout_ms,
        )
        if not ok:
            return PairResult(
                success=False,
                provider=PaymentProviderType.GODADDY_POSBRIDGE,
                message=err or self._bridge_status_message(),
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                error_code="PAIR_FAILED",
                error_message=err or self._bridge_status_message(),
                metadata=payload,
            )
        return PairResult(
            success=bool(payload.get("success", True)),
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            message=str(payload.get("message", "Pair command completed")),
            terminal_name=str(payload.get("terminal_name", self.settings.terminal_name)),
            terminal_ip=str(payload.get("terminal_ip", self.settings.terminal_ip)),
            metadata=payload,
        )

    def ping(self) -> PingResult:
        if platform.system().lower() != "windows":
            return PingResult(
                success=False,
                provider=PaymentProviderType.GODADDY_POSBRIDGE,
                message=self._bridge_status_message(),
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                error_code="WINDOWS_ONLY",
                error_message=self._bridge_status_message(),
            )
        ok, payload, err = self._execute_bridge_operation(
            operation="ping",
            payload=self.settings.to_dict(),
            timeout_ms=self.settings.request_timeout_ms,
        )
        if not ok:
            return PingResult(
                success=False,
                provider=PaymentProviderType.GODADDY_POSBRIDGE,
                message=err or self._bridge_status_message(),
                terminal_name=self.settings.terminal_name,
                terminal_ip=self.settings.terminal_ip,
                error_code="PING_FAILED",
                error_message=err or self._bridge_status_message(),
                metadata=payload,
            )
        return PingResult(
            success=bool(payload.get("success", True)),
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            message=str(payload.get("message", "Ping command completed")),
            terminal_name=str(payload.get("terminal_name", self.settings.terminal_name)),
            terminal_ip=str(payload.get("terminal_ip", self.settings.terminal_ip)),
            latency_ms=int(payload.get("latency_ms", 0) or 0) if payload.get("latency_ms") is not None else None,
            metadata=payload,
        )

    def sale(self, order_id: str, amount_cents: int, currency: str, description: str) -> PaymentResult:
        if platform.system().lower() != "windows":
            return self._not_ready_result(status=PaymentStatus.ERROR, order_id=order_id, amount_cents=amount_cents)
        ok, payload, err = self._execute_bridge_operation(
            operation="sale",
            payload={
                "order_id": order_id,
                "amount_cents": int(amount_cents),
                "currency": str(currency or self.settings.currency),
                "description": str(description or ""),
                "terminal_ip": self.settings.terminal_ip,
                "terminal_port": int(self.settings.terminal_port),
                "terminal_name": self.settings.terminal_name,
                "pairing_code_or_key": self.settings.pairing_code_or_key,
                "request_timeout_ms": int(self.settings.request_timeout_ms),
                "auto_print_receipt": bool(self.settings.auto_print_receipt),
            },
            timeout_ms=self.settings.request_timeout_ms,
        )
        if not ok:
            return PaymentResult(
                status=PaymentStatus.ERROR,
                order_id=order_id,
                amount_cents=amount_cents,
                currency=currency,
                provider=PaymentProviderType.GODADDY_POSBRIDGE,
                error_code="SALE_FAILED",
                error_message=err or self._bridge_status_message(),
                message=err or self._bridge_status_message(),
                raw_response=payload,
            )
        status = self._normalize_sale_status(payload)
        return PaymentResult(
            status=status,
            order_id=order_id,
            amount_cents=amount_cents,
            currency=currency,
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            transaction_id=str(payload.get("provider_transaction_id", "") or payload.get("processor_transaction_id", "")).strip(),
            provider_reference=str(payload.get("provider_reference", "") or payload.get("transaction_number", "")).strip(),
            approval_code=str(payload.get("approval_code", "")).strip(),
            card_brand=str(payload.get("card_brand", "")).strip(),
            last4_masked=str(payload.get("last4_masked", "")).strip() or None,
            error_code=str(payload.get("error_code", "")).strip(),
            error_message=str(payload.get("error_message", "") or payload.get("processor_status_message", "")).strip(),
            message=str(payload.get("message", "") or payload.get("raw_payment_status", "")).strip(),
            raw_response=payload,
        )

    def void(self, transaction_id: str, amount_cents: int | None = None) -> PaymentResult:
        ok, payload, err = self._execute_bridge_operation(
            operation="void",
            payload={
                "transaction_id": str(transaction_id or ""),
                "amount_cents": int(amount_cents or 0),
                "terminal_ip": self.settings.terminal_ip,
                "terminal_port": int(self.settings.terminal_port),
                "terminal_name": self.settings.terminal_name,
                "pairing_code_or_key": self.settings.pairing_code_or_key,
                "request_timeout_ms": int(self.settings.request_timeout_ms),
            },
            timeout_ms=self.settings.request_timeout_ms,
        )
        if not ok:
            return self._not_ready_result(status=PaymentStatus.ERROR, amount_cents=int(amount_cents or 0))
        status = self._normalize_sale_status(payload)
        if status == PaymentStatus.APPROVED:
            status = PaymentStatus.VOIDED
        return PaymentResult(
            status=status,
            order_id="",
            amount_cents=int(amount_cents or 0),
            currency=self.settings.currency,
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            transaction_id=str(payload.get("provider_transaction_id", "") or transaction_id).strip(),
            provider_reference=str(payload.get("provider_reference", "")).strip(),
            approval_code=str(payload.get("approval_code", "")).strip(),
            card_brand=str(payload.get("card_brand", "")).strip(),
            last4_masked=str(payload.get("last4_masked", "")).strip() or None,
            error_message=str(err or payload.get("processor_status_message", "")).strip(),
            message=str(payload.get("message", "") or "Void completed").strip(),
            raw_response=payload,
        )

    def refund(self, transaction_id: str, amount_cents: int) -> PaymentResult:
        ok, payload, err = self._execute_bridge_operation(
            operation="refund",
            payload={
                "transaction_id": str(transaction_id or ""),
                "amount_cents": int(amount_cents),
                "terminal_ip": self.settings.terminal_ip,
                "terminal_port": int(self.settings.terminal_port),
                "terminal_name": self.settings.terminal_name,
                "pairing_code_or_key": self.settings.pairing_code_or_key,
                "request_timeout_ms": int(self.settings.request_timeout_ms),
            },
            timeout_ms=self.settings.request_timeout_ms,
        )
        if not ok:
            return self._not_ready_result(status=PaymentStatus.ERROR, amount_cents=int(amount_cents))
        status = self._normalize_sale_status(payload)
        if status == PaymentStatus.APPROVED:
            status = PaymentStatus.REFUNDED
        return PaymentResult(
            status=status,
            order_id="",
            amount_cents=int(amount_cents),
            currency=self.settings.currency,
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            transaction_id=str(payload.get("provider_transaction_id", "") or transaction_id).strip(),
            provider_reference=str(payload.get("provider_reference", "")).strip(),
            approval_code=str(payload.get("approval_code", "")).strip(),
            card_brand=str(payload.get("card_brand", "")).strip(),
            last4_masked=str(payload.get("last4_masked", "")).strip() or None,
            error_message=str(err or payload.get("processor_status_message", "")).strip(),
            message=str(payload.get("message", "") or "Refund completed").strip(),
            raw_response=payload,
        )

    def get_flow_state(self) -> FlowStateResult:
        ok, payload, err = self._execute_bridge_operation(
            operation="flow",
            payload=self.settings.to_dict(),
            timeout_ms=self.settings.request_timeout_ms,
        )
        if ok:
            state_text = str(payload.get("current_state", "") or payload.get("message", "")).strip()
            self._flow_state = FlowStateResult(
                provider=PaymentProviderType.GODADDY_POSBRIDGE,
                status=PaymentStatus.PENDING if state_text and state_text.upper() != "IDLE" else PaymentStatus.IDLE,
                is_busy=bool(state_text and state_text.upper() != "IDLE"),
                message=state_text or "IDLE",
                current_order_id=str(self._flow_state.current_order_id or ""),
                terminal_name=str(self.settings.terminal_name or ""),
                terminal_ip=str(self.settings.terminal_ip or ""),
                updated_at=now_iso(),
            )
        return FlowStateResult(
            provider=self._flow_state.provider,
            status=self._flow_state.status,
            is_busy=bool(self._flow_state.is_busy),
            message=str(self._flow_state.message or err or self._bridge_status_message()),
            current_order_id=str(self._flow_state.current_order_id or ""),
            terminal_name=str(self.settings.terminal_name or ""),
            terminal_ip=str(self.settings.terminal_ip or ""),
            cancellable=bool(self._flow_state.cancellable),
            updated_at=str(self._flow_state.updated_at or now_iso()),
            metadata=dict(self._flow_state.metadata or {}),
        )

    def close(self) -> None:
        self._flow_state = FlowStateResult(
            provider=PaymentProviderType.GODADDY_POSBRIDGE,
            status=PaymentStatus.IDLE,
            is_busy=False,
            message="Provider closed",
            terminal_name=self.settings.terminal_name,
            terminal_ip=self.settings.terminal_ip,
            updated_at=now_iso(),
        )
