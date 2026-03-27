from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app.main as kiosk_main


class _RuntimeLogStub:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def get_runtime_log_file_path(self) -> str:
        return str(self._path)


class RuntimeLogSnapshotTests(unittest.TestCase):
    def test_build_runtime_log_snapshot_returns_tail_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "kiosk_20260327.log"
            path.write_text("line1\nline2\nline3\n", encoding="utf-8")
            stub = _RuntimeLogStub(path)
            with patch.dict("os.environ", {"KIOSK_HEARTBEAT_LOG_LINES": "2", "KIOSK_HEARTBEAT_LOG_CHARS": "2000"}):
                snapshot = kiosk_main.KioskMainWindow._build_runtime_log_snapshot(stub)

        self.assertEqual(snapshot.get("runtime_log_filename"), "kiosk_20260327.log")
        self.assertIn("line2", snapshot.get("runtime_log_excerpt", ""))
        self.assertIn("line3", snapshot.get("runtime_log_excerpt", ""))
        self.assertIn("line1", snapshot.get("runtime_log_excerpt", ""))
        self.assertTrue(snapshot.get("runtime_log_updated_at"))

    def test_build_runtime_log_sync_payload_and_mark_sent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "kiosk_20260327.log"
            state_path = Path(tmp_dir) / "runtime_log_sync_state.json"
            path.write_text("line1\nline2\n", encoding="utf-8")

            class _SyncStub(_RuntimeLogStub):
                def __init__(self, log_path: Path, sync_path: Path) -> None:
                    super().__init__(log_path)
                    self._runtime_log_sync_state_path = sync_path
                    self._pending_runtime_log_sync_state = {}

                def _load_runtime_log_sync_state(self):
                    return kiosk_main.KioskMainWindow._load_runtime_log_sync_state(self)

                def _save_runtime_log_sync_state(self, state):
                    return kiosk_main.KioskMainWindow._save_runtime_log_sync_state(self, state)

            stub = _SyncStub(path, state_path)
            payload = kiosk_main.KioskMainWindow._build_runtime_log_sync_payload(stub)
            self.assertEqual(payload.get("runtime_log_filename"), "kiosk_20260327.log")
            self.assertIn("line1", payload.get("runtime_log_chunk", ""))
            kiosk_main.KioskMainWindow._mark_runtime_log_sync_sent(stub)
            saved = kiosk_main.KioskMainWindow._load_runtime_log_sync_state(stub)
            self.assertEqual(saved.get("offset"), payload.get("runtime_log_chunk_end"))


if __name__ == "__main__":
    unittest.main()
