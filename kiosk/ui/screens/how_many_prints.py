from __future__ import annotations

from pathlib import Path

from kiosk.ui.screens.status import StaticImageScreen

ROOT_DIR = Path(__file__).resolve().parents[3]


class HowManyPrintsScreen(StaticImageScreen):
    def __init__(self, main_window) -> None:
        super().__init__(
            main_window,
            "how_many_prints",
            ROOT_DIR / "assets" / "ui" / "4_How_many_prints" / "main_2.png",
            missing_text="How many prints",
        )
