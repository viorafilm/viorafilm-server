from __future__ import annotations

import unittest
from unittest.mock import patch

import app.main as kiosk_main


class _HeartbeatStub:
    def __init__(self, ds620_remaining, rx1hs_remaining, default_model="DS620") -> None:
        self._ds620_remaining = ds620_remaining
        self._rx1hs_remaining = rx1hs_remaining
        self._default_model = default_model
        self.calls: list[tuple[str, bool]] = []

    def get_share_settings(self):
        return {"api_base_url": "https://api.viorafilm.com/api"}

    def get_printing_settings(self):
        return {"default_model": self._default_model}

    def _current_kiosk_app_version(self):
        return "1.0.0"

    def _printer_health_snapshot(self, _models, _printing_settings=None):
        return True, "ok"

    def _get_film_remaining(self, model, allow_fallback=True):
        normalized = kiosk_main.KioskMainWindow._normalize_film_model(model)
        self.calls.append((normalized, bool(allow_fallback)))
        if normalized == "DS620":
            return self._ds620_remaining if allow_fallback else None
        if normalized == "RX1HS":
            return self._rx1hs_remaining if allow_fallback else None
        return None

    def _env_optional_nonnegative_int(self, _name):
        return None

    def _offline_telemetry_snapshot(self):
        return {}

    def _build_runtime_log_snapshot(self):
        return {}

    def _build_runtime_log_sync_payload(self):
        return {}

    def _normalize_film_model(self, model):
        return kiosk_main.KioskMainWindow._normalize_film_model(model)


class HeartbeatFilmRemainingTests(unittest.TestCase):
    def test_heartbeat_uses_cached_primary_model_remaining(self) -> None:
        stub = _HeartbeatStub(ds620_remaining=382, rx1hs_remaining=400, default_model="DS620")

        with patch("app.main.check_internet", return_value=(True, "ok")):
            payload = kiosk_main.KioskMainWindow._build_heartbeat_payload(stub)

        self.assertEqual(payload["film_remaining"], 382)
        self.assertEqual(payload["printer_ds620"]["film_remaining"], 382)
        self.assertEqual(payload["printer_rx1hs"]["film_remaining"], 400)
        self.assertIn(("DS620", True), stub.calls)
        self.assertIn(("RX1HS", True), stub.calls)
        self.assertNotIn(("DS620", False), stub.calls)
        self.assertNotIn(("RX1HS", False), stub.calls)

    def test_heartbeat_does_not_swap_to_other_printer_when_primary_missing(self) -> None:
        stub = _HeartbeatStub(ds620_remaining=None, rx1hs_remaining=400, default_model="DS620")

        with patch("app.main.check_internet", return_value=(True, "ok")):
            payload = kiosk_main.KioskMainWindow._build_heartbeat_payload(stub)

        self.assertNotIn("film_remaining", payload)
        self.assertNotIn("printer_ds620", payload)
        self.assertEqual(payload["printer_rx1hs"]["film_remaining"], 400)


if __name__ == "__main__":
    unittest.main()
