from __future__ import annotations

import os
import random
import time
from pathlib import Path

from kiosk.services.upload.uploader import Uploader


class DummyUploader(Uploader):
    def upload_print(self, session_id: str, print_path: Path) -> str:
        source = Path(print_path)
        if not source.is_file():
            raise FileNotFoundError(f"print file not found: {source}")

        if os.getenv("DUMMY_UPLOAD_FAIL", "").strip() == "1":
            raise RuntimeError("dummy upload failed")

        time.sleep(random.uniform(1.0, 2.0))
        base = os.getenv("UPLOAD_BASE_URL", "https://example.com/s").strip()
        if not base:
            base = "https://example.com/s"
        return f"{base.rstrip('/')}/{session_id}"
