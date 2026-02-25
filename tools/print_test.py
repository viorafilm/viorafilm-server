#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    raise SystemExit(1)

from kiosk.services.printer.win_spooler import print_image


def _create_test_image(path: Path, printer_name: str, copies: int) -> None:
    image = Image.new("RGB", (1800, 1200), (248, 248, 248))
    draw = ImageDraw.Draw(image)
    draw.rectangle((70, 70, 1730, 1130), outline=(30, 30, 30), width=8)

    lines = [
        "PhotoHaru Printer Test",
        f"Printer: {printer_name}",
        f"Copies: {copies}",
        f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    y = 240
    for line in lines:
        draw.text((140, y), line, fill=(0, 0, 0))
        y += 120

    image.save(path, format="PNG")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and print a test image.")
    parser.add_argument("--printer", required=True, help="Target printer queue name")
    parser.add_argument(
        "--copies",
        type=int,
        default=2,
        help="Number of copies to print (default: 2)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.copies < 1:
        print("Error: --copies must be at least 1.", file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        image_path = Path(temp_file.name)

    try:
        _create_test_image(image_path, args.printer, args.copies)
        print_image(args.printer, image_path, copies=args.copies)
    except Exception as exc:
        print(f"Print failed: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            image_path.unlink(missing_ok=True)
        except OSError:
            pass

    print(f'Print job submitted to "{args.printer}" with {args.copies} copies.')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

