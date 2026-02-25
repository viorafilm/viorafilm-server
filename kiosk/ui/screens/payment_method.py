from __future__ import annotations

from pathlib import Path

from kiosk.ui.screens.status import StaticImageScreen

ROOT_DIR = Path(__file__).resolve().parents[3]


def _resolve_payment_background() -> Path:
    primary = (
        ROOT_DIR
        / "assets"
        / "ui"
        / "5_Select_a_payment_Method"
        / "Paycashmain"
        / "Cash_main.png"
    )
    if primary.is_file():
        return primary

    fallback = (
        ROOT_DIR
        / "assets"
        / "ui"
        / "5_Select_a_payment_Method"
        / "cashcard_mode"
        / "cashcardmode_main.png"
    )
    if fallback.is_file():
        return fallback
    return primary


class PaymentMethodScreen(StaticImageScreen):
    def __init__(self, main_window) -> None:
        super().__init__(
            main_window,
            "payment_method",
            _resolve_payment_background(),
            missing_text="Payment method",
        )
