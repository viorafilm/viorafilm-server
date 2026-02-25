from __future__ import annotations

from pathlib import Path

try:
    from PySide6.QtCore import QTimer
except ImportError:
    try:
        from PyQt6.QtCore import QTimer
    except ImportError:
        from PyQt5.QtCore import QTimer

from kiosk.ui.screens.status import StaticImageScreen

ROOT_DIR = Path(__file__).resolve().parents[3]


class PaymentCompleteScreen(StaticImageScreen):
    def __init__(self, main_window, screen_name: str, success: bool) -> None:
        image_path = (
            ROOT_DIR / "assets" / "ui" / "6_payment_complete" / "payment_success.png"
            if success
            else ROOT_DIR / "assets" / "ui" / "6_payment_complete" / "payment_failed.png"
        )
        super().__init__(
            main_window,
            screen_name,
            image_path,
            missing_text="Payment complete",
        )
        self.success = success

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if self.success:
            QTimer.singleShot(1000, self._auto_next)

    def _auto_next(self) -> None:
        if not self.isVisible():
            return
        if self.success and hasattr(self.main_window, "handle_payment_complete_success"):
            self.main_window.handle_payment_complete_success()
