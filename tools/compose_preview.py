#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from kiosk.print.compose import EXPECTED_SLOT_COUNT_BY_LAYOUT, compose_print, resolve_slots


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose a preview image with dummy photos.")
    parser.add_argument("--layout", required=True, help="Layout id (e.g. 2641, 6241)")
    parser.add_argument("--frame", required=True, type=int, help="Frame index (1-based)")
    parser.add_argument("--debug", action="store_true", help="Save slot debug image")
    return parser.parse_args()


def _frame_sort_key(path: Path):
    stem = path.stem
    if stem.isdigit():
        return (0, int(stem), len(stem), stem)
    return (1, 0, 0, stem.lower())


def _resolve_frame_file(layout_id: str, frame_index: int) -> Path:
    frame_dir = ROOT_DIR / "assets" / "ui" / "10_select_Design" / "Frame" / "Frame2" / layout_id
    if not frame_dir.is_dir():
        raise FileNotFoundError(f"Frame directory not found: {frame_dir}")

    png_files = sorted(
        [p for p in frame_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"],
        key=_frame_sort_key,
    )
    if not png_files:
        raise FileNotFoundError(f"No PNG frame files in: {frame_dir}")

    by_number = [p for p in png_files if p.stem.isdigit() and int(p.stem) == frame_index]
    if by_number:
        by_number.sort(key=lambda p: (len(p.stem), p.name.lower()))
        return by_number[0]

    if 1 <= frame_index <= len(png_files):
        return png_files[frame_index - 1]

    names = ", ".join(p.name for p in png_files)
    raise ValueError(f"Frame index {frame_index} not found in {frame_dir}. Available: {names}")


def _load_font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "malgun.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _create_dummy_photo(path: Path, number: int) -> None:
    palette = [
        (235, 95, 95),
        (95, 145, 235),
        (95, 185, 115),
        (210, 145, 70),
        (165, 115, 215),
        (90, 180, 185),
        (210, 95, 150),
        (120, 120, 120),
    ]
    color = palette[(number - 1) % len(palette)]
    image = Image.new("RGB", (1600, 1200), color)
    draw = ImageDraw.Draw(image)

    font = _load_font(420)
    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=8)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (image.width - text_w) // 2
    y = (image.height - text_h) // 2

    draw.text(
        (x, y),
        text,
        fill=(255, 255, 255),
        font=font,
        stroke_width=8,
        stroke_fill=(20, 20, 20),
    )
    image.save(path, format="JPEG", quality=95)


def main() -> int:
    args = _parse_args()
    frame_path = _resolve_frame_file(args.layout, args.frame)
    slots, slot_source = resolve_slots(frame_path, args.layout)
    slot_count = len(slots)
    if slot_count <= 0:
        slot_count = EXPECTED_SLOT_COUNT_BY_LAYOUT.get(args.layout, 4)

    out_dir = ROOT_DIR / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"compose_{args.layout}_{args.frame}.jpg"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        photos: list[Path] = []
        for i in range(slot_count):
            photo_path = temp_root / f"dummy_{i + 1}.jpg"
            _create_dummy_photo(photo_path, i + 1)
            photos.append(photo_path)

        composed = compose_print(frame_path, photos, args.layout)
        composed.save(output_path, format="JPEG", quality=95)

        if args.debug:
            debug_image = composed.copy()
            draw = ImageDraw.Draw(debug_image)
            label_font = _load_font(38)
            for idx, (x, y, w, h) in enumerate(slots, start=1):
                draw.rectangle((x, y, x + w - 1, y + h - 1), outline=(255, 0, 0), width=6)
                draw.text((x + 8, y + 8), str(idx), fill=(255, 0, 0), font=label_font)
            debug_path = out_dir / f"compose_{args.layout}_{args.frame}_debug.jpg"
            debug_image.save(debug_path, format="JPEG", quality=95)
            print(f"Debug image saved: {debug_path}")

    print(f"Frame: {frame_path.name}")
    print(f"Slots: {len(slots)} ({slot_source})")
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"compose_preview failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

