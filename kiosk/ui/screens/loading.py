from __future__ import annotations

from pathlib import Path
import re

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

if hasattr(Qt, "AspectRatioMode"):
    KEEP_ASPECT = Qt.AspectRatioMode.KeepAspectRatio
    SMOOTH_TRANSFORM = Qt.TransformationMode.SmoothTransformation
    WORD_WRAP = Qt.TextFlag.TextWordWrap
else:
    KEEP_ASPECT = Qt.KeepAspectRatio
    SMOOTH_TRANSFORM = Qt.SmoothTransformation
    WORD_WRAP = Qt.TextWordWrap


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
        self._status_message = ""
        self._status_animate = False
        self._status_phase = 0
        self._status_percent: int | None = None
        self._status_lines: list[str] = []
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(260)
        self._status_timer.timeout.connect(self._advance_status_phase)
        self._preview_frames: list[QPixmap] = []
        self._preview_frame_index = 0
        self._preview_timer = QTimer(self)
        self._preview_timer.setInterval(100)
        self._preview_timer.timeout.connect(self._advance_preview_frame)

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

    def _advance_status_phase(self) -> None:
        self._status_phase = (self._status_phase + 1) % 4
        if self._status_message:
            self.update()

    def _advance_preview_frame(self) -> None:
        if len(self._preview_frames) <= 1:
            return
        self._preview_frame_index = (self._preview_frame_index + 1) % len(self._preview_frames)
        self.update()

    def set_preview_animation(
        self,
        frames_by_shot: dict[int, list[bytes]] | None,
        interval_ms: int = 100,
    ) -> None:
        preview_frames: list[QPixmap] = []
        if isinstance(frames_by_shot, dict):
            for shot_index in sorted(frames_by_shot.keys()):
                bucket = frames_by_shot.get(shot_index) or []
                shot_frames: list[QPixmap] = []
                for raw in bucket:
                    if not raw:
                        continue
                    pixmap = QPixmap()
                    if pixmap.loadFromData(raw):
                        shot_frames.append(pixmap)
                if not shot_frames:
                    continue
                preview_frames.extend(shot_frames)
                linger_frames = max(1, min(3, len(shot_frames) // 3))
                preview_frames.extend([shot_frames[-1]] * linger_frames)
        self._preview_frames = preview_frames
        self._preview_frame_index = 0
        self._preview_timer.stop()
        self._preview_timer.setInterval(max(80, min(250, int(interval_ms or 100))))
        if len(self._preview_frames) > 1 and self.isVisible():
            self._preview_timer.start()
        self.update()

    def clear_preview_animation(self) -> None:
        self._preview_timer.stop()
        self._preview_frames = []
        self._preview_frame_index = 0
        self.update()

    def set_status_message(self, message: str, animate: bool = False) -> None:
        self._status_message = str(message or "").strip()
        self._status_percent = None
        self._status_lines = []
        parsed_lines = [line.strip() for line in self._status_message.splitlines() if line.strip()]
        for line in parsed_lines:
            match = re.search(r"(\d{1,3})\s*%", line)
            if match:
                try:
                    value = int(match.group(1))
                except Exception:
                    value = 0
                self._status_percent = max(0, min(100, value))
                continue
            self._status_lines.append(line)
        self._status_animate = bool(animate and self._status_message)
        self._status_phase = 0
        if self._status_animate and self.isVisible():
            self._status_timer.start()
        else:
            self._status_timer.stop()
        self.update()

    def clear_status_message(self) -> None:
        self._status_message = ""
        self._status_animate = False
        self._status_phase = 0
        self._status_percent = None
        self._status_lines = []
        self._status_timer.stop()
        self.update()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if self._frames:
            self._timer.start()
        if self._status_animate and self._status_message:
            self._status_timer.start()
        if len(self._preview_frames) > 1:
            self._preview_timer.start()

    def hideEvent(self, event):  # noqa: N802
        super().hideEvent(event)
        self._timer.stop()
        self._status_timer.stop()
        self._preview_timer.stop()

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

        if self._preview_frames:
            box_w = max(260, int(self.width() * 0.40))
            box_h = max(180, int(self.height() * 0.33))
            box_x = int((self.width() - box_w) / 2)
            box_y = int(self.height() * 0.10)
            box_rect = QRect(box_x, box_y, box_w, box_h)
            painter.fillRect(box_rect, QColor(0, 0, 0, 160))
            preview_pen = QPen(QColor(255, 255, 255, 210))
            preview_pen.setWidth(3)
            painter.setPen(preview_pen)
            painter.drawRect(box_rect)

            frame = self._preview_frames[self._preview_frame_index % len(self._preview_frames)]
            if not frame.isNull():
                inner_rect = QRect(
                    box_x + 18,
                    box_y + 18,
                    max(1, box_w - 36),
                    max(1, box_h - 36),
                )
                scaled = frame.scaled(inner_rect.size(), KEEP_ASPECT, SMOOTH_TRANSFORM)
                draw_x = inner_rect.x() + max(0, int((inner_rect.width() - scaled.width()) / 2))
                draw_y = inner_rect.y() + max(0, int((inner_rect.height() - scaled.height()) / 2))
                painter.drawPixmap(draw_x, draw_y, scaled)

        if self._status_message:
            w = int(self.width() * 0.80)
            h = max(180, int(self.height() * 0.27))
            x = int((self.width() - w) / 2)
            y = int(self.height() * 0.62)
            box_rect = QRect(x, y, w, h)
            painter.fillRect(box_rect, QColor(0, 0, 0, 175))
            pen = QPen(QColor(255, 255, 255, 210))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(box_rect)

            if self._status_percent is not None:
                percent = max(0, min(100, int(self._status_percent)))
                bar_x = x + 34
                bar_y = y + 22
                bar_h = 46
                percent_w = 132
                bar_w = max(160, w - 34 - 30 - percent_w)
                track_rect = QRect(bar_x, bar_y, bar_w, bar_h)
                painter.fillRect(track_rect, QColor(255, 255, 255, 26))
                track_pen = QPen(QColor(255, 255, 255, 130))
                track_pen.setWidth(1)
                painter.setPen(track_pen)
                painter.drawRect(track_rect)

                seg_gap = 8
                seg_count = 10
                inner_x = bar_x + 10
                inner_y = bar_y + 10
                inner_w = max(10, bar_w - 20)
                inner_h = max(10, bar_h - 20)
                seg_w = max(4, int((inner_w - (seg_gap * (seg_count - 1))) / seg_count))
                filled = max(0, min(seg_count, int((percent + 9) / 10)))
                cursor = inner_x
                for idx in range(seg_count):
                    seg_rect = QRect(cursor, inner_y, seg_w, inner_h)
                    color = QColor(70, 190, 255, 230) if idx < filled else QColor(255, 255, 255, 40)
                    painter.fillRect(seg_rect, color)
                    cursor += seg_w + seg_gap

                painter.setPen(QColor(255, 255, 255))
                percent_font = painter.font()
                percent_font.setBold(True)
                percent_font.setPixelSize(max(30, int(bar_h * 0.72)))
                painter.setFont(percent_font)
                percent_rect = QRect(bar_x + bar_w + 8, bar_y, percent_w, bar_h)
                painter.drawText(percent_rect, ALIGN_CENTER, f"{percent}%")

                if self._status_lines:
                    info = "\n".join(self._status_lines[:2])
                    info_rect = QRect(x + 28, bar_y + bar_h + 18, w - 56, max(40, h - (bar_h + 48)))
                    info_font = painter.font()
                    info_font.setBold(True)
                    info_font.setPixelSize(max(22, int(h * 0.15)))
                    painter.setFont(info_font)
                    painter.drawText(info_rect, ALIGN_CENTER | WORD_WRAP, info)
            else:
                dots = "." * self._status_phase if self._status_animate else ""
                lines = [line for line in self._status_message.splitlines() if line.strip()]
                if not lines:
                    return
                if dots:
                    lines = [f"{line}{dots}" for line in lines]
                display = "\n".join(lines)
                painter.setPen(QColor(255, 255, 255))
                message_font = painter.font()
                message_font.setBold(True)
                message_font.setPixelSize(max(24, int(h * 0.18)))
                painter.setFont(message_font)
                painter.drawText(box_rect, ALIGN_CENTER | WORD_WRAP, display)

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
