from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

try:
    from PySide6.QtCore import QObject, QRect, Qt, Signal
    from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import QLabel, QWidget
except ImportError:
    try:
        from PyQt6.QtCore import QObject, QRect, Qt, pyqtSignal as Signal
        from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
        from PyQt6.QtWidgets import QLabel, QWidget
    except ImportError:
        from PyQt5.QtCore import QObject, QRect, Qt, pyqtSignal as Signal
        from PyQt5.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
        from PyQt5.QtWidgets import QLabel, QWidget

from kiosk.ui.hotspots import Hotspot

ROOT_DIR = Path(__file__).resolve().parents[3]
DESIGN_WIDTH = 1920
DESIGN_HEIGHT = 1080
PREVIEW_RECT = (200, 140, 1520, 800)

if hasattr(Qt, "MouseButton"):
    LEFT_BUTTON = Qt.MouseButton.LeftButton
else:
    LEFT_BUTTON = Qt.LeftButton

if hasattr(Qt, "WidgetAttribute"):
    WA_TRANSPARENT = Qt.WidgetAttribute.WA_TransparentForMouseEvents
else:
    WA_TRANSPARENT = Qt.WA_TransparentForMouseEvents

if hasattr(Qt, "AlignmentFlag"):
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
else:
    ALIGN_CENTER = Qt.AlignCenter

if hasattr(Qt, "AspectRatioMode"):
    KEEP_ASPECT = Qt.AspectRatioMode.KeepAspectRatio
    SMOOTH_TRANSFORM = Qt.TransformationMode.SmoothTransformation
else:
    KEEP_ASPECT = Qt.KeepAspectRatio
    SMOOTH_TRANSFORM = Qt.SmoothTransformation


def _event_pos(event: QMouseEvent):
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()


class PrintWorker(QObject):
    success = Signal()
    failure = Signal(str)

    def __init__(
        self,
        printer_name: str,
        image_path: Path,
        copies: int = 2,
        two_jobs: bool = True,
    ) -> None:
        super().__init__()
        self.printer_name = printer_name
        self.image_path = Path(image_path)
        self.copies = max(1, int(copies))
        self.two_jobs = bool(two_jobs)

    def run(self) -> None:
        try:
            if os.getenv("DRY_RUN_PRINT", "").strip() == "1":
                time.sleep(1.2)
                self.success.emit()
                return

            from kiosk.services.printer.win_spooler import print_image

            if self.two_jobs:
                for _ in range(self.copies):
                    print_image(self.printer_name, self.image_path, copies=1)
            else:
                print_image(self.printer_name, self.image_path, copies=self.copies)
            self.success.emit()
        except Exception as exc:
            self.failure.emit(str(exc))


class _HotspotOverlay(QWidget):
    def __init__(self, screen: "PreviewScreen") -> None:
        super().__init__(screen)
        self.screen = screen
        self.setAttribute(WA_TRANSPARENT, True)
        self.hide()

    def paintEvent(self, event):  # noqa: N802
        if not self.screen.hotspots:
            return
        painter = QPainter(self)
        pen = QPen(QColor(0, 255, 0, 220))
        pen.setWidth(3)
        painter.setPen(pen)
        for hotspot in self.screen.hotspots:
            painter.drawRect(self.screen.design_rect_to_widget(hotspot.rect))


class PreviewScreen(QWidget):
    def __init__(self, main_window) -> None:
        super().__init__()
        self.main_window = main_window
        self.screen_name = "preview"
        self.hotspots: list[Hotspot] = []
        self._overlay = _HotspotOverlay(self)
        self._background = QPixmap()
        self._preview_source: Optional[QPixmap] = None
        self.layout_id: Optional[str] = None
        self.confirm_locked = False

        self.preview_label = QLabel("No print preview", self)
        self.preview_label.setAlignment(ALIGN_CENTER)
        self.preview_label.setStyleSheet(
            "QLabel {"
            "border: 2px solid rgba(255,255,255,180);"
            "color: white;"
            "background-color: rgba(0,0,0,120);"
            "}"
        )
        self.preview_label.setWordWrap(True)
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(ALIGN_CENTER)
        self.status_label.setStyleSheet("QLabel { color: rgb(255,220,120); }")

        self._update_preview_geometry()
        self._render_preview()

    def set_hotspots(self, hotspots: list[Hotspot]) -> None:
        self.hotspots = hotspots
        self._overlay.update()

    def set_overlay_visible(self, visible: bool) -> None:
        self._overlay.setVisible(visible)
        self._overlay.update()

    def set_layout(self, layout_id: Optional[str]) -> None:
        self.layout_id = layout_id
        self._background = QPixmap()
        if layout_id:
            path = ROOT_DIR / "assets" / "ui" / "9_select_photo" / f"main_{layout_id}.png"
            if path.is_file():
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    self._background = pixmap
            else:
                print(f"[PREVIEW] background not found: {path}")
        self.update()

    def set_print_image(self, print_path: Optional[str]) -> None:
        self._preview_source = None
        if print_path:
            pixmap = QPixmap(print_path)
            if not pixmap.isNull():
                self._preview_source = pixmap
            else:
                print(f"[PREVIEW] failed to load print image: {print_path}")
        self._render_preview()

    def set_confirm_locked(self, locked: bool) -> None:
        self.confirm_locked = bool(locked)
        if self.confirm_locked:
            self.status_label.setText("Printing...")
        else:
            self.status_label.setText("")

    @staticmethod
    def create_print_worker(
        printer_name: str,
        image_path: Path,
        copies: int = 2,
        two_jobs: bool = True,
    ) -> PrintWorker:
        return PrintWorker(
            printer_name=printer_name,
            image_path=image_path,
            copies=copies,
            two_jobs=two_jobs,
        )

    def _update_preview_geometry(self) -> None:
        self.preview_label.setGeometry(self.design_rect_to_widget(PREVIEW_RECT))
        status_rect = self.design_rect_to_widget((200, 960, 1520, 60))
        self.status_label.setGeometry(status_rect)

    def _render_preview(self) -> None:
        if self._preview_source is None:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("No print preview")
            return
        size = self.preview_label.contentsRect().size()
        if size.width() <= 0 or size.height() <= 0:
            return
        scaled = self._preview_source.scaled(size, KEEP_ASPECT, SMOOTH_TRANSFORM)
        self.preview_label.setText("")
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._overlay.setGeometry(self.rect())
        self._update_preview_geometry()
        self._render_preview()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        if not self._background.isNull():
            painter.drawPixmap(self.rect(), self._background)

    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802
        if event.button() != LEFT_BUTTON:
            return
        pos = _event_pos(event)
        x, y = self.widget_to_design(pos.x(), pos.y())
        self.main_window.handle_screen_click(self, x, y)

    def widget_to_design(self, x: int, y: int) -> tuple[int, int]:
        if self.width() <= 0 or self.height() <= 0:
            return 0, 0
        dx = int(x * DESIGN_WIDTH / self.width())
        dy = int(y * DESIGN_HEIGHT / self.height())
        dx = max(0, min(DESIGN_WIDTH - 1, dx))
        dy = max(0, min(DESIGN_HEIGHT - 1, dy))
        return dx, dy

    def design_rect_to_widget(self, rect: tuple[int, int, int, int]) -> QRect:
        x, y, w, h = rect
        sx = self.width() / DESIGN_WIDTH if DESIGN_WIDTH else 1.0
        sy = self.height() / DESIGN_HEIGHT if DESIGN_HEIGHT else 1.0
        return QRect(
            int(x * sx),
            int(y * sy),
            max(1, int(w * sx)),
            max(1, int(h * sy)),
        )
