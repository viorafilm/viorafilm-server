from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

Rect = tuple[int, int, int, int]

EXPECTED_SLOT_COUNT_BY_LAYOUT: dict[str, int] = {
    "2641": 4,
    "6241": 4,
    "4641": 4,
    "4661": 6,
    "4681": 8,
}

# TODO: Move fallback slot definitions to a JSON generated from UI R-mode captures.
_FALLBACK_SLOT_NORMALIZED: dict[str, list[tuple[float, float, float, float]]] = {
    "2641": [
        (0.07, 0.09, 0.39, 0.38),
        (0.54, 0.09, 0.39, 0.38),
        (0.07, 0.53, 0.39, 0.38),
        (0.54, 0.53, 0.39, 0.38),
    ],
    "6241": [
        (0.05, 0.12, 0.43, 0.34),
        (0.52, 0.12, 0.43, 0.34),
        (0.05, 0.54, 0.43, 0.34),
        (0.52, 0.54, 0.43, 0.34),
    ],
    "4641": [
        (0.07, 0.09, 0.39, 0.38),
        (0.54, 0.09, 0.39, 0.38),
        (0.07, 0.53, 0.39, 0.38),
        (0.54, 0.53, 0.39, 0.38),
    ],
    "4661": [
        (0.07, 0.06, 0.39, 0.25),
        (0.54, 0.06, 0.39, 0.25),
        (0.07, 0.37, 0.39, 0.25),
        (0.54, 0.37, 0.39, 0.25),
        (0.07, 0.68, 0.39, 0.25),
        (0.54, 0.68, 0.39, 0.25),
    ],
    "4681": [
        (0.07, 0.05, 0.39, 0.18),
        (0.54, 0.05, 0.39, 0.18),
        (0.07, 0.27, 0.39, 0.18),
        (0.54, 0.27, 0.39, 0.18),
        (0.07, 0.49, 0.39, 0.18),
        (0.54, 0.49, 0.39, 0.18),
        (0.07, 0.71, 0.39, 0.18),
        (0.54, 0.71, 0.39, 0.18),
    ],
}


def _sort_rects(rects: list[Rect]) -> list[Rect]:
    return sorted(rects, key=lambda r: (r[1], r[0]))


def _detect_gray_slot_components(
    frame_rgba: Image.Image,
    target_rgb: tuple[int, int, int] = (91, 91, 91),
    tolerance: int = 12,
) -> list[tuple[Rect, int]]:
    width, height = frame_rgba.size
    pixels = frame_rgba.load()
    mask = [bytearray(width) for _ in range(height)]

    tr, tg, tb = target_rgb
    for y in range(height):
        row = mask[y]
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if (
                a > 0
                and abs(r - tr) <= tolerance
                and abs(g - tg) <= tolerance
                and abs(b - tb) <= tolerance
            ):
                row[x] = 1

    min_area = max(300, (width * height) // 20000)
    components: list[tuple[Rect, int]] = []

    for y in range(height):
        row = mask[y]
        for x in range(width):
            if not row[x]:
                continue

            row[x] = 0
            queue: deque[tuple[int, int]] = deque([(x, y)])
            min_x = max_x = x
            min_y = max_y = y
            area = 0

            while queue:
                cx, cy = queue.pop()
                area += 1
                if cx < min_x:
                    min_x = cx
                if cx > max_x:
                    max_x = cx
                if cy < min_y:
                    min_y = cy
                if cy > max_y:
                    max_y = cy

                if cx > 0 and mask[cy][cx - 1]:
                    mask[cy][cx - 1] = 0
                    queue.append((cx - 1, cy))
                if cx + 1 < width and mask[cy][cx + 1]:
                    mask[cy][cx + 1] = 0
                    queue.append((cx + 1, cy))
                if cy > 0 and mask[cy - 1][cx]:
                    mask[cy - 1][cx] = 0
                    queue.append((cx, cy - 1))
                if cy + 1 < height and mask[cy + 1][cx]:
                    mask[cy + 1][cx] = 0
                    queue.append((cx, cy + 1))

            if area >= min_area:
                rect = (min_x, min_y, (max_x - min_x + 1), (max_y - min_y + 1))
                components.append((rect, area))

    return components


def _fallback_slots(layout_id: str, frame_size: tuple[int, int]) -> list[Rect]:
    normalized = _FALLBACK_SLOT_NORMALIZED.get(layout_id, [])
    if not normalized:
        return []

    width, height = frame_size
    slots: list[Rect] = []
    for nx, ny, nw, nh in normalized:
        x = int(width * nx)
        y = int(height * ny)
        w = max(1, int(width * nw))
        h = max(1, int(height * nh))
        slots.append((x, y, w, h))
    return slots


def resolve_slots(frame_png_path: Path, layout_id: str) -> tuple[list[Rect], str]:
    frame_path = Path(frame_png_path)
    if not frame_path.is_file():
        raise FileNotFoundError(f"Frame PNG not found: {frame_path}")

    with Image.open(frame_path) as frame_source:
        frame_rgba = frame_source.convert("RGBA")

    components = _detect_gray_slot_components(frame_rgba)
    expected_count = EXPECTED_SLOT_COUNT_BY_LAYOUT.get(layout_id)

    if expected_count is None:
        detected = _sort_rects([rect for rect, _ in components])
        if detected:
            return detected, "detected"
        fallback = _fallback_slots(layout_id, frame_rgba.size)
        if fallback:
            return _sort_rects(fallback), "fallback"
        raise ValueError(f"No slot rule for layout_id={layout_id}")

    if len(components) >= expected_count:
        selected = sorted(components, key=lambda item: item[1], reverse=True)[:expected_count]
        rects = _sort_rects([rect for rect, _area in selected])
        return rects, "detected"

    fallback = _fallback_slots(layout_id, frame_rgba.size)
    if not fallback:
        raise ValueError(
            f"Detected slots={len(components)} < expected={expected_count}, "
            f"and no fallback slots for layout_id={layout_id}"
        )
    return _sort_rects(fallback), "fallback"


def _fit_cover(photo: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    target_w, target_h = target_size
    if target_w <= 0 or target_h <= 0:
        raise ValueError(f"Invalid target size: {target_size}")

    src_w, src_h = photo.size
    if src_w <= 0 or src_h <= 0:
        raise ValueError("Invalid source image size")

    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        crop_w = int(src_h * target_ratio)
        crop_h = src_h
        crop_x = (src_w - crop_w) // 2
        crop_y = 0
    else:
        crop_w = src_w
        crop_h = int(src_w / target_ratio)
        crop_x = 0
        crop_y = (src_h - crop_h) // 2

    cropped = photo.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def compose_print(frame_png_path: Path, photos: list[Path], layout_id: str) -> Image.Image:
    frame_path = Path(frame_png_path)
    if not frame_path.is_file():
        raise FileNotFoundError(f"Frame PNG not found: {frame_path}")
    if not photos:
        raise ValueError("photos must not be empty")

    slots, _slot_source = resolve_slots(frame_path, layout_id)
    if not slots:
        raise ValueError(f"No slots available for layout_id={layout_id}")

    loaded_photos: list[Image.Image] = []
    for photo_path in photos:
        p = Path(photo_path)
        if not p.is_file():
            raise FileNotFoundError(f"Photo not found: {p}")
        with Image.open(p) as source:
            loaded_photos.append(source.convert("RGB"))

    with Image.open(frame_path) as frame_source:
        frame_rgba = frame_source.convert("RGBA")

    base = Image.new("RGB", frame_rgba.size, (255, 255, 255))
    for idx, (x, y, w, h) in enumerate(slots):
        photo = loaded_photos[idx % len(loaded_photos)]
        fitted = _fit_cover(photo, (w, h))
        base.paste(fitted, (x, y))

    composed = base.convert("RGBA")
    composed.alpha_composite(frame_rgba)
    return composed.convert("RGB")
