from __future__ import annotations

from pathlib import Path

import win32con
import win32print
import win32ui

try:
    from PIL import Image, ImageWin
except ImportError as exc:  # pragma: no cover - runtime dependency check
    Image = None
    ImageWin = None
    _PIL_IMPORT_ERROR = exc
else:
    _PIL_IMPORT_ERROR = None


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def _resolve_printer_name(printer_name: str) -> str:
    if not printer_name or not printer_name.strip():
        raise ValueError("Printer name is required.")

    printers = win32print.EnumPrinters(
        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    )
    normalized = {entry[2].casefold(): entry[2] for entry in printers if len(entry) > 2}
    resolved = normalized.get(printer_name.strip().casefold())
    if not resolved:
        raise ValueError(
            f'Printer "{printer_name}" was not found. '
            "Run `python tools/list_printers.py` to check installed printers."
        )
    return resolved


def _load_image(image_path: Path) -> "Image.Image":
    if _PIL_IMPORT_ERROR is not None:
        raise RuntimeError(
            "Pillow is required to print images. Install with: pip install Pillow"
        ) from _PIL_IMPORT_ERROR

    with Image.open(image_path) as source:
        if source.mode in {"RGBA", "LA"} or "transparency" in source.info:
            rgba = source.convert("RGBA")
            flattened = Image.new("RGB", rgba.size, "white")
            flattened.paste(rgba, mask=rgba.split()[-1])
            return flattened
        return source.convert("RGB")


def _fit_size(src_width: int, src_height: int, dst_width: int, dst_height: int) -> tuple[int, int]:
    scale = min(dst_width / src_width, dst_height / src_height)
    draw_width = max(1, int(src_width * scale))
    draw_height = max(1, int(src_height * scale))
    return draw_width, draw_height


def print_image(printer_name: str, image_path: Path, copies: int = 1) -> None:
    if copies < 1:
        raise ValueError("Copies must be at least 1.")

    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(f"Only PNG/JPG images are supported: {image_path}")

    resolved_printer = _resolve_printer_name(printer_name)
    image = _load_image(image_path)
    dib = ImageWin.Dib(image)

    printer_dc = win32ui.CreateDC()
    doc_started = False
    try:
        printer_dc.CreatePrinterDC(resolved_printer)

        printable_width = printer_dc.GetDeviceCaps(win32con.HORZRES)
        printable_height = printer_dc.GetDeviceCaps(win32con.VERTRES)
        if printable_width <= 0 or printable_height <= 0:
            raise RuntimeError("Printer reported an invalid printable area.")

        draw_width, draw_height = _fit_size(
            image.width, image.height, printable_width, printable_height
        )
        offset_x = printer_dc.GetDeviceCaps(win32con.PHYSICALOFFSETX)
        offset_y = printer_dc.GetDeviceCaps(win32con.PHYSICALOFFSETY)
        left = offset_x + (printable_width - draw_width) // 2
        top = offset_y + (printable_height - draw_height) // 2
        rect = (left, top, left + draw_width, top + draw_height)

        printer_dc.StartDoc(f"PhotoHaru - {image_path.name}")
        doc_started = True
        for _ in range(copies):
            printer_dc.StartPage()
            dib.draw(printer_dc.GetHandleOutput(), rect)
            printer_dc.EndPage()
        printer_dc.EndDoc()
        doc_started = False
    except Exception as exc:
        if doc_started:
            try:
                printer_dc.AbortDoc()
            except Exception:
                pass
        raise RuntimeError(
            f'Failed to print "{image_path}" on printer "{resolved_printer}": {exc}'
        ) from exc
    finally:
        try:
            printer_dc.DeleteDC()
        except Exception:
            pass

