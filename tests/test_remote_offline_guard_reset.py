from __future__ import annotations

import unittest
from unittest.mock import patch

import app.main as kiosk_main


class _OfflineGuardResetStub:
    def __init__(self) -> None:
        self._last_remote_action_id = ""
        self._pending_remote_action_payload = {
            "id": "abc123",
            "kind": "offline_guard_reset",
            "meta": {"actor": "admin"},
        }
        self._pending_remote_action_ack_id = ""
        self.record_online_calls = 0
        self.enforce_calls: list[str] = []
        self.notice_calls: list[tuple[str, int]] = []
        self.heartbeat_calls = 0

    def _current_screen_name_for_heartbeat(self) -> str:
        return "offline_locked"

    def _record_online_heartbeat(self) -> None:
        self.record_online_calls += 1

    def _enforce_offline_runtime_guard(self, trigger: str = "") -> None:
        self.enforce_calls.append(str(trigger))

    def _show_runtime_notice(self, message: str, duration_ms: int = 0) -> None:
        self.notice_calls.append((str(message), int(duration_ms)))

    def _heartbeat_tick(self) -> None:
        self.heartbeat_calls += 1

    def _apply_remote_offline_guard_reset_action(self, payload: dict, current_screen: str = "") -> None:
        kiosk_main.KioskMainWindow._apply_remote_offline_guard_reset_action(self, payload, current_screen=current_screen)


class RemoteOfflineGuardResetTests(unittest.TestCase):
    def test_try_apply_pending_remote_action_resets_offline_guard(self) -> None:
        stub = _OfflineGuardResetStub()

        with patch("app.main.QTimer.singleShot", side_effect=lambda _delay, callback: callback()):
            applied = kiosk_main.KioskMainWindow._try_apply_pending_remote_action(
                stub,
                current_screen="offline_locked",
            )

        self.assertTrue(applied)
        self.assertEqual(stub.record_online_calls, 1)
        self.assertEqual(stub.enforce_calls, ["remote_action:offline_guard_reset"])
        self.assertEqual(stub._last_remote_action_id, "abc123")
        self.assertEqual(stub._pending_remote_action_payload, {})
        self.assertEqual(stub._pending_remote_action_ack_id, "abc123")
        self.assertEqual(stub.heartbeat_calls, 1)
        self.assertTrue(stub.notice_calls)
        self.assertIn("Authorization refreshed", stub.notice_calls[0][0])


if __name__ == "__main__":
    unittest.main()
