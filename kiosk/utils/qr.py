from __future__ import annotations

from pathlib import Path

import qrcode


def generate_qr_png(
    url: str,
    out_path: Path,
    box_size: int = 10,
    border: int = 2,
) -> Path:
    output_path = Path(out_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=max(1, int(box_size)),
        border=max(0, int(border)),
    )
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    image.save(output_path, format="PNG")
    return output_path
