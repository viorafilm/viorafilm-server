from __future__ import annotations

from pathlib import Path

try:
    from PySide6.QtCore import QRect, Qt, QTimer
    from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import QWidget
except ImportError:
    try:
        from PyQt6.QtCore import QRect, Qt, QTimer
        from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
        from PyQt6.QtWidgets import QWidget
    except ImportError:
        from PyQt5.QtCore import QRect, Qt, QTimer
        from PyQt5.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
        from PyQt5.QtWidgets import QWidget

from kiosk.ui.hotspots import Hotspot

ROOT_DIR = Path(__file__).resolve().parents[3]
DESIGN_WIDTH = 1920
DESIGN_HEIGHT = 1080

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


def _event_pos(event: QMouseEvent):
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()


class _HotspotOverlay(QWidget):
    def __init__(self, screen: "LoadingScreen") -> None:
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


class LoadingScreen(QWidget):
    def __init__(self, main_window, interval_ms: int = 180) -> None:
        super().__init__()
        self.main_window = main_window
        self.screen_name = "loading"
        self.hotspots: list[Hotspot] = []
        self._overlay = _HotspotOverlay(self)
        self._frames = self._load_frames()
        self._frame_index = 0
        self._timer = QTimer(self)
        self._timer.setInterval(max(150, min(250, int(interval_ms))))
        self._timer.timeout.connect(self._advance_frame)

    def _load_frames(self) -> list[QPixmap]:
        frames_dir = ROOT_DIR / "assets" / "ui" / "8_after_camera_loadingpage"
        if not frames_dir.is_dir():
            print(f"[LOADING] frame folder not found: {frames_dir}")
            return []

        png_files = [p for p in frames_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"]

        def _sort_key(path: Path):
            stem = path.stem
            if stem.isdigit():
                return (0, int(stem), path.name.lower())
            return (1, 0, path.name.lower())

        png_files.sort(key=_sort_key)
        frames: list[QPixmap] = []
        for path in png_files:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                frames.append(pixmap)
        if not frames:
            print("[LOADING] no usable PNG frames found")
        return frames

    def set_hotspots(self, hotspots: list[Hotspot]) -> None:
        self.hotspots = hotspots
        self._overlay.update()

    def set_overlay_visible(self, visible: bool) -> None:
        self._overlay.setVisible(visible)
        self._overlay.update()

    def _advance_frame(self) -> None:
        if not self._frames:
            return
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if self._frames:
            self._timer.start()

    def hideEvent(self, event):  # noqa: N802
        super().hideEvent(event)
        self._timer.stop()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._overlay.setGeometry(self.rect())

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        if self._frames:
            painter.drawPixmap(self.rect(), self._frames[self._frame_index])
        else:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(self.rect(), ALIGN_CENTER, "Loading...")

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

