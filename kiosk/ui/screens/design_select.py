from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

try:
    from PySide6.QtCore import QRect, QSize, Qt
    from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import QLabel, QToolButton, QWidget
except ImportError:
    try:
        from PyQt6.QtCore import QRect, QSize, Qt
        from PyQt6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen, QPixmap
        from PyQt6.QtWidgets import QLabel, QToolButton, QWidget
    except ImportError:
        from PyQt5.QtCore import QRect, QSize, Qt
        from PyQt5.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen, QPixmap
        from PyQt5.QtWidgets import QLabel, QToolButton, QWidget

from kiosk.ui.hotspots import Hotspot

ROOT_DIR = Path(__file__).resolve().parents[3]
DESIGN_WIDTH = 1920
DESIGN_HEIGHT = 1080
GRID_RECT = (90, 220, 1120, 650)
PREVIEW_RECT = (1240, 220, 600, 650)
GRID_ROWS = 2
GRID_COLS = 7
GRID_GAP_X = 20
GRID_GAP_Y = 20
MAX_ITEMS = GRID_ROWS * GRID_COLS

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
    def __init__(self, screen: "DesignSelectScreen") -> None:
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


class DesignSelectScreen(QWidget):
    def __init__(
        self,
        main_window,
        background_path: Path,
        on_design_selected: Callable[[int, str], None],
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.screen_name = "design_select"
        self.hotspots: list[Hotspot] = []
        self._background = QPixmap(str(background_path))
        self._overlay = _HotspotOverlay(self)
        self._on_design_selected = on_design_selected

        self.current_layout_id: Optional[str] = None
        self.frame_paths: list[Path] = []
        self.selected_design_index: Optional[int] = None
        self.selected_design_path: Optional[str] = None
        self.buttons: list[QToolButton] = []
        self.preview_label = QLabel("Select design", self)
        self.preview_label.setAlignment(ALIGN_CENTER)
        self.preview_label.setStyleSheet(
            "QLabel {"
            "border: 2px solid rgba(255,255,255,180);"
            "color: white;"
            "background-color: rgba(0,0,0,100);"
            "}"
        )
        self.preview_label.setWordWrap(True)
        self._preview_source: Optional[QPixmap] = None

        if self._background.isNull():
            print(f"[WARN] Background image not found: {background_path}")

        for i in range(MAX_ITEMS):
            button = QToolButton(self)
            button.setAutoRaise(False)
            button.hide()
            button.clicked.connect(lambda _, idx=i: self.select_design(idx))
            self.buttons.append(button)
        self._update_button_styles()
        self._update_preview_geometry()
        self._render_preview()

    def set_hotspots(self, hotspots: list[Hotspot]) -> None:
        self.hotspots = hotspots
        self._overlay.update()

    def set_overlay_visible(self, visible: bool) -> None:
        self._overlay.setVisible(visible)
        self._overlay.update()

    def set_layout(self, layout_id: str) -> None:
        self.current_layout_id = layout_id
        self.frame_paths = self._scan_design_files(layout_id)
        self.selected_design_index = None
        self.selected_design_path = None
        self._preview_source = None
        self._refresh_buttons()
        self._render_preview()
        print(f"[DESIGN] loaded layout={layout_id} count={len(self.frame_paths)}")

    def select_design(self, index: int) -> bool:
        if index < 0 or index >= len(self.frame_paths):
            return False
        self.selected_design_index = index
        self.selected_design_path = str(self.frame_paths[index])
        self._update_button_styles()
        self._set_preview_path(self.selected_design_path)
        self._on_design_selected(index, self.selected_design_path)
        print(f"[DESIGN] selected index={index + 1} path={self.selected_design_path}")
        return True

    def select_design_number(self, number: int) -> bool:
        if number < 1:
            return False
        return self.select_design(number - 1)

    def _scan_design_files(self, layout_id: str) -> list[Path]:
        frame_dir = (
            ROOT_DIR / "assets" / "ui" / "10_select_Design" / "Frame" / "Frame2" / layout_id
        )
        if not frame_dir.is_dir():
            print(f"[DESIGN] frame folder not found: {frame_dir}")
            return []

        png_files = [p for p in frame_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"]

        def _sort_key(path: Path):
            stem = path.stem
            if stem.isdigit():
                return (0, int(stem), "")
            return (1, 0, stem.lower())

        png_files.sort(key=_sort_key)
        return png_files

    def _refresh_buttons(self) -> None:
        self._update_grid_geometry()
        for i, button in enumerate(self.buttons):
            if i < len(self.frame_paths):
                image_path = self.frame_paths[i]
                pixmap = QPixmap(str(image_path))
                button.setEnabled(not pixmap.isNull())
                if not pixmap.isNull():
                    button.setIcon(QIcon(pixmap))
                button.show()
            else:
                button.hide()
        self._update_button_styles()

    def _update_button_styles(self) -> None:
        default_style = (
            "QToolButton {border: 2px solid rgba(255,255,255,120);"
            "background-color: rgba(0,0,0,80);}"
        )
        selected_style = (
            "QToolButton {border: 4px solid rgb(0,255,120);"
            "background-color: rgba(0,0,0,80);}"
        )
        for i, button in enumerate(self.buttons):
            if i == self.selected_design_index:
                button.setStyleSheet(selected_style)
            else:
                button.setStyleSheet(default_style)

    def _update_grid_geometry(self) -> None:
        left, top, width, height = GRID_RECT
        cell_width = (width - (GRID_COLS - 1) * GRID_GAP_X) // GRID_COLS
        cell_height = (height - (GRID_ROWS - 1) * GRID_GAP_Y) // GRID_ROWS

        for i, button in enumerate(self.buttons):
            row = i // GRID_COLS
            col = i % GRID_COLS
            x = left + col * (cell_width + GRID_GAP_X)
            y = top + row * (cell_height + GRID_GAP_Y)
            rect = self.design_rect_to_widget((x, y, cell_width, cell_height))
            button.setGeometry(rect)
            icon_w = max(1, rect.width() - 10)
            icon_h = max(1, rect.height() - 10)
            button.setIconSize(QSize(icon_w, icon_h))

    def _update_preview_geometry(self) -> None:
        self.preview_label.setGeometry(self.design_rect_to_widget(PREVIEW_RECT))

    def _set_preview_path(self, image_path: Optional[str]) -> None:
        if image_path:
            pixmap = QPixmap(image_path)
            self._preview_source = pixmap if not pixmap.isNull() else None
        else:
            self._preview_source = None
        self._render_preview()

    def _render_preview(self) -> None:
        if self._preview_source is None:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Select design")
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
        self._update_grid_geometry()
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
