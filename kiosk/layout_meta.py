from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

Rect = tuple[int, int, int, int]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _meta_dir() -> Path:
    return _repo_root() / "assets" / "layout_meta"


def _merge_meta(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key == "inherits":
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_meta(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _load_layout_meta(layout_id: str, stack: Optional[set[str]] = None) -> Optional[dict[str, Any]]:
    layout_key = str(layout_id or "").strip()
    if not layout_key:
        return None

    meta_path = _meta_dir() / f"{layout_key}.json"
    if not meta_path.is_file():
        return None

    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None

    seen = set(stack or set())
    if layout_key in seen:
        return None
    seen.add(layout_key)

    parent_key = str(raw.get("inherits", "") or "").strip()
    if parent_key:
        parent_meta = _load_layout_meta(parent_key, seen)
        if isinstance(parent_meta, dict):
            return _merge_meta(parent_meta, raw)

    return raw


def get_layout_meta(layout_id: str) -> Optional[dict[str, Any]]:
    meta = _load_layout_meta(layout_id)
    if not isinstance(meta, dict):
        return None
    return meta


def _scale_rect(rect: tuple[int, int, int, int], base_size: tuple[int, int], canvas_size: tuple[int, int]) -> Rect:
    bx, by, bw, bh = rect
    base_w = max(1, int(base_size[0]))
    base_h = max(1, int(base_size[1]))
    canvas_w = max(1, int(canvas_size[0]))
    canvas_h = max(1, int(canvas_size[1]))
    sx = float(canvas_w) / float(base_w)
    sy = float(canvas_h) / float(base_h)
    return (
        max(0, int(round(bx * sx))),
        max(0, int(round(by * sy))),
        max(1, int(round(bw * sx))),
        max(1, int(round(bh * sy))),
    )


def _section_dict(layout_id: str, scope: str) -> Optional[dict[str, Any]]:
    meta = get_layout_meta(layout_id)
    if not isinstance(meta, dict):
        return None
    section = meta.get(str(scope or "").strip())
    if not isinstance(section, dict):
        return None
    return section


def resolve_layout_meta_slots(
    layout_id: str,
    scope: str,
    canvas_size: tuple[int, int],
    variant: Optional[str] = None,
) -> list[Rect]:
    section = _section_dict(layout_id, scope)
    if section is None:
        return []
    base_size = section.get("base_size")
    raw_slots = section.get("slots")
    if variant is not None:
        slots_by_variant = section.get("slots_by_frame")
        if isinstance(slots_by_variant, dict):
            variant_key = str(variant or "").strip()
            if variant_key and isinstance(slots_by_variant.get(variant_key), list):
                raw_slots = slots_by_variant.get(variant_key)
            elif isinstance(slots_by_variant.get("default"), list):
                raw_slots = slots_by_variant.get("default")
    if not (
        isinstance(base_size, (list, tuple))
        and len(base_size) >= 2
        and isinstance(raw_slots, list)
        and raw_slots
    ):
        return []

    scaled: list[Rect] = []
    for item in raw_slots:
        if not isinstance(item, (list, tuple)) or len(item) < 4:
            continue
        scaled.append(
            _scale_rect(
                (int(item[0]), int(item[1]), int(item[2]), int(item[3])),
                (int(base_size[0]), int(base_size[1])),
                canvas_size,
            )
        )
    return scaled


def resolve_layout_meta_qr_rect(layout_id: str, scope: str, canvas_size: tuple[int, int]) -> Optional[Rect]:
    section = _section_dict(layout_id, scope)
    if section is None:
        return None
    base_size = section.get("base_size")
    raw_rect = section.get("qr_rect")
    if not (
        isinstance(base_size, (list, tuple))
        and len(base_size) >= 2
        and isinstance(raw_rect, (list, tuple))
        and len(raw_rect) >= 4
    ):
        return None
    return _scale_rect(
        (int(raw_rect[0]), int(raw_rect[1]), int(raw_rect[2]), int(raw_rect[3])),
        (int(base_size[0]), int(base_size[1])),
        canvas_size,
    )


def get_layout_meta_grouping(layout_id: str, scope: str = "print") -> Optional[str]:
    section = _section_dict(layout_id, scope)
    if section is None:
        return None
    grouping = str(section.get("grouping", "") or "").strip().lower()
    return grouping or None
