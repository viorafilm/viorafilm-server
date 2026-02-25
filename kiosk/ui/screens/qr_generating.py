from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal
except ImportError:
    try:
        from PyQt6.QtCore import QObject, QThread, QTimer, Qt, pyqtSignal as Signal
    except ImportError:
        from PyQt5.QtCore import QObject, QThread, QTimer, Qt, pyqtSignal as Signal

from kiosk.services.upload.dummy_uploader import DummyUploader
from kiosk.utils.qr import generate_qr_png
from kiosk.ui.screens.status import StaticImageScreen

ROOT_DIR = Path(__file__).resolve().parents[3]

if hasattr(Qt, "Key"):
    KEY_ENTER = Qt.Key.Key_Enter
    KEY_RETURN = Qt.Key.Key_Return
else:
    KEY_ENTER = Qt.Key_Enter
    KEY_RETURN = Qt.Key_Return

if hasattr(Qt, "FocusPolicy"):
    STRONG_FOCUS = Qt.FocusPolicy.StrongFocus
else:
    STRONG_FOCUS = Qt.StrongFocus


class UploadWorker(QObject):
    success = Signal(str)
    failure = Signal(str)
    finished = Signal()

    def __init__(self, session) -> None:
        super().__init__()
        self.session = session

    def run(self) -> None:
        try:
            if self.session is None:
                raise RuntimeError("session missing")

            session_id = self.session.session_id or self.session.session_dir.name
            if self.session.print_path:
                print_path = Path(self.session.print_path)
            else:
                print_path = self.session.print_dir / "print.jpg"
            if not print_path.is_file():
                raise FileNotFoundError(f"print file not found: {print_path}")

            uploader = DummyUploader()
            share_url = uploader.upload_print(session_id, print_path)
            qr_path = generate_qr_png(share_url, self.session.qr_dir / "qr.png")
            self.session.set_share_url(share_url)
            self.session.save_qr(qr_path)
            self.success.emit(share_url)
        except Exception as exc:
            if self.session is not None:
                try:
                    self.session.clear_share()
                except Exception:
                    pass
            self.failure.emit(str(exc))
        finally:
            self.finished.emit()


class QrGeneratingScreen(StaticImageScreen):
    def __init__(self, main_window) -> None:
        super().__init__(
            main_window,
            "qr_generating",
            ROOT_DIR / "assets" / "ui" / "11_Qrcode" / "Generation_QR_code.png",
            missing_text="Generating QR...",
        )
        self.setFocusPolicy(STRONG_FOCUS)
        self._token = 0
        self._active_token = 0
        self._active_session = None
        self._thread: Optional[QThread] = None
        self._worker: Optional[UploadWorker] = None
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._token += 1
        token = self._token
        self.setFocus()
        self._timeout_timer.start(15000)
        self._start_worker(token)

    def hideEvent(self, event):  # noqa: N802
        super().hideEvent(event)
        self._token += 1
        self._timeout_timer.stop()

    def _get_active_session(self):
        if hasattr(self.main_window, "get_active_session"):
            return self.main_window.get_active_session()
        screens = getattr(self.main_window, "screens", {})
        camera_screen = screens.get("camera")
        return getattr(camera_screen, "session", None)

    def _start_worker(self, token: int) -> None:
        session = self._get_active_session()
        if session is None:
            print("[QR_GEN] session missing")
            self._finish(token, None)
            return
        if self._thread is not None and self._thread.isRunning():
            print("[QR_GEN] worker already running")
            return

        worker = UploadWorker(session)
        thread = QThread(self)
        worker.moveToThread(thread)
        self._active_token = token
        self._active_session = session

        thread.started.connect(worker.run)
        worker.success.connect(self._on_worker_success)
        worker.failure.connect(self._on_worker_failure)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        self._worker = worker
        self._thread = thread
        print("[QR_GEN] upload worker started")
        thread.start()

    def _on_worker_success(self, share_url: str) -> None:
        if self._active_token != self._token:
            return
        self._timeout_timer.stop()
        print(f"[QR_GEN] upload ok url={share_url}")
        if hasattr(self.main_window, "on_upload_success"):
            self.main_window.on_upload_success(share_url)
            return
        qr_path = getattr(self._active_session, "qr_path", None)
        self._finish(self._token, qr_path)

    def _on_worker_failure(self, error_message: str) -> None:
        if self._active_token != self._token:
            return
        self._timeout_timer.stop()
        print(f"[QR_GEN] upload failed: {error_message}")
        if hasattr(self.main_window, "on_upload_fail"):
            self.main_window.on_upload_fail(error_message)
            return
        self._finish(self._token, None)

    def _on_thread_finished(self) -> None:
        self._active_session = None
        self._thread = None
        self._worker = None

    def _finish(self, token: int, qr_path: Optional[Path]) -> None:
        if token != self._token:
            return
        if hasattr(self.main_window, "handle_qr_generating_done"):
            self.main_window.handle_qr_generating_done(qr_path)

    def _on_timeout(self) -> None:
        self._token += 1
        print("[QR_GEN] timeout")
        if hasattr(self.main_window, "on_upload_fail"):
            self.main_window.on_upload_fail("upload timeout")
            return
        if hasattr(self.main_window, "handle_qr_generating_done"):
            self.main_window.handle_qr_generating_done(None)

    def keyPressEvent(self, event):  # noqa: N802
        key = event.key()
        if key in (KEY_ENTER, KEY_RETURN):
            self._timeout_timer.stop()
            self._token += 1
            if hasattr(self.main_window, "on_upload_fail"):
                self.main_window.on_upload_fail("upload skipped")
                return
            if hasattr(self.main_window, "handle_qr_generating_done"):
                self.main_window.handle_qr_generating_done(None)
            return
        super().keyPressEvent(event)
