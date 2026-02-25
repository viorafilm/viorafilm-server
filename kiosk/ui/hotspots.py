from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Hotspot:
    id: str
    rect: tuple[int, int, int, int]
    action: str


def load_hotspots(json_path: Path) -> Dict[str, List[Hotspot]]:
    path = Path(json_path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Invalid hotspot json format: {path}")

    result: Dict[str, List[Hotspot]] = {}
    for screen_name, entries in raw.items():
        if not isinstance(entries, list):
            raise ValueError(f"Hotspots for screen '{screen_name}' must be a list")

        screen_hotspots: List[Hotspot] = []
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError(f"Each hotspot for '{screen_name}' must be an object")

            rect = item.get("rect")
            if not (
                isinstance(rect, list)
                and len(rect) == 4
                and all(isinstance(v, (int, float)) for v in rect)
            ):
                raise ValueError(f"Hotspot rect for '{screen_name}' must be [x,y,w,h]")

            hotspot = Hotspot(
                id=str(item.get("id", "")),
                rect=(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])),
                action=str(item.get("action", "")),
            )
            screen_hotspots.append(hotspot)

        result[str(screen_name)] = screen_hotspots

    return result


def hit_test(hotspots: List[Hotspot], x: int, y: int) -> Optional[str]:
    ordered = sorted(
        hotspots,
        key=lambda h: max(0, h.rect[2]) * max(0, h.rect[3]),
    )
    for hotspot in ordered:
        left, top, width, height = hotspot.rect
        if width <= 0 or height <= 0:
            continue
        if left <= x < left + width and top <= y < top + height:
            print(
                f"[HIT_TEST] id={hotspot.id} action={hotspot.action} "
                f"rect={list(hotspot.rect)}"
            )
            return hotspot.action
    return None
