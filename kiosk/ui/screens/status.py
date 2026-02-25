from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from PySide6.QtCore import QRect, Qt
    from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import QLabel, QWidget
except ImportError:
    try:
        from PyQt6.QtCore import QRect, Qt
        from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
        from PyQt6.QtWidgets import QLabel, QWidget
    except ImportError:
        from PyQt5.QtCore import QRect, Qt
        from PyQt5.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap
        from PyQt5.QtWidgets import QLabel, QWidget

from kiosk.ui.hotspots import Hotspot

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


class _HotspotOverlay(QWidget):
    def __init__(self, screen: "StaticImageScreen") -> None:
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


class StaticImageScreen(QWidget):
    def __init__(
        self,
        main_window,
        screen_name: str,
        image_path: Path,
        missing_text: str = "",
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.screen_name = screen_name
        self.hotspots: list[Hotspot] = []
        self._overlay = _HotspotOverlay(self)
        self._image = QPixmap(str(image_path))
        self._missing_text = missing_text or screen_name
        if self._image.isNull():
            print(f"[{screen_name.upper()}] image not found: {image_path}")

    def set_hotspots(self, hotspots: list[Hotspot]) -> None:
        self.hotspots = hotspots
        self._overlay.update()

    def set_overlay_visible(self, visible: bool) -> None:
        self._overlay.setVisible(visible)
        self._overlay.update()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._overlay.setGeometry(self.rect())

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        if self._image.isNull():
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(self.rect(), ALIGN_CENTER, self._missing_text)
            return

        scaled = self._image.scaled(self.size(), KEEP_ASPECT, SMOOTH_TRANSFORM)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

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


class ThankYouScreen(StaticImageScreen):
    # TODO: expose via config/hotspot capture after final UI calibration.
    DEFAULT_QR_RECT = (760, 520, 400, 400)

    def __init__(self, main_window, image_path: Path) -> None:
        super().__init__(
            main_window,
            "thank_you",
            image_path,
            missing_text="Thank you",
        )
        self._qr_source: Optional[QPixmap] = None
        self._qr_label = QLabel(self)
        self._qr_label.setAlignment(ALIGN_CENTER)
        self._qr_label.setStyleSheet("QLabel { background: transparent; }")
        self._qr_label.hide()
        self._update_qr_geometry()

    def set_qr_path(self, qr_path: Optional[Path]) -> None:
        self._qr_source = None
        if qr_path:
            pixmap = QPixmap(str(qr_path))
            if pixmap.isNull():
                print(f"[THANK_YOU] qr image not found: {qr_path}")
            else:
                self._qr_source = pixmap
        self._render_qr()

    def _update_qr_geometry(self) -> None:
        self._qr_label.setGeometry(self.design_rect_to_widget(self.DEFAULT_QR_RECT))

    def _render_qr(self) -> None:
        if self._qr_source is None:
            self._qr_label.clear()
            self._qr_label.hide()
            return

        size = self._qr_label.contentsRect().size()
        if size.width() <= 0 or size.height() <= 0:
            return

        scaled = self._qr_source.scaled(size, KEEP_ASPECT, SMOOTH_TRANSFORM)
        self._qr_label.setPixmap(scaled)
        self._qr_label.show()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._update_qr_geometry()
        self._render_qr()
