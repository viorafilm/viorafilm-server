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


if __name__ == "__main__":
    unittest.main()
