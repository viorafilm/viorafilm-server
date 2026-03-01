from __future__ import annotations

import io
import json
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from PIL import Image


@dataclass
class Session:
    session_dir: Path
    shots_dir: Path
    print_dir: Path
    qr_dir: Path
    meta_path: Path
    created_at: str
    session_id: Optional[str] = None
    layout_id: Optional[str] = None
    design_path: Optional[str] = None
    print_path: Optional[str] = None
    share_url: Optional[str] = None
    qr_path: Optional[Path] = None
    shot_paths: list[Path] = field(default_factory=list)

    def set_context(
        self,
        layout_id: Optional[str] = None,
        design_path: Optional[str] = None,
    ) -> None:
        self.layout_id = layout_id
        self.design_path = design_path
        self._write_meta()

    def set_share_url(self, url: Optional[str]) -> None:
        self.share_url = url
        self._write_meta()

    def clear_share(self) -> None:
        self.share_url = None
        self.qr_path = None
        self._write_meta()

    def save_qr(self, image_source, filename: str = "qr.png") -> Path:
        self.qr_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.qr_dir / filename

        if isinstance(image_source, (str, Path)):
            source_path = Path(image_source)
            output_path.write_bytes(source_path.read_bytes())
        elif isinstance(image_source, bytes):
            output_path.write_bytes(image_source)
        elif isinstance(image_source, Image.Image):
            image_source.save(output_path, format="PNG")
        else:
            raise TypeError("image_source must be bytes, PIL.Image.Image, str, or Path")

        self.qr_path = output_path
        self._write_meta()
        return output_path

    def save_print(self, image_source, filename: str = "print.jpg") -> Path:
        output_path = self.print_dir / filename
        self.print_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(image_source, (str, Path)):
            with Image.open(image_source) as source:
                source.convert("RGB").save(output_path, format="JPEG", quality=95)
        elif isinstance(image_source, bytes):
            with Image.open(io.BytesIO(image_source)) as source:
                source.convert("RGB").save(output_path, format="JPEG", quality=95)
        elif isinstance(image_source, Image.Image):
            image_source.convert("RGB").save(output_path, format="JPEG", quality=95)
        else:
            raise TypeError(
                "image_source must be bytes, PIL.Image.Image, str, or Path"
            )

        self.print_path = str(output_path)
        self._write_meta()
        return output_path

    def save_shot(self, image_source, index: int) -> Path:
        if index < 1:
            raise ValueError("index must be >= 1")

        output_path = self.shots_dir / f"shot_{index:02d}.jpg"
        self.shots_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(image_source, (str, Path)):
            with Image.open(image_source) as source:
                source.convert("RGB").save(output_path, format="JPEG", quality=95)
        elif isinstance(image_source, bytes):
            with Image.open(io.BytesIO(image_source)) as source:
                source.convert("RGB").save(output_path, format="JPEG", quality=95)
        elif isinstance(image_source, Image.Image):
            image_source.convert("RGB").save(output_path, format="JPEG", quality=95)
        else:
            raise TypeError(
                "image_source must be bytes, PIL.Image.Image, str, or Path"
            )

        if len(self.shot_paths) >= index:
            self.shot_paths[index - 1] = output_path
        else:
            self.shot_paths.append(output_path)
        self._write_meta()
        return output_path

    def delete_last_shot(self) -> Optional[Path]:
        if not self.shot_paths:
            return None

        last = self.shot_paths.pop()
        try:
            last.unlink(missing_ok=True)
        except OSError:
            pass
        self._write_meta()
        return last

    def _write_meta(self) -> None:
        payload = {
            "created_at": self.created_at,
            "session_id": self.session_id,
            "layout_id": self.layout_id,
            "design_path": self.design_path,
            "print_path": self.print_path,
            "share_url": self.share_url,
            "qr_path": str(self.qr_path) if self.qr_path else None,
        }
        self.meta_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def create_session(base_dir="sessions") -> Session:
    cleanup_old_sessions(base_dir, retention_hours=24.0)

    base_path = Path(base_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid4().hex[:4]
    session_dir = base_path / f"{timestamp}_{suffix}"
    shots_dir = session_dir / "shots"
    print_dir = session_dir / "print"
    qr_dir = session_dir / "qr"
    meta_path = session_dir / "meta.json"

    shots_dir.mkdir(parents=True, exist_ok=True)
    print_dir.mkdir(parents=True, exist_ok=True)
    qr_dir.mkdir(parents=True, exist_ok=True)
    session = Session(
        session_dir=session_dir,
        shots_dir=shots_dir,
        print_dir=print_dir,
        qr_dir=qr_dir,
        meta_path=meta_path,
        created_at=datetime.now().isoformat(timespec="seconds"),
        session_id=session_dir.name,
    )
    session._write_meta()
    return session


def cleanup_old_sessions(
    base_dir: str | Path = "sessions",
    *,
    retention_hours: float = 24.0,
    keep_session_ids: Optional[set[str]] = None,
) -> dict[str, int]:
    base_path = Path(base_dir)
    if not base_path.exists():
        return {"removed": 0, "failed": 0}
    if not base_path.is_dir():
        return {"removed": 0, "failed": 1}

    keep_ids = {str(x).strip() for x in (keep_session_ids or set()) if str(x).strip()}
    retention_sec = max(3600.0, float(retention_hours) * 3600.0)
    cutoff_ts = time.time() - retention_sec

    removed = 0
    failed = 0
    for child in base_path.iterdir():
        if not child.is_dir():
            continue
        if child.name in keep_ids:
            continue
        try:
            mtime = float(child.stat().st_mtime)
        except Exception:
            failed += 1
            continue
        if mtime > cutoff_ts:
            continue
        try:
            shutil.rmtree(child, ignore_errors=False)
            removed += 1
        except Exception:
            failed += 1
    return {"removed": removed, "failed": failed}
