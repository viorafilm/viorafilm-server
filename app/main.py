from __future__ import annotations

import ctypes
import base64
import hashlib
import io
import json
import logging
import math
import mimetypes
import os
import queue
import re
import socket
import shutil
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from ctypes import wintypes
from urllib.parse import unquote, urlencode, urlsplit

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

try:
    import serial
    from serial import SerialException
    from serial.tools import list_ports as serial_list_ports
except Exception:
    serial = None
    SerialException = Exception
    serial_list_ports = None

try:
    import requests
except Exception:
    requests = None

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    import winsound  # type: ignore[attr-defined]
except Exception:
    winsound = None  # type: ignore[assignment]

def _resolve_root_dir() -> Path:
    # Frozen(one-folder) build should use executable location as install root.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    script_path = Path(__file__).resolve()
    candidates = [
        script_path.parents[1],  # repo-style: <root>/app/main.py
        script_path.parent,      # flat-style: <root>/main.py
        Path.cwd(),
    ]
    for candidate in candidates:
        if (candidate / "kiosk").is_dir():
            return candidate
    return script_path.parents[1]


def _resolve_bundle_root(install_root: Path) -> Path:
    if not getattr(sys, "frozen", False):
        return install_root
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidate = Path(str(meipass)).resolve()
        if candidate.is_dir():
            return candidate
    return install_root


INSTALL_ROOT = _resolve_root_dir()
ROOT_DIR = _resolve_bundle_root(INSTALL_ROOT)
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(INSTALL_ROOT) not in sys.path:
    sys.path.insert(0, str(INSTALL_ROOT))

if load_dotenv is not None:
    try:
        env_candidates = [
            INSTALL_ROOT / ".env",
            ROOT_DIR / ".env",
        ]
        for env_path in env_candidates:
            if env_path.is_file():
                load_dotenv(env_path, override=False)
                break
    except Exception as exc:
        print(f"[BOOT] dotenv load failed: {exc}")

_LOGGING_INITIALIZED = False
_LOG_FILE_PATH: Optional[Path] = None


def _safe_boot_write(message: str) -> None:
    text = str(message or "")
    if not text:
        return
    candidates = [
        getattr(sys, "__stderr__", None),
        getattr(sys, "__stdout__", None),
        getattr(sys, "stderr", None),
        getattr(sys, "stdout", None),
    ]
    for stream in candidates:
        if stream is None or not hasattr(stream, "write"):
            continue
        try:
            stream.write(text)
            if hasattr(stream, "flush"):
                stream.flush()
            return
        except Exception:
            continue


def _is_writable_stream(stream) -> bool:
    if stream is None or not hasattr(stream, "write"):
        return False
    try:
        stream.write("")
        if hasattr(stream, "flush"):
            stream.flush()
        return True
    except Exception:
        return False


class _NullStream:
    def write(self, message) -> int:
        try:
            return len(str(message or ""))
        except Exception:
            return 0

    def flush(self) -> None:
        return

    def isatty(self) -> bool:
        return False


class _LoggerStream:
    def __init__(
        self,
        logger: logging.Logger,
        level: int,
        fallback_stream,
        forward_to_logger: bool = True,
    ) -> None:
        self._logger = logger
        self._level = level
        self._fallback = fallback_stream
        self._forward_to_logger = bool(forward_to_logger)
        self._buffer = ""
        self._in_write = False

    def write(self, message) -> int:
        if message is None:
            return 0
        text = str(message)
        if not text:
            return 0
        if self._in_write:
            try:
                if self._fallback is not None and hasattr(self._fallback, "write"):
                    self._fallback.write(text)
            except Exception:
                pass
            return len(text)
        self._in_write = True
        self._buffer += text
        try:
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                line = line.rstrip("\r")
                if not line:
                    continue
                if self._forward_to_logger:
                    try:
                        self._logger.log(self._level, line)
                    except Exception:
                        try:
                            if self._fallback is not None and hasattr(self._fallback, "write"):
                                self._fallback.write(line + "\n")
                        except Exception:
                            pass
                else:
                    try:
                        if self._fallback is not None and hasattr(self._fallback, "write"):
                            self._fallback.write(line + "\n")
                    except Exception:
                        pass
        finally:
            self._in_write = False
        return len(text)

    def flush(self) -> None:
        line = self._buffer.strip()
        self._buffer = ""
        if line and not self._in_write and self._forward_to_logger:
            self._in_write = True
            try:
                self._logger.log(self._level, line)
            except Exception:
                pass
            finally:
                self._in_write = False
        try:
            if self._fallback is not None and hasattr(self._fallback, "flush"):
                self._fallback.flush()
        except Exception:
            pass

    def isatty(self) -> bool:
        return False


def _to_positive_int(value, default_value: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        return default_value
    return parsed if parsed > 0 else default_value


def _normalize_kiosk_api_base_url(value: object) -> str:
    raw = str(value or "").strip().rstrip("/")
    if not raw:
        return ""
    try:
        split = urlsplit(raw)
    except Exception:
        return raw
    if not split.scheme or not split.netloc:
        return raw
    path = str(split.path or "").rstrip("/")
    segments = [seg for seg in path.split("/") if seg]
    if "api" not in segments:
        path = f"{path}/api" if path else "/api"
    return f"{split.scheme}://{split.netloc}{path}".rstrip("/")


def _remap_legacy_install_path(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    normalized = text.replace("\\", "/")
    lowered = normalized.lower()
    legacy_prefixes = (
        "d:/photoharu/",
        "d:/photoharu",
    )
    for prefix in legacy_prefixes:
        if lowered.startswith(prefix):
            suffix = normalized[len(prefix) :].lstrip("/")
            mapped = ROOT_DIR / suffix if suffix else ROOT_DIR
            return str(mapped)
    return text


def _iter_runtime_data_dir_candidates() -> list[Path]:
    candidates: list[Path] = []
    custom = str(os.environ.get("VIORAFILM_DATA_DIR", "")).strip()
    if custom:
        candidates.append(Path(custom))

    program_data = str(os.environ.get("PROGRAMDATA", "")).strip()
    if program_data:
        candidates.append(Path(program_data) / "ViorafilmKiosk")

    public_root = str(os.environ.get("PUBLIC", "")).strip()
    if public_root:
        candidates.append(Path(public_root) / "Documents" / "ViorafilmKiosk")

    local_appdata = str(os.environ.get("LOCALAPPDATA", "")).strip()
    if local_appdata:
        candidates.append(Path(local_appdata) / "ViorafilmKiosk")

    roaming_appdata = str(os.environ.get("APPDATA", "")).strip()
    if roaming_appdata:
        candidates.append(Path(roaming_appdata) / "ViorafilmKiosk")

    expanded_local = os.path.expandvars(r"%LOCALAPPDATA%").strip()
    if expanded_local and expanded_local != r"%LOCALAPPDATA%":
        candidates.append(Path(expanded_local) / "ViorafilmKiosk")

    user_profile = str(os.environ.get("USERPROFILE", "")).strip()
    if user_profile:
        candidates.append(Path(user_profile) / "AppData" / "Local" / "ViorafilmKiosk")

    try:
        home = Path.home()
        if str(home).strip():
            candidates.append(home / "AppData" / "Local" / "ViorafilmKiosk")
            candidates.append(home / "ViorafilmKiosk")
    except Exception:
        pass

    for temp_key in ("TEMP", "TMP"):
        temp_dir = str(os.environ.get(temp_key, "")).strip()
        if temp_dir:
            candidates.append(Path(temp_dir) / "ViorafilmKiosk")

    candidates.append(Path.cwd() / "ViorafilmKioskData")

    seen: set[str] = set()
    dedup: list[Path] = []
    for candidate in candidates:
        key = str(candidate).strip().lower()
        if key and key not in seen:
            seen.add(key)
            dedup.append(candidate)
    return dedup


def _preferred_runtime_data_dirs() -> list[Path]:
    preferred: list[Path] = []
    program_data = str(os.environ.get("PROGRAMDATA", "")).strip()
    if program_data:
        preferred.append(Path(program_data) / "ViorafilmKiosk")
    public_root = str(os.environ.get("PUBLIC", "")).strip()
    if public_root:
        preferred.append(Path(public_root) / "Documents" / "ViorafilmKiosk")
    return preferred


def _default_runtime_data_dir() -> Path:
    def _can_write(path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / f".vf_probe_{os.getpid()}.tmp"
            probe.write_text("ok", encoding="utf-8")
            try:
                probe.unlink(missing_ok=True)
            except Exception:
                pass
            return True
        except Exception:
            return False

    dedup = _iter_runtime_data_dir_candidates()
    for candidate in dedup:
        if _can_write(candidate):
            return candidate
    return dedup[0] if dedup else (Path.cwd() / "ViorafilmKioskData")


def _path_is_within(child: Path, parent: Path) -> bool:
    try:
        child_resolved = child.resolve(strict=False)
        parent_resolved = parent.resolve(strict=False)
    except Exception:
        return False
    try:
        child_resolved.relative_to(parent_resolved)
        return True
    except Exception:
        return False


def _is_protected_install_path(path: Path) -> bool:
    normalized = str(path).replace("/", "\\").lower()
    if "\\program files\\" in normalized:
        return True
    if "\\windows\\" in normalized:
        return True
    if getattr(sys, "frozen", False):
        install_roots: list[Path] = []
        for root in (INSTALL_ROOT, ROOT_DIR):
            try:
                install_roots.append(Path(root).resolve(strict=False))
            except Exception:
                continue
        for root in install_roots:
            if _path_is_within(path, root):
                return True
    return False


def _sanitize_runtime_path(path: Path, fallback: Path, label: str) -> Path:
    candidate = Path(path)
    if getattr(sys, "frozen", False) and _is_protected_install_path(candidate):
        _safe_boot_write(
            f"[BOOT] unsafe {label} path redirected: {candidate} -> {fallback}\n"
        )
        return fallback
    return candidate


def _resolve_log_dir(log_dir_name: str) -> Path:
    raw = str(log_dir_name or "logs").strip() or "logs"
    candidate = Path(raw)
    if candidate.is_absolute():
        fallback = _default_runtime_data_dir() / "logs"
        return _sanitize_runtime_path(candidate, fallback, "log_dir")
    if getattr(sys, "frozen", False):
        return _default_runtime_data_dir() / candidate
    return ROOT_DIR / candidate


def _resolve_runtime_config_path() -> Path:
    env_override = str(os.environ.get("VIORAFILM_CONFIG_PATH", "")).strip()
    if env_override:
        path = Path(env_override)
        if not path.is_absolute():
            base = _default_runtime_data_dir() if getattr(sys, "frozen", False) else ROOT_DIR
            path = (base / path).resolve()
        fallback = _default_runtime_data_dir() / "config" / "config.json"
        path = _sanitize_runtime_path(path, fallback, "config_path")
        if _is_directory_writable(path.parent):
            return path
        _safe_boot_write(
            f"[BOOT] config path not writable, fallback: {path} -> {fallback}\n"
        )
        return fallback

    bundled = ROOT_DIR / "config" / "config.json"
    if not getattr(sys, "frozen", False):
        return bundled

    default_runtime_path = _default_runtime_data_dir() / "config" / "config.json"
    runtime_path = default_runtime_path
    preferred_existing: list[Path] = []
    for root in _preferred_runtime_data_dirs():
        candidate = _sanitize_runtime_path(
            root / "config" / "config.json",
            default_runtime_path,
            "runtime_config_path",
        )
        try:
            if candidate.is_file():
                preferred_existing.append(candidate)
        except Exception:
            continue
    if preferred_existing:
        try:
            preferred_existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            runtime_path = preferred_existing[0]
        except Exception:
            runtime_path = preferred_existing[0]
    runtime_path = _sanitize_runtime_path(
        runtime_path,
        default_runtime_path,
        "runtime_config_path",
    )
    try:
        runtime_path.parent.mkdir(parents=True, exist_ok=True)
        if (not runtime_path.is_file()) and bundled.is_file():
            shutil.copy2(bundled, runtime_path)
    except Exception as exc:
        _safe_boot_write(f"[BOOT] runtime config prepare failed: {exc}\n")
    if not _is_directory_writable(runtime_path.parent):
        fallback = default_runtime_path
        try:
            fallback.parent.mkdir(parents=True, exist_ok=True)
            if (not fallback.is_file()) and bundled.is_file():
                shutil.copy2(bundled, fallback)
            runtime_path = fallback
        except Exception:
            pass
    return runtime_path


def _resolve_runtime_out_dir() -> Path:
    env_override = str(os.environ.get("VIORAFILM_OUT_DIR", "")).strip()
    if env_override:
        path = Path(env_override)
        if not path.is_absolute():
            base = _default_runtime_data_dir() if getattr(sys, "frozen", False) else ROOT_DIR
            path = (base / path).resolve()
        fallback = _default_runtime_data_dir() / "out"
        path = _sanitize_runtime_path(path, fallback, "out_dir")
        if _is_directory_writable(path):
            return path
        _safe_boot_write(f"[BOOT] out_dir not writable, fallback: {path} -> {fallback}\n")
        return fallback
    if getattr(sys, "frozen", False):
        target = _default_runtime_data_dir() / "out"
    else:
        target = ROOT_DIR / "out"
    if _is_directory_writable(target):
        return target
    return _default_runtime_data_dir() / "out"


def _resolve_runtime_sessions_dir() -> Path:
    env_override = str(
        os.environ.get("KIOSK_SESSIONS_DIR", os.environ.get("VIORAFILM_SESSIONS_DIR", ""))
    ).strip()
    if env_override:
        path = Path(env_override)
        if not path.is_absolute():
            base = _default_runtime_data_dir() if getattr(sys, "frozen", False) else ROOT_DIR
            path = (base / path).resolve()
        fallback = _default_runtime_data_dir() / "sessions"
        path = _sanitize_runtime_path(path, fallback, "sessions_dir")
        if _is_directory_writable(path):
            return path
        _safe_boot_write(
            f"[BOOT] sessions_dir not writable, fallback: {path} -> {fallback}\n"
        )
        return fallback
    if getattr(sys, "frozen", False):
        target = _default_runtime_data_dir() / "sessions"
    else:
        target = ROOT_DIR / "sessions"
    if _is_directory_writable(target):
        return target
    return _default_runtime_data_dir() / "sessions"


def _is_directory_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".vf_write_probe_{os.getpid()}.tmp"
        probe.write_text("ok", encoding="utf-8")
        try:
            probe.unlink(missing_ok=True)
        except Exception:
            pass
        return True
    except Exception:
        return False


def setup_logging() -> Path:
    global _LOGGING_INITIALIZED
    global _LOG_FILE_PATH

    if _LOGGING_INITIALIZED and _LOG_FILE_PATH is not None:
        return _LOG_FILE_PATH

    config_path = _resolve_runtime_config_path()
    level_name = "DEBUG"
    log_dir_name = "logs"
    rotate_mb = 10
    backup_count = 10

    try:
        if config_path.is_file():
            data = json.loads(config_path.read_text(encoding="utf-8-sig"))
            if isinstance(data, dict):
                logging_cfg = data.get("logging")
                if isinstance(logging_cfg, dict):
                    raw_level = logging_cfg.get("level")
                    raw_dir = logging_cfg.get("dir")
                    if isinstance(raw_level, str) and raw_level.strip():
                        level_name = raw_level.strip().upper()
                    if isinstance(raw_dir, str) and raw_dir.strip():
                        log_dir_name = raw_dir.strip()
                    rotate_mb = _to_positive_int(logging_cfg.get("rotate_mb"), 10)
                    backup_count = _to_positive_int(logging_cfg.get("backup_count"), 10)
    except Exception as exc:
        _safe_boot_write(f"[BOOT] logging config parse failed: {exc}\n")

    def _candidate_log_dirs(primary: Path) -> list[Path]:
        dirs: list[Path] = [primary]
        runtime_root = _default_runtime_data_dir()
        dirs.append(runtime_root / "logs")
        program_data = str(os.environ.get("PROGRAMDATA", "")).strip()
        if program_data:
            dirs.append(Path(program_data) / "ViorafilmKiosk" / "logs")
        public_root = str(os.environ.get("PUBLIC", "")).strip()
        if public_root:
            dirs.append(Path(public_root) / "Documents" / "ViorafilmKiosk" / "logs")
        temp_root = str(os.environ.get("TEMP", os.getcwd())).strip()
        dirs.append(Path(temp_root) / "ViorafilmKiosk" / "logs")
        dedup: list[Path] = []
        seen: set[str] = set()
        for item in dirs:
            key = str(item).strip().lower()
            if key and key not in seen:
                seen.add(key)
                dedup.append(item)
        return dedup

    log_dir = _resolve_log_dir(log_dir_name)
    selected_log_dir: Optional[Path] = None
    for candidate_dir in _candidate_log_dirs(log_dir):
        if _is_directory_writable(candidate_dir):
            selected_log_dir = candidate_dir
            break
    if selected_log_dir is None:
        selected_log_dir = Path(os.environ.get("TEMP", os.getcwd())) / "ViorafilmKiosk" / "logs"
        try:
            selected_log_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    if str(selected_log_dir).lower() != str(log_dir).lower():
        _safe_boot_write(
            f"[BOOT] log dir fallback ({log_dir}) -> ({selected_log_dir})\n"
        )
    log_dir = selected_log_dir
    log_file = log_dir / f"kiosk_{time.strftime('%Y%m%d')}.log"

    level_value = getattr(logging, level_name, logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    logger = logging.getLogger("kiosk")
    logger.handlers.clear()
    logger.setLevel(level_value)
    logger.propagate = False

    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=rotate_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding="utf-8",
        )
    except Exception as file_exc:
        fallback_done = False
        for candidate_dir in _candidate_log_dirs(_default_runtime_data_dir() / "logs"):
            try:
                candidate_dir.mkdir(parents=True, exist_ok=True)
                candidate_file = candidate_dir / f"kiosk_{time.strftime('%Y%m%d')}.log"
                file_handler = RotatingFileHandler(
                    candidate_file,
                    maxBytes=rotate_mb * 1024 * 1024,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                log_file = candidate_file
                fallback_done = True
                _safe_boot_write(
                    f"[BOOT] log file fallback ({file_exc}) -> ({log_file})\n"
                )
                break
            except Exception:
                continue
        if not fallback_done:
            raise
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    raw_stdout = getattr(sys, "__stdout__", None)
    raw_stderr = getattr(sys, "__stderr__", None)
    logging.raiseExceptions = False

    stdout_writable = _is_writable_stream(raw_stdout)
    stderr_writable = _is_writable_stream(raw_stderr)

    # Avoid unstable GUI stdio streams in frozen(windowed) builds.
    if stdout_writable and not getattr(sys, "frozen", False):
        console_handler = logging.StreamHandler(raw_stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Windowed executable can have None/broken stdio; avoid logging recursion.
    stdout_fallback = raw_stdout if stdout_writable else _NullStream()
    stderr_fallback = raw_stderr if stderr_writable else _NullStream()
    # Always forward print() to file logger so kiosk logs are preserved
    # even when stdout/stderr are unavailable in windowed executables.
    stdout_to_logger = True
    sys.stdout = _LoggerStream(
        logger,
        logging.INFO,
        stdout_fallback,
        forward_to_logger=stdout_to_logger,
    )
    sys.stderr = _LoggerStream(
        logger,
        logging.ERROR,
        stderr_fallback,
        forward_to_logger=False,
    )

    _LOGGING_INITIALIZED = True
    _LOG_FILE_PATH = log_file
    try:
        runtime_data = _default_runtime_data_dir()
        runtime_data.mkdir(parents=True, exist_ok=True)
        marker = runtime_data / "last_log_path.txt"
        marker.write_text(str(log_file), encoding="utf-8")
        try:
            install_marker = INSTALL_ROOT / "last_log_path.txt"
            install_marker.write_text(str(log_file), encoding="utf-8")
        except Exception:
            pass
        try:
            public_root = str(os.environ.get("PUBLIC", "")).strip()
            if public_root:
                public_marker = Path(public_root) / "Documents" / "ViorafilmKiosk" / "last_log_path.txt"
                public_marker.parent.mkdir(parents=True, exist_ok=True)
                public_marker.write_text(str(log_file), encoding="utf-8")
        except Exception:
            pass
        try:
            program_data = str(os.environ.get("PROGRAMDATA", "")).strip()
            if program_data:
                prog_marker = Path(program_data) / "ViorafilmKiosk" / "last_log_path.txt"
                prog_marker.parent.mkdir(parents=True, exist_ok=True)
                prog_marker.write_text(str(log_file), encoding="utf-8")
        except Exception:
            pass
        try:
            temp_marker = Path(os.environ.get("TEMP", os.getcwd())) / "ViorafilmKiosk" / "last_log_path.txt"
            temp_marker.parent.mkdir(parents=True, exist_ok=True)
            temp_marker.write_text(str(log_file), encoding="utf-8")
        except Exception:
            pass
    except Exception:
        pass
    logger.info("[BOOT] logging initialized file=%s level=%s", str(log_file), level_name)
    return log_file

try:
    from PySide6.QtCore import QObject, Qt, QRect, QThread, QTimer, Signal, QBuffer, QByteArray, QIODevice, QUrl
    from PySide6.QtGui import QColor, QIcon, QImage, QIntValidator, QKeyEvent, QMouseEvent, QMovie, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QFormLayout,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QStackedWidget,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    try:
        from PyQt6.QtCore import QObject, Qt, QRect, QThread, QTimer, pyqtSignal as Signal, QBuffer, QByteArray, QIODevice, QUrl
        from PyQt6.QtGui import QColor, QIcon, QImage, QIntValidator, QKeyEvent, QMouseEvent, QMovie, QPainter, QPen, QPixmap
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QDialog,
            QFormLayout,
            QGridLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QScrollArea,
            QSpinBox,
            QStackedWidget,
            QTextEdit,
            QToolButton,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        try:
            from PyQt5.QtCore import QObject, Qt, QRect, QThread, QTimer, pyqtSignal as Signal, QBuffer, QByteArray, QIODevice, QUrl
            from PyQt5.QtGui import QColor, QIcon, QImage, QIntValidator, QKeyEvent, QMouseEvent, QMovie, QPainter, QPen, QPixmap
            from PyQt5.QtWidgets import (
                QApplication,
                QCheckBox,
                QComboBox,
                QDialog,
                QFormLayout,
                QGridLayout,
                QHBoxLayout,
                QLabel,
                QLineEdit,
                QMainWindow,
                QMessageBox,
                QPushButton,
                QScrollArea,
                QSpinBox,
                QStackedWidget,
                QTextEdit,
                QToolButton,
                QVBoxLayout,
                QWidget,
            )
        except ImportError as exc:
            raise SystemExit(
                "Qt bindings are required (PySide6, PyQt6, or PyQt5)."
            ) from exc

try:
    from PySide6.QtMultimedia import QSoundEffect  # type: ignore
except Exception:
    try:
        from PyQt6.QtMultimedia import QSoundEffect  # type: ignore
    except Exception:
        try:
            from PyQt5.QtMultimedia import QSoundEffect  # type: ignore
        except Exception:
            QSoundEffect = None  # type: ignore

from kiosk.print.compose import (
    EXPECTED_SLOT_COUNT_BY_LAYOUT,
    _detect_gray_slot_components,
    compose_print,
    resolve_slots,
)
from kiosk.session import Session, create_session
from kiosk.ui.hotspots import Hotspot, hit_test, load_hotspots
from kiosk.ui.screens.how_many_prints import HowManyPrintsScreen
from kiosk.ui.screens.loading import LoadingScreen
from kiosk.ui.screens.payment_complete import PaymentCompleteScreen
from kiosk.ui.screens.payment_method import PaymentMethodScreen
from kiosk.ui.screens.preview import PreviewScreen
from kiosk.ui.screens.qr_generating import QrGeneratingScreen
from kiosk.ui.screens.status import StaticImageScreen, ThankYouScreen
from kiosk.utils.qr import generate_qr_png

DESIGN_WIDTH = 1920
DESIGN_HEIGHT = 1080

if hasattr(Qt, "Key"):
    KEY_F1 = Qt.Key.Key_F1
    KEY_F2 = Qt.Key.Key_F2
    KEY_F12 = Qt.Key.Key_F12
    KEY_F9 = Qt.Key.Key_F9
    KEY_F5 = Qt.Key.Key_F5
    KEY_R = Qt.Key.Key_R
    KEY_1 = Qt.Key.Key_1
    KEY_2 = Qt.Key.Key_2
    KEY_3 = Qt.Key.Key_3
    KEY_4 = Qt.Key.Key_4
    KEY_5 = Qt.Key.Key_5
    KEY_SPACE = Qt.Key.Key_Space
    KEY_BACKSPACE = Qt.Key.Key_Backspace
    KEY_ENTER = Qt.Key.Key_Enter
    KEY_RETURN = Qt.Key.Key_Return
    KEY_ESCAPE = Qt.Key.Key_Escape
else:
    KEY_F1 = Qt.Key_F1
    KEY_F2 = Qt.Key_F2
    KEY_F12 = Qt.Key_F12
    KEY_F9 = Qt.Key_F9
    KEY_F5 = Qt.Key_F5
    KEY_R = Qt.Key_R
    KEY_1 = Qt.Key_1
    KEY_2 = Qt.Key_2
    KEY_3 = Qt.Key_3
    KEY_4 = Qt.Key_4
    KEY_5 = Qt.Key_5
    KEY_SPACE = Qt.Key_Space
    KEY_BACKSPACE = Qt.Key_Backspace
    KEY_ENTER = Qt.Key_Enter
    KEY_RETURN = Qt.Key_Return
    KEY_ESCAPE = Qt.Key_Escape

if hasattr(Qt, "MouseButton"):
    LEFT_BUTTON = Qt.MouseButton.LeftButton
else:
    LEFT_BUTTON = Qt.LeftButton

if hasattr(Qt, "WidgetAttribute"):
    WA_TRANSPARENT = Qt.WidgetAttribute.WA_TransparentForMouseEvents
    WA_TRANSLUCENT = Qt.WidgetAttribute.WA_TranslucentBackground
else:
    WA_TRANSPARENT = Qt.WA_TransparentForMouseEvents
    WA_TRANSLUCENT = Qt.WA_TranslucentBackground

if hasattr(Qt, "FocusPolicy"):
    STRONG_FOCUS = Qt.FocusPolicy.StrongFocus
else:
    STRONG_FOCUS = Qt.StrongFocus

if hasattr(Qt, "AlignmentFlag"):
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
else:
    ALIGN_CENTER = Qt.AlignCenter

if hasattr(Qt, "AspectRatioMode"):
    KEEP_ASPECT = Qt.AspectRatioMode.KeepAspectRatio
    KEEP_ASPECT_EXPAND = Qt.AspectRatioMode.KeepAspectRatioByExpanding
    IGNORE_ASPECT = Qt.AspectRatioMode.IgnoreAspectRatio
    SMOOTH_TRANSFORM = Qt.TransformationMode.SmoothTransformation
else:
    KEEP_ASPECT = Qt.KeepAspectRatio
    KEEP_ASPECT_EXPAND = Qt.KeepAspectRatioByExpanding
    IGNORE_ASPECT = Qt.IgnoreAspectRatio
    SMOOTH_TRANSFORM = Qt.SmoothTransformation

LAYOUT_KEY_MAP = {
    KEY_1: "2641",
    KEY_2: "6241",
    KEY_3: "4641",
    KEY_4: "4661",
    KEY_5: "4681",
}

DEFAULT_FRAME_LAYOUT_IDS = ["2641", "6241", "4641", "4661", "4681"]

CAPTURE_SLOT_OVERRIDE_BY_LAYOUT = {
    "2641": 8,
    "6241": 9,
    "4641": 10,
    "4661": 9,
    "4681": 10,
}

RIGHT_HOLES = {
    "2641": [
        (1126, 271, 192, 136),
        (1126, 420, 192, 136),
        (1126, 569, 192, 137),
        (1126, 719, 192, 136),
    ],
    # Celebrity mode (2461) uses same slot geometry as 2641 for select_photo.
    "2461": [
        (1126, 271, 192, 136),
        (1126, 420, 192, 136),
        (1126, 569, 192, 137),
        (1126, 719, 192, 136),
    ],
    "4641": [
        (1136, 296, 190, 254),
        (1339, 296, 190, 254),
        (1136, 561, 190, 254),
        (1339, 561, 190, 254),
    ],
    "4661": [
        (1153, 346, 186, 171),
        (1348, 353, 186, 171),
        (1144, 526, 187, 172),
        (1340, 533, 186, 171),
        (1153, 707, 186, 171),
        (1348, 714, 186, 171),
    ],
    "4681": [
        (1126, 275, 192, 136),
        (1324, 275, 192, 136),
        (1126, 416, 192, 137),
        (1324, 416, 192, 137),
        (1126, 558, 192, 136),
        (1324, 558, 192, 136),
        (1126, 699, 192, 137),
        (1324, 699, 192, 137),
    ],
    "6241": [
        (1014, 476, 137, 192),
        (1164, 476, 136, 192),
        (1313, 476, 136, 192),
        (1462, 476, 137, 192),
    ],
}

FRAME_BBOX = {
    "2641": (1113, 258, 1330, 910),
    # Celebrity mode (2461) uses same frame bbox as 2641.
    "2461": (1113, 258, 1330, 910),
    "4641": (1115, 254, 1549, 905),
    "4661": (1123, 265, 1558, 917),
    "4681": (1102, 253, 1536, 905),
    "6241": (1002, 463, 1653, 680),
}

PRINT_QR_ANCHOR_BY_LAYOUT = {
    "2641": "rb",  # right-bottom
    "4641": "lb",  # left-bottom
    "4661": "lt",  # left-top
    "4681": "lb",  # left-bottom
    "6241": "rb",  # right-bottom (avoid overlap with slot area)
    "2461": "rb",
    "2462": "rb",
}

# 2641 users requested a visibly larger QR on print/preview.
PRINT_QR_SIZE_MULTIPLIER_BY_LAYOUT = {
    "2641": 1.3,
}

# Preview should stay smaller than print to avoid visual overlap in design UI.
PREVIEW_QR_RECT_SCALE_BY_LAYOUT = {
    "2641": 1.0,
    "4641": 0.62,
}

# Printer trim-safe margin (2641 was clipping near paper edge).
PRINT_QR_MARGIN_MULTIPLIER_BY_LAYOUT = {
    "2641": 3.0,
}

DEFAULT_ADMIN_SETTINGS = {
    "test_mode": False,
    "camera_backend": "auto",
    "allow_dummy_when_camera_fail": False,
    "countdown_seconds": 3,
    "capture_slots_override": "auto",
    "debug_fullscreen_shutter": False,
    "print_dry_run": True,
    "upload_dry_run": True,
    "qr_enabled": True,
}

DEFAULT_SHARE_SETTINGS = {
    "base_page_url": "https://example.com/s",
    "base_file_url": "https://example.com/s",
    "api_base_url": "https://api.viorafilm.com/api",
    "device_code": "",
    "device_token": "",
    "timeout_sec": 12.0,
}

DEFAULT_PAYMENT_METHODS = {
    "cash": True,
    "card": True,
    "coupon": False,
}

DEFAULT_COUPON_SETTINGS = {
    "enabled": True,
    "length": 6,
    "accept_any_in_test": True,
    "valid_codes": ["123456", "000000"],
}

DEFAULT_GIF_SETTINGS = {
    "enabled": True,
    "frames_per_shot": 3,
    "interval_ms": 200,
    "max_width": 480,
}

DEFAULT_THANK_YOU_SETTINGS = {
    "gif_rect": [1400, 520, 420, 420],
}

BILL_PROFILES = {
    "KR_ONEPLUS_RS232_V1_7": {
        "label": "Korea (ONEPLUS RS-232 v1.7)",
        "baud": 9600,
        "probe_bauds": [9600],
        "default_port": "COM3",
        "parity": "N",
        "bytesize": 8,
        "stopbits": 1,
        "strict_init": True,
        "supports_reset": True,
        "supports_config_bits": True,
        "supports_insert_control": True,
        "recognition_status": [0x05, 0x0B],
        "bill_to_amount": {
            1: 1000,
            5: 5000,
            10: 10000,
        },
        "default_denoms": {
            "1000": True,
            "5000": True,
            "10000": True,
            "50000": False,
        },
    },
    "TP70_RS232_COMPAT": {
        "label": "Overseas (TP70 RS-232 compatible)",
        "baud": 9600,
        "probe_bauds": [9600, 19200],
        "default_port": "COM3",
        "parity": "N",
        "bytesize": 8,
        "stopbits": 1,
        "strict_init": False,
        "supports_reset": True,
        "supports_config_bits": False,
        "supports_insert_control": True,
        "recognition_status": [0x05, 0x0B],
        # 해외 설치 시 운영 통화에 맞게 config.json bill_acceptor.bill_to_amount 값으로 override 가능.
        "bill_to_amount": {
            1: 1000,
            2: 2000,
            5: 5000,
            10: 10000,
            20: 20000,
            50: 50000,
        },
        "default_denoms": {
            "1000": True,
            "5000": True,
            "10000": True,
            "50000": True,
        },
    },
    "TOP_TB_SERIES_RS232_STD": {
        "label": "TOP TB Series (TB74/TB7x RS-232 standard)",
        "baud": 9600,
        "probe_bauds": [9600, 19200, 38400, 57600],
        "probe_parities": ["N", "E", "O"],
        "probe_stopbits": [1, 2],
        "probe_bytesizes": [8, 7],
        "default_port": "AUTO",
        "auto_fallback": True,
        "parity": "N",
        "bytesize": 8,
        "stopbits": 1,
        "strict_init": False,
        "supports_reset": True,
        "supports_config_bits": False,
        "supports_insert_control": True,
        "recognition_status": [0x05, 0x0B],
        "bill_to_amount": {
            1: 1000,
            2: 2000,
            5: 5000,
            10: 10000,
            20: 20000,
            50: 50000,
            100: 100000,
        },
        "default_denoms": {
            "1000": True,
            "5000": True,
            "10000": True,
            "50000": True,
        },
    },
    "TOP_TV74_RS232_STD": {
        "label": "TOP TV74 Series (alias, RS-232 standard)",
        "baud": 9600,
        "probe_bauds": [9600, 19200, 38400, 57600],
        "probe_parities": ["N", "E", "O"],
        "probe_stopbits": [1, 2],
        "probe_bytesizes": [8, 7],
        "default_port": "AUTO",
        "auto_fallback": True,
        "parity": "N",
        "bytesize": 8,
        "stopbits": 1,
        "strict_init": False,
        "supports_reset": True,
        "supports_config_bits": False,
        "supports_insert_control": True,
        "recognition_status": [0x05, 0x0B],
        "bill_to_amount": {
            1: 1000,
            2: 2000,
            5: 5000,
            10: 10000,
            20: 20000,
            50: 50000,
            100: 100000,
        },
        "default_denoms": {
            "1000": True,
            "5000": True,
            "10000": True,
            "50000": True,
        },
    },
}

DEFAULT_BILL_ACCEPTOR_SETTINGS = {
    "enabled": False,
    "profile": "KR_ONEPLUS_RS232_V1_7",
    "port": "AUTO",
    "baud": 9600,
    "denoms": {
        "1000": True,
        "5000": True,
        "10000": True,
        "50000": False,
    },
    "bill_to_amount": {},
}

DEFAULT_PRICING_SETTINGS = {
    "currency_prefix": "KRW",
    "default_price": 4000,
    "layouts": {},
}

DEFAULT_COUPON_VALUE_SETTINGS = {
    "default_coupon_value": 0,
    "values": {},
}

DEFAULT_PRINTING_SETTINGS = {
    "enabled": True,
    "dry_run": False,
    "printers": {
        "DS620": {"win_name": "DP-DS620", "form_4x6": "4x6", "form_2x6": "2x6"},
        # Optional dedicated queue for strip jobs (2x6x2).
        "DS620_STRIP": {"win_name": "", "form_4x6": "4x6", "form_2x6": ""},
        "RX1HS": {"win_name": "DNP RX1HS", "form_4x6": "4x6", "form_2x6": "2x6"},
    },
    "default_model": "DS620",
}

DEFAULT_LAYOUT_SETTINGS = {
    "strip_2x6": ["2462", "2641", "6241"],
}

DEFAULT_MODE_SETTINGS = {
    "celebrity_enabled": True,
    "ai_enabled": False,
}

DEFAULT_CELEBRITY_SETTINGS = {
    "templates_dir": str((ROOT_DIR / "assets" / "celebrity_templates").as_posix()),
    "layout_id": "2461",
}

AI_LAYOUT_ID = "4641"
AI_CAPTURE_SLOTS = 4
AI_SELECT_SLOTS = 2
AI_OUTPUT_SLOTS = 4
AI_CAMERA_OVERLAY_PATH = ROOT_DIR / "assets" / "ui" / "14_ai_mode" / "4641_AImode.png"
# Locked model: Nano Banana 2 tier (Gemini 3.1 Flash image preview).
# Do not allow runtime override to prevent expensive/slow model drift.
CHEAPEST_GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
# 0.5K request budget: downscale source so the longest edge is 512px before API call.
GEMINI_REQUEST_MAX_EDGE = 512

DEFAULT_AI_STYLE_PRESETS: dict[str, dict[str, str]] = {
    "kpop_idol": {
        "label_ko": "KPOP 아이돌",
        "label_en": "KPOP Idol",
        "prompt": "K-pop inspired portrait, clean skin, glossy magazine tone, vibrant but natural colors",
    },
    "caricature": {
        "label_ko": "캐리커처",
        "label_en": "Caricature",
        "prompt": "Stylized caricature portrait with playful exaggeration, clear outlines, colorful shading",
    },
    "anime": {
        "label_ko": "애니메이션",
        "label_en": "Anime",
        "prompt": "Anime portrait style, smooth cel shading, clean lines, high contrast",
    },
    "vintage": {
        "label_ko": "빈티지 필름",
        "label_en": "Vintage Film",
        "prompt": "Vintage film portrait, warm tones, slight grain, nostalgic look",
    },
}
AI_STYLE_PRESETS: dict[str, dict[str, str]] = {
    key: dict(value) for key, value in DEFAULT_AI_STYLE_PRESETS.items()
}

AI_STYLE_PRIMARY_FALLBACK = "kpop_idol"


def _resolve_preferred_ai_style_id(value: object = "") -> str:
    style = str(value or "").strip().lower()
    if style in AI_STYLE_PRESETS:
        return style
    if AI_STYLE_PRIMARY_FALLBACK in AI_STYLE_PRESETS:
        return AI_STYLE_PRIMARY_FALLBACK
    if AI_STYLE_PRESETS:
        return next(iter(AI_STYLE_PRESETS.keys()))
    if AI_STYLE_PRIMARY_FALLBACK in DEFAULT_AI_STYLE_PRESETS:
        return AI_STYLE_PRIMARY_FALLBACK
    if DEFAULT_AI_STYLE_PRESETS:
        return next(iter(DEFAULT_AI_STYLE_PRESETS.keys()))
    return AI_STYLE_PRIMARY_FALLBACK


def _extract_ai_style_id_from_path(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    name = Path(raw).name.lower()
    stem = Path(name).stem.lower()
    known_styles: list[str] = []
    for style_id in list(AI_STYLE_PRESETS.keys()) + list(DEFAULT_AI_STYLE_PRESETS.keys()):
        normalized = str(style_id or "").strip().lower()
        if normalized and normalized not in known_styles:
            known_styles.append(normalized)
    known_styles.sort(key=len, reverse=True)
    for style_id in known_styles:
        if stem == style_id:
            return style_id
        if stem.endswith(f"_{style_id}") or f"_{style_id}_" in stem:
            return style_id
    return ""

DEFAULT_OFFLINE_GRACE_HOURS = 72
DEFAULT_FILM_REMAINING_BY_MODEL = {
    "DS620": 400,
    "RX1HS": 400,
}

_TRANSPARENT_SLOT_CACHE: dict[
    tuple[str, int, int, int],
    tuple[tuple[tuple[int, int, int, int], ...], tuple[int, int]],
] = {}
_USED_SLOT_CACHE: dict[
    tuple[str, str, int, int, int, int],
    tuple[tuple[int, int, int, int], ...],
] = {}
_FRAME_SELECT_BOTTOM_Y_CACHE: dict[tuple[str, str, int, int, int, int], Optional[int]] = {}
_FRAME_SELECT_BOUNDS_CACHE: dict[
    tuple[str, str, int, int, int, int],
    Optional[tuple[int, int, int]],
] = {}


def _event_pos(event: QMouseEvent):
    if hasattr(event, "position"):
        return event.position().toPoint()
    return event.pos()


def ensure_share_dir(session_dir: Path) -> Path:
    share_dir = Path(session_dir) / "share"
    share_dir.mkdir(parents=True, exist_ok=True)
    return share_dir


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp_path, path)


def money_fmt(value: int) -> str:
    try:
        amount = int(value)
    except Exception:
        amount = 0
    return f"{amount:,}"


def format_price(prefix: str, amount: int) -> str:
    value = f"{max(0, int(amount)):,}"
    text_prefix = str(prefix or "").strip()
    if not text_prefix:
        return value
    if any(ch.isalnum() for ch in text_prefix):
        return f"{text_prefix} {value}"
    return f"{text_prefix}{value}"


def _decode_flag_bits(value: int, bits: list[tuple[int, str]]) -> str:
    names = [name for bit, name in bits if int(value) & int(bit)]
    return "|".join(names) if names else "OK"


def _get_printer_status_snapshot(printer_name: str) -> tuple[int, str]:
    try:
        import win32print
    except Exception as exc:
        raise RuntimeError(f"win32print import failed: {exc}") from exc

    handle = win32print.OpenPrinter(str(printer_name))
    try:
        info = win32print.GetPrinter(handle, 2)
        status = int(info.get("Status", 0) or 0)
        status_text = _decode_flag_bits(
            status,
            [
                (int(getattr(win32print, "PRINTER_STATUS_PAUSED", 0)), "PAUSED"),
                (int(getattr(win32print, "PRINTER_STATUS_ERROR", 0)), "ERROR"),
                (int(getattr(win32print, "PRINTER_STATUS_PENDING_DELETION", 0)), "PENDING_DELETION"),
                (int(getattr(win32print, "PRINTER_STATUS_PAPER_JAM", 0)), "PAPER_JAM"),
                (int(getattr(win32print, "PRINTER_STATUS_PAPER_OUT", 0)), "PAPER_OUT"),
                (int(getattr(win32print, "PRINTER_STATUS_OFFLINE", 0)), "OFFLINE"),
                (int(getattr(win32print, "PRINTER_STATUS_BUSY", 0)), "BUSY"),
                (int(getattr(win32print, "PRINTER_STATUS_PRINTING", 0)), "PRINTING"),
                (int(getattr(win32print, "PRINTER_STATUS_NOT_AVAILABLE", 0)), "NOT_AVAILABLE"),
                (int(getattr(win32print, "PRINTER_STATUS_USER_INTERVENTION", 0)), "USER_INTERVENTION"),
                (int(getattr(win32print, "PRINTER_STATUS_DOOR_OPEN", 0)), "DOOR_OPEN"),
            ],
        )
        return status, status_text
    finally:
        win32print.ClosePrinter(handle)


def _wait_spooler_job(printer_name: str, job_id: int, timeout_sec: float = 8.0) -> None:
    try:
        import pywintypes
        import win32print
    except Exception as exc:
        raise RuntimeError(f"pywin32 import failed: {exc}") from exc

    handle = win32print.OpenPrinter(str(printer_name))
    try:
        deadline = time.monotonic() + max(0.5, float(timeout_sec))
        error_mask = (
            int(getattr(win32print, "JOB_STATUS_ERROR", 0))
            | int(getattr(win32print, "JOB_STATUS_OFFLINE", 0))
            | int(getattr(win32print, "JOB_STATUS_PAPEROUT", 0))
            | int(getattr(win32print, "JOB_STATUS_BLOCKED_DEVQ", 0))
            | int(getattr(win32print, "JOB_STATUS_USER_INTERVENTION", 0))
        )
        while time.monotonic() < deadline:
            try:
                info = win32print.GetJob(handle, int(job_id), 1)
            except pywintypes.error as exc:
                if int(getattr(exc, "winerror", 0)) in {87, 1801}:
                    print(f"[PRINT] spooler job_id={job_id} removed from queue")
                    return
                raise

            status = int(info.get("Status", 0) or 0)
            pages_total = int(info.get("TotalPages", 0) or 0)
            pages_printed = int(info.get("PagesPrinted", 0) or 0)
            status_text = _decode_flag_bits(
                status,
                [
                    (int(getattr(win32print, "JOB_STATUS_PAUSED", 0)), "PAUSED"),
                    (int(getattr(win32print, "JOB_STATUS_ERROR", 0)), "ERROR"),
                    (int(getattr(win32print, "JOB_STATUS_DELETING", 0)), "DELETING"),
                    (int(getattr(win32print, "JOB_STATUS_SPOOLING", 0)), "SPOOLING"),
                    (int(getattr(win32print, "JOB_STATUS_PRINTING", 0)), "PRINTING"),
                    (int(getattr(win32print, "JOB_STATUS_OFFLINE", 0)), "OFFLINE"),
                    (int(getattr(win32print, "JOB_STATUS_PAPEROUT", 0)), "PAPER_OUT"),
                    (int(getattr(win32print, "JOB_STATUS_PRINTED", 0)), "PRINTED"),
                    (int(getattr(win32print, "JOB_STATUS_BLOCKED_DEVQ", 0)), "BLOCKED_DEVQ"),
                    (int(getattr(win32print, "JOB_STATUS_USER_INTERVENTION", 0)), "USER_INTERVENTION"),
                ],
            )
            print(
                f"[PRINT] spooler job_id={job_id} status=0x{status:08X} "
                f"({status_text}) pages={pages_printed}/{pages_total}"
            )
            if status & error_mask:
                raise RuntimeError(
                    f"spooler job error status=0x{status:08X} ({status_text})"
                )
            if status & int(getattr(win32print, "JOB_STATUS_PRINTED", 0)):
                return
            time.sleep(0.2)

        print(f"[PRINT] spooler wait timeout job_id={job_id} timeout_sec={timeout_sec:.1f}")
    finally:
        win32print.ClosePrinter(handle)


def _internet_probe_urls(api_base_url: str = "") -> list[str]:
    candidates: list[str] = []
    base_candidates = [
        api_base_url,
        os.environ.get("VIORAFILM_API_BASE_URL", ""),
        DEFAULT_SHARE_SETTINGS.get("api_base_url", ""),
        "https://api.viorafilm.com/api",
    ]
    for raw_base in base_candidates:
        normalized = _normalize_kiosk_api_base_url(raw_base)
        if not normalized:
            continue
        candidates.append(f"{normalized}/health/")
        candidates.append(f"{normalized}/health")
    candidates.append("https://www.msftconnecttest.com/connecttest.txt")

    unique: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        url = str(item or "").strip()
        key = url.lower()
        if not url or key in seen:
            continue
        seen.add(key)
        unique.append(url)
    return unique


def check_internet(timeout: float = 1.0, api_base_url: str = "") -> tuple[bool, str]:
    probe_timeout = max(0.3, float(timeout))
    urls = _internet_probe_urls(api_base_url)
    if requests is not None:
        for url in urls:
            try:
                resp = requests.get(
                    url,
                    timeout=max(0.8, min(3.0, probe_timeout)),
                    allow_redirects=True,
                )
                code = int(resp.status_code)
                if 200 <= code < 500:
                    host = urlsplit(url).netloc or url
                    return True, f"인터넷 연결됨 ({host})"
            except Exception:
                continue

    for host, port in (("1.1.1.1", 53), ("8.8.8.8", 53), ("api.viorafilm.com", 443)):
        try:
            with socket.create_connection((host, int(port)), timeout=max(0.2, probe_timeout)):
                return True, "인터넷 연결됨"
        except Exception:
            continue
    return False, "인터넷 연결 안됨 (네트워크 정책 또는 DNS 차단 가능)"


def _health_log_key(raw_key: str) -> str:
    key = str(raw_key or "").strip()
    if key == "printer_ds620":
        return "printer_DS620"
    if key == "printer_ds620_strip":
        return "printer_DS620_STRIP"
    if key == "printer_rx1hs":
        return "printer_RX1HS"
    return key


def get_printer_health(printer_name: str) -> tuple[bool, str]:
    name = str(printer_name or "").strip()
    if not name:
        return False, "프린터 이름 미설정"

    try:
        import pywintypes
        import win32print
    except Exception as exc:
        return False, f"pywin32 import failed ({exc})"

    try:
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        entries = win32print.EnumPrinters(flags)
        names = {
            str(item[2]).strip()
            for item in entries
            if isinstance(item, (tuple, list)) and len(item) >= 3 and str(item[2]).strip()
        }
        if name not in names:
            return False, "프린터 미등록"
    except Exception as exc:
        return False, f"프린터 목록 조회 실패 ({exc})"

    try:
        handle = win32print.OpenPrinter(name)
    except pywintypes.error:
        return False, "프린터 미등록"
    except Exception as exc:
        return False, f"OpenPrinter failed ({exc})"

    try:
        info = win32print.GetPrinter(handle, 2)
        status = int(info.get("Status", 0) or 0)
        status_text = _decode_flag_bits(
            status,
            [
                (int(getattr(win32print, "PRINTER_STATUS_OFFLINE", 0)), "OFFLINE"),
                (int(getattr(win32print, "PRINTER_STATUS_ERROR", 0)), "ERROR"),
                (int(getattr(win32print, "PRINTER_STATUS_PAPER_OUT", 0)), "PAPER_OUT"),
                (int(getattr(win32print, "PRINTER_STATUS_PAPER_JAM", 0)), "PAPER_JAM"),
                (int(getattr(win32print, "PRINTER_STATUS_DOOR_OPEN", 0)), "DOOR_OPEN"),
                (int(getattr(win32print, "PRINTER_STATUS_USER_INTERVENTION", 0)), "USER_INTERVENTION"),
            ],
        )
        critical_mask = (
            int(getattr(win32print, "PRINTER_STATUS_OFFLINE", 0))
            | int(getattr(win32print, "PRINTER_STATUS_ERROR", 0))
            | int(getattr(win32print, "PRINTER_STATUS_PAPER_OUT", 0))
            | int(getattr(win32print, "PRINTER_STATUS_PAPER_JAM", 0))
            | int(getattr(win32print, "PRINTER_STATUS_DOOR_OPEN", 0))
            | int(getattr(win32print, "PRINTER_STATUS_USER_INTERVENTION", 0))
        )
        ok = (status & critical_mask) == 0
        return ok, f"status=0x{status:08X} ({status_text})"
    except Exception as exc:
        return False, f"GetPrinter failed ({exc})"
    finally:
        try:
            win32print.ClosePrinter(handle)
        except Exception:
            pass


def _bind_edsdk_health_api(sdk) -> None:
    c_void_pp = ctypes.POINTER(ctypes.c_void_p)
    c_uint32_p = ctypes.POINTER(ctypes.c_uint32)
    sdk.EdsGetCameraList.restype = ctypes.c_uint32
    sdk.EdsGetCameraList.argtypes = [c_void_pp]
    sdk.EdsGetChildCount.restype = ctypes.c_uint32
    sdk.EdsGetChildCount.argtypes = [ctypes.c_void_p, c_uint32_p]
    sdk.EdsGetChildAtIndex.restype = ctypes.c_uint32
    sdk.EdsGetChildAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_int32, c_void_pp]
    sdk.EdsOpenSession.restype = ctypes.c_uint32
    sdk.EdsOpenSession.argtypes = [ctypes.c_void_p]
    sdk.EdsCloseSession.restype = ctypes.c_uint32
    sdk.EdsCloseSession.argtypes = [ctypes.c_void_p]
    sdk.EdsRelease.restype = ctypes.c_uint32
    sdk.EdsRelease.argtypes = [ctypes.c_void_p]


def get_camera_health(dll_path: str, backend: str = "auto") -> tuple[bool, str]:
    backend_name = str(backend or "auto").strip().lower()
    if backend_name == "dummy":
        return True, "dummy backend"

    path_text = str(dll_path or "").strip()
    if not path_text:
        return False, "카메라 연결 안됨 (EDSDK DLL 경로 없음)"
    dll_path_obj = Path(path_text)
    if not dll_path_obj.is_file():
        return False, f"카메라 연결 안됨 (EDSDK DLL 없음: {dll_path_obj})"

    camera_list = ctypes.c_void_p()
    camera = ctypes.c_void_p()
    session_opened = False
    sdk = None
    initialized_locally = False
    dll_dir_handle = None
    try:
        # Health check must not change process-wide EDSDK init ownership.
        # If SDK is already initialized by camera runtime, reuse it.
        if _EDS_SDK_INITIALIZED and _EDS_DLL_HANDLE is not None:
            sdk = _EDS_DLL_HANDLE
        else:
            if hasattr(os, "add_dll_directory"):
                dll_dir_handle = os.add_dll_directory(str(dll_path_obj.parent))
            sdk = ctypes.WinDLL(str(dll_path_obj))
            _bind_edsdk_init_api(sdk)
            err_init = sdk.EdsInitializeSDK()
            if err_init != EDS_ERR_OK:
                return False, (
                    "카메라 연결 안됨 "
                    f"(EdsInitializeSDK failed {_hex_err(err_init)} {_describe_eds_error(err_init)})"
                )
            initialized_locally = True

        _bind_edsdk_health_api(sdk)

        err = sdk.EdsGetCameraList(ctypes.byref(camera_list))
        if err != EDS_ERR_OK:
            return False, (
                "카메라 연결 안됨 "
                f"(EdsGetCameraList failed {_hex_err(err)} {_describe_eds_error(err)})"
            )

        count = ctypes.c_uint32(0)
        err = sdk.EdsGetChildCount(camera_list, ctypes.byref(count))
        if err != EDS_ERR_OK:
            return False, (
                "카메라 연결 안됨 "
                f"(EdsGetChildCount failed {_hex_err(err)} {_describe_eds_error(err)})"
            )
        if int(count.value) <= 0:
            return False, "카메라 연결 안됨 (camera not detected)"

        err = sdk.EdsGetChildAtIndex(camera_list, 0, ctypes.byref(camera))
        if err != EDS_ERR_OK:
            return False, (
                "카메라 연결 안됨 "
                f"(EdsGetChildAtIndex failed {_hex_err(err)} {_describe_eds_error(err)})"
            )

        err = sdk.EdsOpenSession(camera)
        if err != EDS_ERR_OK:
            return False, (
                "카메라 연결 안됨 "
                f"(EdsOpenSession failed {_hex_err(err)} {_describe_eds_error(err)})"
            )
        session_opened = True
        return True, f"camera_count={int(count.value)}"
    except Exception as exc:
        return False, f"카메라 연결 안됨 ({exc})"
    finally:
        try:
            if sdk is not None and session_opened and camera:
                sdk.EdsCloseSession(camera)
        except Exception:
            pass
        try:
            if sdk is not None and camera:
                sdk.EdsRelease(camera)
        except Exception:
            pass
        try:
            if sdk is not None and camera_list:
                sdk.EdsRelease(camera_list)
        except Exception:
            pass
        if initialized_locally and sdk is not None:
            try:
                _bind_edsdk_init_api(sdk)
                sdk.EdsTerminateSDK()
            except Exception:
                pass
        if dll_dir_handle is not None:
            try:
                dll_dir_handle.close()
            except Exception:
                pass


def _try_apply_printer_form(printer_name: str, hdc, form_name: str) -> bool:
    import win32con
    import win32print

    def _compact(text: str) -> str:
        return re.sub(r"[^0-9a-z]+", "", str(text or "").lower())

    def _extract_dims(text: str) -> Optional[tuple[str, str]]:
        match = re.search(r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)", str(text or ""))
        if not match:
            return None
        return match.group(1), match.group(2)

    desired = str(form_name or "").strip()
    if not desired:
        return False

    def _apply_devmode_to_dc(devmode_obj: object, reason: str) -> bool:
        # Prefer ResetDC when available; some pywin32 builds expose only CreateDC.
        if hasattr(hdc, "ResetDC"):
            try:
                hdc.ResetDC(devmode_obj)
                return True
            except Exception as exc:
                print(
                    f"[PRINT_FORM] ResetDC failed printer={printer_name} "
                    f"reason={reason} error={exc}"
                )
                return False
        try:
            hdc.DeleteDC()
        except Exception:
            pass
        try:
            hdc.CreateDC("WINSPOOL", str(printer_name), None, devmode_obj)
            print(
                f"[PRINT_FORM] applied via CreateDC printer={printer_name} "
                f"reason={reason}"
            )
            return True
        except Exception as exc:
            print(
                f"[PRINT_FORM] CreateDC failed printer={printer_name} "
                f"reason={reason} error={exc}"
            )
            try:
                hdc.CreatePrinterDC(str(printer_name))
            except Exception:
                pass
            return False

    handle = None
    try:
        handle = win32print.OpenPrinter(str(printer_name))
        info2 = win32print.GetPrinter(handle, 2)
        devmode = info2.get("pDevMode")
        if devmode is None:
            print(f"[PRINT_FORM] missing devmode printer={printer_name}")
            return False

        resolved = ""
        try:
            forms = win32print.EnumForms(handle)
        except Exception:
            forms = []
        form_names: list[str] = []
        if isinstance(forms, list):
            for entry in forms:
                data = entry if isinstance(entry, dict) else {}
                name = str(data.get("Name", "")).strip()
                if name:
                    form_names.append(name)

        if form_names:
            lower_desired = desired.lower()
            desired_compact = _compact(desired)
            desired_dims = _extract_dims(desired)

            # 1) exact match
            for name in form_names:
                if name.lower() == lower_desired:
                    resolved = name
                    break

            # 2) same dimensions (allow swapped orientation: 4x6 == 6x4)
            if not resolved and desired_dims is not None:
                d1, d2 = desired_dims
                for name in form_names:
                    dims = _extract_dims(name)
                    if dims is None:
                        continue
                    n1, n2 = dims
                    if (n1 == d1 and n2 == d2) or (n1 == d2 and n2 == d1):
                        resolved = name
                        break

            # 3) compact contains alias (fallback)
            if not resolved and desired_compact:
                aliases = {desired_compact}
                if "x" in desired.lower():
                    swapped = re.sub(
                        r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)",
                        r"\2x\1",
                        desired.lower(),
                    )
                    aliases.add(_compact(swapped))
                for name in form_names:
                    compact_name = _compact(name)
                    if any(alias and alias in compact_name for alias in aliases):
                        resolved = name
                        break

        if not resolved:
            # Best-effort fallback: force custom 2x6 paper size (in 0.1mm units).
            # This is driver-dependent but can work when named 2x6 form is unavailable.
            if _is_likely_2x6_form_name(desired):
                dm_fields = int(getattr(devmode, "dmFields", getattr(devmode, "Fields", 0)))
                dm_papersize = int(getattr(win32con, "DM_PAPERSIZE", 0x00000002))
                dm_paperlength = int(getattr(win32con, "DM_PAPERLENGTH", 0x00000004))
                dm_paperwidth = int(getattr(win32con, "DM_PAPERWIDTH", 0x00000008))
                new_fields = dm_fields | dm_papersize | dm_paperlength | dm_paperwidth
                if hasattr(devmode, "dmFields"):
                    devmode.dmFields = new_fields
                if hasattr(devmode, "Fields"):
                    devmode.Fields = new_fields
                # DMPAPER_USER(256) + width/length for 2x6 inch (50.8 x 152.4 mm)
                if hasattr(devmode, "dmPaperSize"):
                    devmode.dmPaperSize = 256
                if hasattr(devmode, "PaperSize"):
                    devmode.PaperSize = 256
                if hasattr(devmode, "dmPaperWidth"):
                    devmode.dmPaperWidth = 508
                if hasattr(devmode, "PaperWidth"):
                    devmode.PaperWidth = 508
                if hasattr(devmode, "dmPaperLength"):
                    devmode.dmPaperLength = 1524
                if hasattr(devmode, "PaperLength"):
                    devmode.PaperLength = 1524
                if not _apply_devmode_to_dc(devmode, "custom_2x6"):
                    return False
                print(
                    "[PRINT_FORM] applied custom 2x6 "
                    f"printer={printer_name} desired=\"{desired}\""
                )
                return True

            print(
                f"[PRINT_FORM] not found printer={printer_name} desired=\"{desired}\" "
                f"(will keep driver default)"
            )
            return False

        dm_formname = int(getattr(win32con, "DM_FORMNAME", 0x00010000))
        current_fields = int(
            getattr(devmode, "dmFields", getattr(devmode, "Fields", 0))
        )
        new_fields = current_fields | dm_formname
        # pywin32 DEVMode wrapper can expose either dmFields/dmFormName or Fields/FormName.
        if hasattr(devmode, "dmFields"):
            devmode.dmFields = new_fields
        if hasattr(devmode, "Fields"):
            devmode.Fields = new_fields
        if hasattr(devmode, "dmFormName"):
            devmode.dmFormName = str(resolved)[:31]
        if hasattr(devmode, "FormName"):
            devmode.FormName = str(resolved)[:31]
        if not _apply_devmode_to_dc(devmode, f"named_form:{resolved}"):
            return False
        print(f"[PRINT_FORM] applied form=\"{resolved}\"")
        return True
    except Exception as exc:
        print(f"[PRINT_FORM] apply failed form=\"{desired}\" error={exc}")
        return False
    finally:
        if handle is not None:
            try:
                win32print.ClosePrinter(handle)
            except Exception:
                pass


def win_print_image(
    printer_name: str,
    image_path: str,
    copies: int = 1,
    form_name: str = "",
) -> None:
    import win32con
    import win32print
    import win32ui
    from PIL import ImageWin

    print(
        f"[PRINT] win_print_image enter printer=\"{printer_name}\" "
        f"image={image_path} copies={max(1, int(copies))}"
    )
    path = str(image_path)
    if not Path(path).is_file():
        raise FileNotFoundError(f"image not found: {path}")
    if not str(printer_name).strip():
        raise RuntimeError("printer_name is empty")

    com_initialized = False
    try:
        import pythoncom  # type: ignore

        pythoncom.CoInitialize()
        com_initialized = True
    except Exception:
        com_initialized = False

    hdc = None
    doc_started = False
    job_id: Optional[int] = None

    # Runtime offline checks are executed before worker start.
    # Avoid duplicate OpenPrinter/GetPrinter calls here because some
    # Windows drivers intermittently block in worker threads.
    try:
        print(f"[PRINT] image open start path={path}")
        with Image.open(path) as src:
            img = src.convert("RGB")
        print(f"[PRINT] image open ok size={img.size[0]}x{img.size[1]}")

        print(f"[PRINT] CreatePrinterDC start printer=\"{printer_name}\"")
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(str(printer_name))
        print(f"[PRINT] CreatePrinterDC ok printer=\"{printer_name}\"")
        print(f"[PRINT_FORM] apply start desired=\"{str(form_name or '')}\"")
        _try_apply_printer_form(str(printer_name), hdc, str(form_name or ""))
        print("[PRINT_FORM] apply done")
        pw = int(hdc.GetDeviceCaps(win32con.HORZRES))
        ph = int(hdc.GetDeviceCaps(win32con.VERTRES))
        iw, ih = img.size
        if iw <= 0 or ih <= 0:
            raise RuntimeError("invalid image size")
        if pw <= 0 or ph <= 0:
            raise RuntimeError("invalid printable area")

        dc_landscape = pw >= ph
        image_landscape = iw >= ih
        rotated = False
        if dc_landscape != image_landscape:
            img = img.rotate(90, expand=True)
            iw, ih = img.size
            rotated = True
        print(f"[PRINT_ORIENT] dc={pw}x{ph} img={iw}x{ih} rotate={90 if rotated else 0}")

        scale = min(pw / iw, ph / ih)
        dw, dh = max(1, int(iw * scale)), max(1, int(ih * scale))
        x1 = (pw - dw) // 2
        y1 = (ph - dh) // 2
        x2 = x1 + dw
        y2 = y1 + dh
        print(
            f"[PRINT] form=\"{str(form_name or '')}\" pw={pw} ph={ph} "
            f"img={iw}x{ih} rotated={1 if rotated else 0} scale={scale:.4f}"
        )

        docname = Path(path).name
        print(f"[PRINT] StartDoc begin doc=\"{docname}\"")
        start_result = hdc.StartDoc(docname)
        try:
            parsed = int(start_result)
            if parsed > 0:
                job_id = parsed
                print(f"[PRINT] StartDoc job_id={job_id}")
        except Exception:
            job_id = None
        doc_started = True
        dib = ImageWin.Dib(img)

        for _ in range(max(1, int(copies))):
            print("[PRINT] StartPage")
            hdc.StartPage()
            dib.draw(hdc.GetHandleOutput(), (x1, y1, x2, y2))
            hdc.EndPage()
            print("[PRINT] EndPage")
        print("[PRINT] EndDoc begin")
        hdc.EndDoc()
        print("[PRINT] EndDoc done")
        doc_started = False
        if job_id is not None:
            _wait_spooler_job(str(printer_name), int(job_id), timeout_sec=8.0)
    except Exception:
        if doc_started:
            try:
                hdc.AbortDoc()
            except Exception:
                pass
        raise
    finally:
        if hdc is not None:
            try:
                hdc.DeleteDC()
            except Exception:
                pass
        if com_initialized:
            try:
                import pythoncom  # type: ignore

                pythoncom.CoUninitialize()
            except Exception:
                pass


def _split_print_image_for_2x6(image_path: Path) -> tuple[Path, Path]:
    source_path = Path(image_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"print image missing: {source_path}")

    with Image.open(source_path) as src:
        image = src.convert("RGB")
    w, h = image.size
    if w <= 1 or h <= 1:
        raise RuntimeError(f"invalid split size: {w}x{h}")

    if w >= h:
        cut = max(1, h // 2)
        part_a = image.crop((0, 0, w, cut))
        part_b = image.crop((0, cut, w, h))
    else:
        cut = max(1, w // 2)
        part_a = image.crop((0, 0, cut, h))
        part_b = image.crop((cut, 0, w, h))

    out_dir = source_path.parent
    part_a_path = out_dir / "strip_a.jpg"
    part_b_path = out_dir / "strip_b.jpg"
    part_a.save(part_a_path, format="JPEG", quality=95)
    part_b.save(part_b_path, format="JPEG", quality=95)
    return part_a_path, part_b_path


def _is_likely_2x6_form_name(form_name: str) -> bool:
    text = str(form_name or "").strip().lower()
    if not text:
        return False
    compact = re.sub(r"\s+", "", text)
    explicit_tokens = ("2x6", "6x2", "50x152", "152x50")
    return any(token in compact for token in explicit_tokens)


def normalize_serial_port(port: str) -> str:
    text = str(port).strip()
    if text.upper().startswith("COM"):
        suffix = text[3:]
        if suffix.isdigit() and int(suffix) >= 10:
            return f"\\\\.\\{text.upper()}"
    return text


def _is_auto_serial_port(port: object) -> bool:
    text = str(port or "").strip().upper()
    return text in {"AUTO", "AUTODETECT", "DETECT", "SCAN"}


def _list_serial_port_names() -> list[str]:
    if serial_list_ports is None:
        return []
    ports: list[str] = []
    try:
        for info in serial_list_ports.comports():
            device = str(getattr(info, "device", "")).strip()
            if device:
                ports.append(device)
    except Exception:
        return []
    return sorted(set(ports))


def _packet_byte(value: Any) -> int:
    if isinstance(value, bytes):
        if not value:
            raise ValueError("empty byte value")
        return int(value[0]) & 0xFF
    if isinstance(value, str):
        if not value:
            raise ValueError("empty string value")
        return ord(value[0]) & 0xFF
    return int(value) & 0xFF


def build_packet(b2: Any, b3: Any, b4: Any) -> bytes:
    byte2 = _packet_byte(b2)
    byte3 = _packet_byte(b3)
    byte4 = _packet_byte(b4)
    checksum = (byte2 + byte3 + byte4) & 0xFF
    return bytes((0x24, byte2, byte3, byte4, checksum))


def read_packet(serial_conn: Any, timeout: float = 0.5) -> Optional[tuple[int, int, int]]:
    deadline = time.monotonic() + max(0.05, float(timeout))
    while time.monotonic() < deadline:
        head = serial_conn.read(1)
        if not head:
            continue
        if head[0] != 0x24:
            continue

        payload = bytearray()
        while len(payload) < 4 and time.monotonic() < deadline:
            chunk = serial_conn.read(4 - len(payload))
            if not chunk:
                continue
            payload.extend(chunk)
        if len(payload) < 4:
            return None

        byte2, byte3, byte4, checksum = payload
        if ((byte2 + byte3 + byte4) & 0xFF) != checksum:
            continue
        return int(byte2), int(byte3), int(byte4)
    return None


def send_cmd_with_retry(
    serial_conn: Any,
    cmd: bytes | tuple[Any, Any, Any] | list[Any],
    timeout: float = 0.5,
    retries: int = 3,
    validator=None,
) -> tuple[int, int, int]:
    if isinstance(cmd, bytes):
        if len(cmd) != 5:
            raise ValueError("cmd bytes must be 5-byte packet")
        packet = cmd
    elif isinstance(cmd, (tuple, list)) and len(cmd) == 3:
        packet = build_packet(cmd[0], cmd[1], cmd[2])
    else:
        raise ValueError("cmd must be bytes packet or 3-byte tuple/list")

    last_error = "timeout"
    for attempt in range(1, max(1, int(retries)) + 1):
        try:
            try:
                serial_conn.reset_input_buffer()
            except Exception:
                pass
            serial_conn.write(packet)
            serial_conn.flush()
            response = read_packet(serial_conn, timeout=timeout)
            if response is None:
                last_error = f"timeout attempt={attempt}"
                continue
            if callable(validator) and not validator(response):
                last_error = f"invalid response={response} attempt={attempt}"
                continue
            return response
        except Exception as exc:
            last_error = f"{exc} attempt={attempt}"

    raise TimeoutError(last_error)


def detect_button_bbox(
    main_path: Path,
    selected_path: Path,
    roi: tuple[int, int, int, int] = (0, 250, 1920, 850),
    thr: int = 18,
    pad: int = 16,
) -> Optional[list[int]]:
    if not isinstance(main_path, Path) or not isinstance(selected_path, Path):
        return None
    if (not main_path.is_file()) or (not selected_path.is_file()):
        return None

    try:
        with Image.open(main_path) as main_img_raw:
            main_img = main_img_raw.convert("RGB")
        with Image.open(selected_path) as selected_img_raw:
            selected_img = selected_img_raw.convert("RGB")
    except Exception:
        return None

    if main_img.size != selected_img.size:
        selected_img = selected_img.resize(main_img.size, Image.BILINEAR)

    width, height = main_img.size
    x1 = max(0, min(width, int(roi[0])))
    y1 = max(0, min(height, int(roi[1])))
    x2 = max(0, min(width, int(roi[2])))
    y2 = max(0, min(height, int(roi[3])))
    if x2 <= x1 or y2 <= y1:
        x1, y1, x2, y2 = 0, 0, width, height

    try:
        diff = ImageChops.difference(main_img, selected_img).crop((x1, y1, x2, y2)).convert("L")
        binary = diff.point(lambda p: 255 if p >= int(thr) else 0, mode="L")
        bbox = binary.getbbox()
    except Exception:
        return None

    if not bbox:
        return None

    left = x1 + int(bbox[0])
    top = y1 + int(bbox[1])
    right = x1 + int(bbox[2])
    bottom = y1 + int(bbox[3])

    shrink = max(0, int(pad))
    left += shrink
    top += shrink
    right -= shrink
    bottom -= shrink

    if right <= left or bottom <= top:
        left = x1 + int(bbox[0])
        top = y1 + int(bbox[1])
        right = x1 + int(bbox[2])
        bottom = y1 + int(bbox[3])
        if right <= left or bottom <= top:
            return None

    out_w = right - left
    out_h = bottom - top
    if out_w < 20 or out_h < 20:
        return None
    return [int(left), int(top), int(out_w), int(out_h)]


def detect_qr_placeholder_rect(
    bg_png_path: Path,
    threshold: int = 245,
    min_side: int = 200,
    max_side: int = 900,
) -> tuple[tuple[int, int, int, int], str]:
    fallback_rect = (220, 280, 520, 520)
    if not bg_png_path.is_file():
        return fallback_rect, "fallback"

    try:
        with Image.open(bg_png_path) as source:
            rgb = source.convert("RGB")
        width, height = rgb.size
        if width <= 0 or height <= 0:
            return fallback_rect, "fallback"

        pixels = rgb.load()
        visited = [bytearray(width) for _ in range(height)]
        candidates: list[tuple[int, tuple[int, int, int, int]]] = []

        for y in range(height):
            for x in range(width):
                if visited[y][x]:
                    continue
                visited[y][x] = 1
                r, g, b = pixels[x, y]
                if r < threshold or g < threshold or b < threshold:
                    continue

                queue = deque([(x, y)])
                min_x = max_x = x
                min_y = max_y = y
                touches_border = x == 0 or y == 0 or x == width - 1 or y == height - 1

                while queue:
                    cx, cy = queue.pop()
                    if cx < min_x:
                        min_x = cx
                    if cx > max_x:
                        max_x = cx
                    if cy < min_y:
                        min_y = cy
                    if cy > max_y:
                        max_y = cy
                    if cx == 0 or cy == 0 or cx == width - 1 or cy == height - 1:
                        touches_border = True

                    for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                        if nx < 0 or ny < 0 or nx >= width or ny >= height:
                            continue
                        if visited[ny][nx]:
                            continue
                        visited[ny][nx] = 1
                        nr, ng, nb = pixels[nx, ny]
                        if nr >= threshold and ng >= threshold and nb >= threshold:
                            queue.append((nx, ny))

                if touches_border:
                    continue
                rect_w = max_x - min_x + 1
                rect_h = max_y - min_y + 1
                if rect_w < min_side or rect_h < min_side:
                    continue
                if rect_w > max_side or rect_h > max_side:
                    continue
                ratio = rect_w / float(rect_h)
                if ratio < 0.8 or ratio > 1.2:
                    continue
                area = rect_w * rect_h
                ratio_penalty = int(abs(1.0 - ratio) * 10000)
                score = area - ratio_penalty
                candidates.append((score, (min_x, min_y, rect_w, rect_h)))

        if not candidates:
            return fallback_rect, "fallback"

        _score, rect = max(candidates, key=lambda item: item[0])
        if (width, height) != (DESIGN_WIDTH, DESIGN_HEIGHT):
            sx = DESIGN_WIDTH / float(width)
            sy = DESIGN_HEIGHT / float(height)
            rect = (
                int(round(rect[0] * sx)),
                int(round(rect[1] * sy)),
                max(1, int(round(rect[2] * sx))),
                max(1, int(round(rect[3] * sy))),
            )
        return rect, "detect"
    except Exception as exc:
        print(f"[QR_UI] placeholder detect failed: {exc}")
        return fallback_rect, "fallback"


def _fit_cover_pil(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
    if target_w <= 0 or target_h <= 0:
        raise ValueError("invalid target size")
    source = image.convert("RGB")
    scale = max(target_w / source.width, target_h / source.height)
    resized_w = max(1, int(round(source.width * scale)))
    resized_h = max(1, int(round(source.height * scale)))
    if hasattr(Image, "Resampling"):
        resized = source.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
    else:
        resized = source.resize((resized_w, resized_h), Image.LANCZOS)
    left = max(0, (resized_w - target_w) // 2)
    top = max(0, (resized_h - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def compose_print_with_options(
    frame_png_path: Path,
    photos: list[Path],
    layout_id: str,
    is_gray: bool = False,
    flip_horizontal: bool = False,
) -> Image.Image:
    frame_path = Path(frame_png_path)
    if not frame_path.is_file():
        raise FileNotFoundError(f"Frame PNG not found: {frame_path}")
    if not photos:
        raise ValueError("photos must not be empty")

    normalized_photos = [Path(p) for p in photos]
    if not is_gray and not flip_horizontal:
        return compose_print(frame_path, normalized_photos, layout_id)

    slots, _slot_source = resolve_slots(frame_path, layout_id)
    if not slots:
        return compose_print(frame_path, normalized_photos, layout_id)

    transformed: list[Image.Image] = []
    for photo_path in normalized_photos:
        if not photo_path.is_file():
            raise FileNotFoundError(f"Photo not found: {photo_path}")
        with Image.open(photo_path) as source:
            image = source.convert("RGB")
        if flip_horizontal:
            if hasattr(Image, "Transpose"):
                image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            else:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
        if is_gray:
            image = image.convert("L").convert("RGB")
        transformed.append(image)

    try:
        with Image.open(frame_path) as frame_source:
            frame_rgba = frame_source.convert("RGBA")
        base = Image.new("RGB", frame_rgba.size, (255, 255, 255))
        for idx, (x, y, w, h) in enumerate(slots):
            source = transformed[idx % len(transformed)]
            fitted = _fit_cover_pil(source, w, h)
            base.paste(fitted, (x, y))
        composed = base.convert("RGBA")
        composed.alpha_composite(frame_rgba)
        return composed.convert("RGB")
    finally:
        for image in transformed:
            try:
                image.close()
            except Exception:
                pass


def _detect_transparent_slot_components(
    frame_rgba: Image.Image,
    alpha_threshold: int = 8,
    min_area: int = 400,
) -> list[tuple[tuple[int, int, int, int], int]]:
    width, height = frame_rgba.size
    pixels = frame_rgba.load()
    visited = [bytearray(width) for _ in range(height)]
    components: list[tuple[tuple[int, int, int, int], int]] = []

    for y in range(height):
        for x in range(width):
            if visited[y][x]:
                continue
            visited[y][x] = 1
            _r, _g, _b, a = pixels[x, y]
            if a > alpha_threshold:
                continue

            queue = deque([(x, y)])
            min_x = max_x = x
            min_y = max_y = y
            area = 0
            touches_border = x == 0 or y == 0 or x == width - 1 or y == height - 1

            while queue:
                cx, cy = queue.pop()
                area += 1
                if cx < min_x:
                    min_x = cx
                if cx > max_x:
                    max_x = cx
                if cy < min_y:
                    min_y = cy
                if cy > max_y:
                    max_y = cy
                if cx == 0 or cy == 0 or cx == width - 1 or cy == height - 1:
                    touches_border = True

                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    if visited[ny][nx]:
                        continue
                    visited[ny][nx] = 1
                    _pr, _pg, _pb, pa = pixels[nx, ny]
                    if pa <= alpha_threshold:
                        queue.append((nx, ny))

            if touches_border:
                continue
            if area < min_area:
                continue
            rect = (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
            components.append((rect, area))

    return components


def _sort_rects_yx(rects: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    return sorted(rects, key=lambda r: (r[1], r[0]))


def _pick_slots_by_count(
    components: list[tuple[tuple[int, int, int, int], int]],
    target_count: int,
) -> list[tuple[int, int, int, int]]:
    if target_count <= 0:
        return []
    if not components:
        return []
    selected = sorted(components, key=lambda item: item[1], reverse=True)[:target_count]
    return _sort_rects_yx([rect for rect, _area in selected])


def _scale_slots(
    slots: list[tuple[int, int, int, int]],
    src_size: tuple[int, int],
    dst_size: tuple[int, int],
) -> list[tuple[int, int, int, int]]:
    src_w, src_h = src_size
    dst_w, dst_h = dst_size
    if src_w <= 0 or src_h <= 0:
        return []
    sx = dst_w / float(src_w)
    sy = dst_h / float(src_h)
    scaled: list[tuple[int, int, int, int]] = []
    for x, y, w, h in slots:
        scaled.append(
            (
                int(round(x * sx)),
                int(round(y * sy)),
                max(1, int(round(w * sx))),
                max(1, int(round(h * sy))),
            )
        )
    return _sort_rects_yx(scaled)


def _scale_rect(
    rect: tuple[int, int, int, int],
    src_size: tuple[int, int],
    dst_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    src_w, src_h = src_size
    dst_w, dst_h = dst_size
    if src_w <= 0 or src_h <= 0:
        return rect
    sx = dst_w / float(src_w)
    sy = dst_h / float(src_h)
    x, y, w, h = rect
    return (
        int(round(x * sx)),
        int(round(y * sy)),
        max(1, int(round(w * sx))),
        max(1, int(round(h * sy))),
    )


def _split_slots_into_copies(
    slots: list[tuple[int, int, int, int]],
    photo_count: int,
) -> list[list[tuple[int, int, int, int]]]:
    if photo_count <= 0:
        return []
    ordered = _sort_rects_yx(slots)
    total = len(ordered)
    if total < photo_count:
        return [ordered]
    if total % photo_count != 0:
        return [ordered[:photo_count]]
    copies = total // photo_count
    if copies <= 1:
        return [ordered[:photo_count]]

    if copies == 2:
        centers_x = sorted(((r[0] + r[2] / 2.0, idx) for idx, r in enumerate(ordered)), key=lambda v: v[0])
        best_x_gap = -1.0
        best_x_idx = -1
        for i in range(len(centers_x) - 1):
            gap = centers_x[i + 1][0] - centers_x[i][0]
            if gap > best_x_gap:
                best_x_gap = gap
                best_x_idx = i
        if best_x_idx >= 0:
            left_indices = {idx for _cx, idx in centers_x[: best_x_idx + 1]}
            left = [ordered[i] for i in range(len(ordered)) if i in left_indices]
            right = [ordered[i] for i in range(len(ordered)) if i not in left_indices]
            if len(left) == photo_count and len(right) == photo_count:
                return [_sort_rects_yx(left), _sort_rects_yx(right)]

        centers_y = sorted(((r[1] + r[3] / 2.0, idx) for idx, r in enumerate(ordered)), key=lambda v: v[0])
        best_y_gap = -1.0
        best_y_idx = -1
        for i in range(len(centers_y) - 1):
            gap = centers_y[i + 1][0] - centers_y[i][0]
            if gap > best_y_gap:
                best_y_gap = gap
                best_y_idx = i
        if best_y_idx >= 0:
            top_indices = {idx for _cy, idx in centers_y[: best_y_idx + 1]}
            top = [ordered[i] for i in range(len(ordered)) if i in top_indices]
            bottom = [ordered[i] for i in range(len(ordered)) if i not in top_indices]
            if len(top) == photo_count and len(bottom) == photo_count:
                return [_sort_rects_yx(top), _sort_rects_yx(bottom)]

    groups: list[list[tuple[int, int, int, int]]] = []
    for i in range(copies):
        chunk = ordered[i * photo_count : (i + 1) * photo_count]
        if chunk:
            groups.append(_sort_rects_yx(chunk))
    return groups if groups else [ordered[:photo_count]]


def _resolve_used_slots_for_canvas(
    layout_id: str,
    slot_ref_path: Optional[Path],
    canvas_size: tuple[int, int],
    photo_count: int,
) -> list[tuple[int, int, int, int]]:
    target_count = max(1, int(photo_count or 1))
    path_text = ""
    path_mtime = 0
    if slot_ref_path is not None:
        try:
            path_text = str(slot_ref_path.resolve())
        except Exception:
            path_text = str(slot_ref_path)
        try:
            path_mtime = int(slot_ref_path.stat().st_mtime_ns)
        except Exception:
            path_mtime = 0
    cache_key = (
        str(layout_id or "").strip(),
        path_text,
        int(canvas_size[0]),
        int(canvas_size[1]),
        int(target_count),
        int(path_mtime),
    )
    cached_used = _USED_SLOT_CACHE.get(cache_key)
    if cached_used:
        return [tuple(int(v) for v in rect) for rect in cached_used]

    slots: list[tuple[int, int, int, int]] = []
    ref_size = (0, 0)

    if slot_ref_path is not None and slot_ref_path.is_file():
        slots, ref_size = _detect_transparent_slots(slot_ref_path, min_area=620)
        if not slots:
            try:
                fallback_slots, _slot_source = resolve_slots(slot_ref_path, layout_id)
                with Image.open(slot_ref_path) as fallback_source:
                    ref_size = fallback_source.size
                slots = fallback_slots
            except Exception:
                slots = []

    if not slots:
        return []

    if ref_size != canvas_size and slots:
        slots = _scale_slots(slots, ref_size, canvas_size)
    if slots:
        slots = _normalize_slots_for_layout(layout_id, slots, canvas_size)

    groups = _split_slots_into_copies(slots, target_count)
    if not groups:
        groups = [slots[:target_count]]
    if layout_id in {"6241", "2641", "2461", "2462"}:
        groups = [
            _normalize_group_slot_sizes(group[:target_count], canvas_size)
            for group in groups
        ]

    used: list[tuple[int, int, int, int]] = []
    for group in groups:
        for x, y, w, h in group[:target_count]:
            used.append((int(x), int(y), int(w), int(h)))
    _USED_SLOT_CACHE[cache_key] = tuple(used)
    return used


def _median_int(values: list[int]) -> int:
    if not values:
        return 0
    ordered = sorted(int(v) for v in values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return int(round((ordered[mid - 1] + ordered[mid]) / 2.0))


def _normalize_group_slot_sizes(
    group: list[tuple[int, int, int, int]],
    bounds_size: tuple[int, int],
) -> list[tuple[int, int, int, int]]:
    if not group:
        return []
    frame_w, frame_h = bounds_size
    target_w = max(1, _median_int([r[2] for r in group]))
    target_h = max(1, _median_int([r[3] for r in group]))
    normalized: list[tuple[int, int, int, int]] = []
    for x, y, w, h in group:
        cx = x + (w / 2.0)
        cy = y + (h / 2.0)
        nx = int(round(cx - (target_w / 2.0)))
        ny = int(round(cy - (target_h / 2.0)))
        nx = max(0, min(nx, max(0, frame_w - target_w)))
        ny = max(0, min(ny, max(0, frame_h - target_h)))
        normalized.append((nx, ny, target_w, target_h))
    return _sort_rects_yx(normalized)


def _normalize_slot_sizes_keep_topleft(
    slots: list[tuple[int, int, int, int]],
    bounds_size: tuple[int, int],
) -> list[tuple[int, int, int, int]]:
    if not slots:
        return []
    frame_w, frame_h = bounds_size
    target_w = max(1, _median_int([r[2] for r in slots]))
    target_h = max(1, _median_int([r[3] for r in slots]))
    normalized: list[tuple[int, int, int, int]] = []
    for x, y, _w, _h in slots:
        nx = max(0, min(int(x), max(0, frame_w - target_w)))
        ny = max(0, min(int(y), max(0, frame_h - target_h)))
        normalized.append((nx, ny, target_w, target_h))
    return _sort_rects_yx(normalized)


def _normalize_slots_for_layout(
    layout_id: str,
    slots: list[tuple[int, int, int, int]],
    bounds_size: tuple[int, int],
) -> list[tuple[int, int, int, int]]:
    key = str(layout_id or "").strip()
    if key == "4641" and slots:
        # 4641 can include one malformed transparent hole (typically LT) on some assets.
        # Normalize slot sizes while preserving top-left anchors to keep row alignment stable.
        return _normalize_slot_sizes_keep_topleft(list(slots), bounds_size)
    # Strip-like layouts can contain one outlier transparent hole (notably 6241),
    # so normalize all slot sizes together before copy-group splitting.
    if key in {"6241", "2641", "2461", "2462"} and slots:
        return _normalize_group_slot_sizes(list(slots), bounds_size)
    return _sort_rects_yx(list(slots))


def _rect_intersects(
    a: tuple[int, int, int, int],
    b: tuple[int, int, int, int],
    pad: int = 0,
) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (
        (ax + aw + pad) <= bx
        or (bx + bw + pad) <= ax
        or (ay + ah + pad) <= by
        or (by + bh + pad) <= ay
    )


def _compute_print_qr_rect(
    layout_id: str,
    canvas_size: tuple[int, int],
    occupied_slots: list[tuple[int, int, int, int]],
    anchor_override: Optional[str] = None,
) -> tuple[int, int, int, int]:
    width, height = canvas_size
    width = max(1, int(width))
    height = max(1, int(height))
    layout_key = str(layout_id or "").strip()
    qr_scale = float(PRINT_QR_SIZE_MULTIPLIER_BY_LAYOUT.get(layout_key, 1.0))
    anchor = (
        str(anchor_override).strip().lower()
        if str(anchor_override or "").strip().lower() in {"lt", "rt", "lb", "rb"}
        else PRINT_QR_ANCHOR_BY_LAYOUT.get(layout_key, "rb")
    )

    is_strip_like = layout_key in {"6241", "2641", "2461", "2462"}
    if is_strip_like:
        margin = max(8, int(round(min(width, height) * 0.012)))
        base_size = max(72, int(round(min(width, height) * 0.09)))
        min_size = max(48, int(round(min(width, height) * 0.06)))
    else:
        margin = max(24, int(round(min(width, height) * 0.03)))
        base_size = max(120, int(round(min(width, height) * 0.13)))
        min_size = max(86, int(round(min(width, height) * 0.08)))

    margin_scale = float(PRINT_QR_MARGIN_MULTIPLIER_BY_LAYOUT.get(layout_key, 1.0))
    if margin_scale != 1.0:
        margin = int(round(margin * margin_scale))

    if qr_scale != 1.0:
        base_size = int(round(base_size * qr_scale))
        min_size = int(round(min_size * qr_scale))
        max_qr_side = max(64, int(round(min(width, height) * 0.45)))
        base_size = max(min_size, min(base_size, max_qr_side))
        min_size = max(48, min(min_size, base_size))

    def _anchor_rect(size: int, dx: int, dy: int) -> tuple[int, int, int, int]:
        if anchor == "lt":
            x = margin + dx
            y = margin + dy
        elif anchor == "rt":
            x = width - margin - size - dx
            y = margin + dy
        elif anchor == "lb":
            x = margin + dx
            y = height - margin - size - dy
        else:  # rb
            x = width - margin - size - dx
            y = height - margin - size - dy
        x = max(0, min(int(x), max(0, width - size)))
        y = max(0, min(int(y), max(0, height - size)))
        return (x, y, size, size)

    # Prefer requested corner first, then move inward while avoiding slot overlap.
    for size in range(base_size, min_size - 1, -10):
        for step in (0, 12, 24, 36, 52, 70, 92, 116, 142):
            for dx, dy in ((step, 0), (0, step), (step, step), (step // 2, step)):
                candidate = _anchor_rect(size, dx, dy)
                if any(_rect_intersects(candidate, slot, pad=10) for slot in occupied_slots):
                    continue
                return candidate

    # Last resort: anchored minimum size.
    return _anchor_rect(min_size, 0, 0)


def _scale_rect_about_center(
    rect: tuple[int, int, int, int],
    canvas_size: tuple[int, int],
    scale: float,
) -> tuple[int, int, int, int]:
    x, y, w, h = rect
    cw, ch = canvas_size
    factor = max(0.2, min(2.5, float(scale)))
    nw = max(1, int(round(w * factor)))
    nh = max(1, int(round(h * factor)))
    cx = x + (w / 2.0)
    cy = y + (h / 2.0)
    nx = int(round(cx - (nw / 2.0)))
    ny = int(round(cy - (nh / 2.0)))
    nx = max(0, min(nx, max(0, int(cw) - nw)))
    ny = max(0, min(ny, max(0, int(ch) - nh)))
    return (nx, ny, nw, nh)


def _preview_qr_override_rect(
    layout_id: str,
    canvas_size: tuple[int, int],
) -> Optional[tuple[int, int, int, int]]:
    key = str(layout_id or "").strip()
    w, h = canvas_size
    if key == "2641":
        # Keep preview QR small and docked to right-bottom footer area.
        side = max(40, int(round(min(w, h) * 0.046)))
        right_margin = max(2, int(round(w * 0.004)))
        bottom_margin = max(2, int(round(h * 0.006)))
        x = max(0, w - side - right_margin)
        y = max(0, h - side - bottom_margin)
        return (x, y, side, side)
    return None


def _build_qr_rgb_from_value(qr_value: str) -> Optional[Image.Image]:
    value = str(qr_value or "").strip()
    if not value:
        return None
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(value)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img.convert("RGB")
    except Exception:
        return None


_PREVIEW_DUMMY_QR_IMAGE: Optional[Image.Image] = None


def _build_preview_dummy_qr(size: int = 256) -> Image.Image:
    global _PREVIEW_DUMMY_QR_IMAGE
    target = max(64, int(size))
    if _PREVIEW_DUMMY_QR_IMAGE is not None and _PREVIEW_DUMMY_QR_IMAGE.size == (target, target):
        return _PREVIEW_DUMMY_QR_IMAGE.copy()

    grid = 29
    cell = max(2, target // grid)
    canvas = Image.new("RGB", (grid * cell, grid * cell), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Simple deterministic matrix that visually looks like QR placeholder.
    def _finder(x0: int, y0: int) -> None:
        s = 7
        draw.rectangle((x0 * cell, y0 * cell, (x0 + s) * cell - 1, (y0 + s) * cell - 1), fill=(0, 0, 0))
        draw.rectangle(((x0 + 1) * cell, (y0 + 1) * cell, (x0 + s - 1) * cell - 1, (y0 + s - 1) * cell - 1), fill=(255, 255, 255))
        draw.rectangle(((x0 + 2) * cell, (y0 + 2) * cell, (x0 + s - 2) * cell - 1, (y0 + s - 2) * cell - 1), fill=(0, 0, 0))

    _finder(1, 1)
    _finder(grid - 8, 1)
    _finder(1, grid - 8)

    seed = 0x5A17
    for gy in range(grid):
        for gx in range(grid):
            if (
                (1 <= gx <= 7 and 1 <= gy <= 7)
                or (grid - 8 <= gx <= grid - 2 and 1 <= gy <= 7)
                or (1 <= gx <= 7 and grid - 8 <= gy <= grid - 2)
            ):
                continue
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            if (seed >> 3) & 1:
                draw.rectangle((gx * cell, gy * cell, (gx + 1) * cell - 1, (gy + 1) * cell - 1), fill=(0, 0, 0))

    if canvas.size != (target, target):
        if hasattr(Image, "Resampling"):
            canvas = canvas.resize((target, target), Image.Resampling.NEAREST)
        else:
            canvas = canvas.resize((target, target), Image.NEAREST)
    _PREVIEW_DUMMY_QR_IMAGE = canvas.copy()
    return canvas


def _overlay_qr_on_image(
    image_rgb: Image.Image,
    layout_id: str,
    occupied_slots: list[tuple[int, int, int, int]],
    qr_value: str,
    log_prefix: str = "[QR]",
    use_dummy_qr: bool = False,
    explicit_rect: Optional[tuple[int, int, int, int]] = None,
    qr_rgb_override: Optional[Image.Image] = None,
) -> Image.Image:
    rect = explicit_rect if explicit_rect is not None else _compute_print_qr_rect(layout_id, image_rgb.size, occupied_slots)
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return image_rgb

    if qr_rgb_override is not None:
        qr_rgb = qr_rgb_override.convert("RGB")
        qr_kind = "provided"
    elif use_dummy_qr:
        qr_rgb = _build_preview_dummy_qr(max(w, h))
        qr_kind = "dummy"
    else:
        qr_rgb = _build_qr_rgb_from_value(qr_value)
        if qr_rgb is None:
            return image_rgb
        qr_kind = "real"

    # Keep QR square and centered inside target rect to avoid compressed preview.
    qr_side = max(1, min(int(w), int(h)))
    if hasattr(Image, "Resampling"):
        qr_fit = qr_rgb.resize((qr_side, qr_side), Image.Resampling.NEAREST)
    else:
        qr_fit = qr_rgb.resize((qr_side, qr_side), Image.NEAREST)

    result = image_rgb.copy().convert("RGB")
    draw = ImageDraw.Draw(result)
    draw.rectangle((x, y, x + w, y + h), fill=(255, 255, 255))
    dx = int((w - qr_side) // 2)
    dy = int((h - qr_side) // 2)
    result.paste(qr_fit, (x + dx, y + dy))
    print(
        f"{log_prefix} overlay layout={layout_id} rect=({x},{y},{w},{h}) "
        f"kind={qr_kind} url={qr_value if not use_dummy_qr else 'preview_dummy'}"
    )
    return result


def _overlay_qr_per_copy_groups(
    image_rgb: Image.Image,
    layout_id: str,
    occupied_slots: list[tuple[int, int, int, int]],
    photo_count: int,
    qr_value: str,
    log_prefix: str = "[QR]",
    use_dummy_qr: bool = False,
) -> Image.Image:
    target_count = max(1, int(photo_count or 1))
    if not occupied_slots:
        return _overlay_qr_on_image(
            image_rgb=image_rgb,
            layout_id=layout_id,
            occupied_slots=[],
            qr_value=qr_value,
            log_prefix=log_prefix,
            use_dummy_qr=use_dummy_qr,
        )

    normalized_slots = _normalize_slots_for_layout(layout_id, list(occupied_slots), image_rgb.size)
    groups = _split_slots_into_copies(normalized_slots, target_count)
    if len(groups) <= 1:
        return _overlay_qr_on_image(
            image_rgb=image_rgb,
            layout_id=layout_id,
            occupied_slots=normalized_slots,
            qr_value=qr_value,
            log_prefix=log_prefix,
            use_dummy_qr=use_dummy_qr,
        )

    qr_source: Optional[Image.Image]
    if use_dummy_qr:
        qr_source = _build_preview_dummy_qr(256)
    else:
        qr_source = _build_qr_rgb_from_value(qr_value)
    if qr_source is None:
        return image_rgb

    image_w, image_h = image_rgb.size

    def _group_bbox(rects: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
        min_x = min(r[0] for r in rects)
        min_y = min(r[1] for r in rects)
        max_x = max(r[0] + r[2] for r in rects)
        max_y = max(r[1] + r[3] for r in rects)
        return (int(min_x), int(min_y), int(max_x), int(max_y))

    regions: list[tuple[int, int, int, int]] = []
    if len(groups) == 2 and groups[0] and groups[1]:
        b0 = _group_bbox(groups[0])
        b1 = _group_bbox(groups[1])
        c0x = (b0[0] + b0[2]) / 2.0
        c0y = (b0[1] + b0[3]) / 2.0
        c1x = (b1[0] + b1[2]) / 2.0
        c1y = (b1[1] + b1[3]) / 2.0
        dx = abs(c0x - c1x)
        dy = abs(c0y - c1y)

        if dx >= dy:
            # Side-by-side copies: keep full page height for each region.
            if c0x <= c1x:
                left_idx, right_idx = 0, 1
                left_box, right_box = b0, b1
            else:
                left_idx, right_idx = 1, 0
                left_box, right_box = b1, b0
            split_x = int(round((left_box[2] + right_box[0]) / 2.0))
            split_x = max(1, min(split_x, image_w - 1))
            regions = [(0, 0, image_w, image_h), (0, 0, image_w, image_h)]
            regions[left_idx] = (0, 0, split_x, image_h)
            regions[right_idx] = (split_x, 0, image_w - split_x, image_h)
        else:
            # Top-bottom copies: keep full page width for each region.
            if c0y <= c1y:
                top_idx, bottom_idx = 0, 1
                top_box, bottom_box = b0, b1
            else:
                top_idx, bottom_idx = 1, 0
                top_box, bottom_box = b1, b0
            split_y = int(round((top_box[3] + bottom_box[1]) / 2.0))
            split_y = max(1, min(split_y, image_h - 1))
            regions = [(0, 0, image_w, image_h), (0, 0, image_w, image_h)]
            regions[top_idx] = (0, 0, image_w, split_y)
            regions[bottom_idx] = (0, split_y, image_w, image_h - split_y)
    else:
        for group in groups:
            if not group:
                regions.append((0, 0, image_w, image_h))
                continue
            min_x, min_y, max_x, max_y = _group_bbox(group)
            regions.append((min_x, min_y, max(1, max_x - min_x), max(1, max_y - min_y)))

    result = image_rgb
    for idx, group in enumerate(groups):
        if not group:
            continue
        if idx < len(regions):
            region_x, region_y, region_w, region_h = regions[idx]
        else:
            min_x, min_y, max_x, max_y = _group_bbox(group)
            region_x = min_x
            region_y = min_y
            region_w = max(1, int(max_x - min_x))
            region_h = max(1, int(max_y - min_y))
        local_slots = [
            (int(x - region_x), int(y - region_y), int(w), int(h))
            for x, y, w, h in group
        ]
        local_rect = _compute_print_qr_rect(
            layout_id=layout_id,
            canvas_size=(region_w, region_h),
            occupied_slots=local_slots,
        )
        gx, gy, gw, gh = local_rect
        global_rect = (int(region_x + gx), int(region_y + gy), int(gw), int(gh))
        result = _overlay_qr_on_image(
            image_rgb=result,
            layout_id=layout_id,
            occupied_slots=group,
            qr_value=qr_value,
            log_prefix=(
                f"{log_prefix} copy={idx + 1}/{len(groups)} "
                f"region=({region_x},{region_y},{region_w},{region_h})"
            ),
            use_dummy_qr=use_dummy_qr,
            explicit_rect=global_rect,
            qr_rgb_override=qr_source,
        )
    return result


def _apply_photo_effects(
    source: Image.Image,
    is_gray: bool,
    flip_horizontal: bool,
) -> Image.Image:
    image = source.convert("RGB")
    if flip_horizontal:
        if hasattr(Image, "Transpose"):
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        else:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
    if is_gray:
        image = image.convert("L").convert("RGB")
    return image


def _apply_local_ai_style(source: Image.Image, style_id: str) -> Image.Image:
    style_key = str(style_id or "").strip().lower()
    image = source.convert("RGB")

    if style_key == "kpop_idol":
        image = ImageEnhance.Color(image).enhance(1.22)
        image = ImageEnhance.Brightness(image).enhance(1.08)
        image = ImageEnhance.Contrast(image).enhance(1.12)
        image = image.filter(ImageFilter.SMOOTH_MORE).filter(ImageFilter.SMOOTH_MORE)
        tint = Image.new("RGB", image.size, (255, 228, 238))
        return Image.blend(image, tint, 0.10)

    if style_key == "caricature":
        poster = ImageOps.posterize(image, 3)
        edges = image.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.SMOOTH)
        line_mask = edges.point(lambda p: 255 if p > 70 else 0).convert("1")
        dark_lines = Image.new("RGB", image.size, (15, 15, 15))
        merged = Image.composite(dark_lines, poster, line_mask)
        return ImageEnhance.Contrast(merged).enhance(1.18)

    if style_key == "anime":
        base = ImageOps.posterize(image, 4)
        base = ImageEnhance.Color(base).enhance(1.25)
        base = ImageEnhance.Contrast(base).enhance(1.2)
        line = image.convert("L").filter(ImageFilter.CONTOUR)
        line = line.point(lambda p: 255 if p > 115 else 0).convert("1")
        return Image.composite(Image.new("RGB", image.size, (25, 25, 30)), base, line)

    if style_key == "vintage":
        gray = ImageOps.grayscale(image)
        sepia = ImageOps.colorize(gray, black="#3a2a1e", white="#f5d7a8")
        sepia = ImageEnhance.Contrast(sepia).enhance(0.9)
        sepia = ImageEnhance.Brightness(sepia).enhance(0.98)
        return sepia

    return image


def _extract_image_from_gemini_response(payload: object) -> Optional[Image.Image]:
    if not isinstance(payload, dict):
        return None
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            if not isinstance(part, dict):
                continue
            inline_data = part.get("inlineData") or part.get("inline_data")
            if not isinstance(inline_data, dict):
                continue
            b64 = inline_data.get("data")
            if not isinstance(b64, str) or not b64.strip():
                continue
            try:
                raw = base64.b64decode(b64)
                with Image.open(io.BytesIO(raw)) as parsed:
                    return parsed.convert("RGB")
            except Exception:
                continue
    return None


_AI_API_KEY_CACHE: dict[str, object] = {
    "path": "",
    "mtime_ns": -1,
    "value": "",
}


def _resolve_gemini_api_key() -> str:
    env_key = str(
        os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    ).strip()
    if env_key:
        return env_key

    config_path = _resolve_runtime_config_path()
    path_text = str(config_path)
    try:
        mtime_ns = int(config_path.stat().st_mtime_ns)
    except Exception:
        mtime_ns = -1

    cached_path = str(_AI_API_KEY_CACHE.get("path", ""))
    cached_mtime = int(_AI_API_KEY_CACHE.get("mtime_ns", -1))
    if cached_path == path_text and cached_mtime == mtime_ns:
        return str(_AI_API_KEY_CACHE.get("value", ""))

    key = ""
    try:
        payload: object = {}
        loaded = False
        for enc in ("utf-8", "utf-8-sig", "cp949"):
            try:
                with config_path.open("r", encoding=enc) as fp:
                    payload = json.load(fp)
                loaded = True
                break
            except Exception:
                continue
        if not loaded:
            payload = {}
        if isinstance(payload, dict):
            ai_section = payload.get("ai") if isinstance(payload.get("ai"), dict) else {}
            admin_section = payload.get("admin") if isinstance(payload.get("admin"), dict) else {}
            for candidate in (
                payload.get("gemini_api_key"),
                payload.get("google_api_key"),
                ai_section.get("gemini_api_key"),
                ai_section.get("google_api_key"),
                admin_section.get("gemini_api_key"),
                admin_section.get("google_api_key"),
            ):
                text = str(candidate or "").strip()
                if text:
                    key = text
                    break
    except Exception:
        key = ""

    _AI_API_KEY_CACHE["path"] = path_text
    _AI_API_KEY_CACHE["mtime_ns"] = mtime_ns
    _AI_API_KEY_CACHE["value"] = key
    if key:
        print(f"[AI] gemini api_key loaded from config path={config_path}")
    return key


def _generate_ai_variant_via_gemini(
    source: Image.Image,
    style_id: str,
) -> Optional[Image.Image]:
    api_key = _resolve_gemini_api_key()
    if requests is None:
        print("[AI] gemini disabled: requests unavailable")
        return None
    if not api_key:
        print(
            "[AI] gemini disabled: api_key missing "
            "(set GEMINI_API_KEY/GOOGLE_API_KEY or config gemini_api_key)"
        )
        return None

    style_info = AI_STYLE_PRESETS.get(style_id) or {}
    prompt = str(style_info.get("prompt", "")).strip() or "Stylized portrait"
    model = CHEAPEST_GEMINI_IMAGE_MODEL
    requested_model = str(os.environ.get("GEMINI_IMAGE_MODEL", "")).strip()
    if requested_model and requested_model != model:
        print(f"[AI] model override ignored requested={requested_model} locked={model}")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    # Slow overseas links need longer read windows; keep model fixed and tune only transport timings.
    connect_timeout_sec = 20.0
    read_timeout_sec = 120.0
    retry_count = 2  # total attempts = retry_count + 1
    retry_backoff_sec = 2.0
    try:
        connect_timeout_sec = max(
            5.0,
            float(os.environ.get("KIOSK_AI_GEMINI_CONNECT_TIMEOUT_SEC", str(connect_timeout_sec)) or connect_timeout_sec),
        )
    except Exception:
        pass
    try:
        read_timeout_sec = max(
            30.0,
            float(os.environ.get("KIOSK_AI_GEMINI_READ_TIMEOUT_SEC", str(read_timeout_sec)) or read_timeout_sec),
        )
    except Exception:
        pass
    try:
        retry_count = max(0, int(os.environ.get("KIOSK_AI_GEMINI_RETRY_COUNT", str(retry_count)) or retry_count))
    except Exception:
        pass
    try:
        retry_backoff_sec = max(
            0.0,
            float(os.environ.get("KIOSK_AI_GEMINI_RETRY_BACKOFF_SEC", str(retry_backoff_sec)) or retry_backoff_sec),
        )
    except Exception:
        pass

    try:
        buffer = io.BytesIO()
        send_image = source.convert("RGB")
        max_edge = int(GEMINI_REQUEST_MAX_EDGE)
        if max(send_image.width, send_image.height) > max_edge:
            ratio = float(max_edge) / float(max(send_image.width, send_image.height))
            target_w = max(1, int(round(send_image.width * ratio)))
            target_h = max(1, int(round(send_image.height * ratio)))
            send_image = send_image.resize((target_w, target_h), Image.LANCZOS)
        send_image.save(buffer, format="JPEG", quality=92)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception as exc:
        print(f"[AI] encode failed style={style_id} err={exc}")
        return None

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": encoded}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.35},
    }

    transient_status = {408, 409, 425, 429, 500, 502, 503, 504}
    max_attempts = max(1, retry_count + 1)
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=(connect_timeout_sec, read_timeout_sec),
            )
            if response.status_code >= 400:
                body_text = str(response.text or "").replace("\n", " ").replace("\r", " ").strip()
                if len(body_text) > 240:
                    body_text = f"{body_text[:240]}..."
                can_retry = response.status_code in transient_status and attempt < max_attempts
                print(
                    f"[AI] gemini failed status={response.status_code} style={style_id} "
                    f"attempt={attempt}/{max_attempts} retry={1 if can_retry else 0} "
                    f"body={body_text or '-'}"
                )
                if can_retry:
                    if retry_backoff_sec > 0:
                        time.sleep(retry_backoff_sec * attempt)
                    continue
                return None
            parsed = response.json()
            image = _extract_image_from_gemini_response(parsed)
            if image is None:
                print(
                    f"[AI] gemini no image style={style_id} "
                    f"attempt={attempt}/{max_attempts}"
                )
                return None
            print(
                f"[AI] gemini ok model={model} style={style_id} "
                f"attempt={attempt}/{max_attempts} req={send_image.width}x{send_image.height} "
                f"max_edge={GEMINI_REQUEST_MAX_EDGE} timeout={connect_timeout_sec:.0f}/{read_timeout_sec:.0f}s"
            )
            return image
        except Exception as exc:
            can_retry = attempt < max_attempts
            print(
                f"[AI] gemini exception style={style_id} "
                f"attempt={attempt}/{max_attempts} retry={1 if can_retry else 0} err={exc}"
            )
            if can_retry:
                if retry_backoff_sec > 0:
                    time.sleep(retry_backoff_sec * attempt)
                continue
            return None
    return None


def _generate_ai_variant_image(
    source: Image.Image,
    style_id: str,
    allow_local_fallback: bool = True,
) -> Image.Image:
    remote = _generate_ai_variant_via_gemini(source, style_id)
    if remote is not None:
        return remote
    if allow_local_fallback:
        print(f"[AI] local filter fallback style={style_id}")
        return _apply_local_ai_style(source, style_id)
    raise RuntimeError(f"gemini_required_but_unavailable style={style_id}")


def _design_assets_base_dir(layout_id: Optional[str] = None) -> Path:
    layout_text = str(layout_id or "").strip()
    celebrity_root = ROOT_DIR / "assets" / "ui" / "10_select_Design_celebrity" / "Frame"
    default_root = ROOT_DIR / "assets" / "ui" / "10_select_Design" / "Frame"
    if layout_text == "2461" and celebrity_root.is_dir():
        return celebrity_root
    return default_root


def _resolve_frame_by_index(frame_dir: Path, frame_index: int) -> Optional[Path]:
    if not frame_dir.is_dir():
        return None
    exact = frame_dir / f"{int(frame_index)}.png"
    if exact.is_file():
        return exact
    matched: list[Path] = []
    for path in frame_dir.glob("*.png"):
        stem = path.stem.strip()
        number: Optional[int] = None
        if stem.isdigit():
            number = int(stem)
        else:
            match = re.search(r"\d+", stem)
            if match:
                number = int(match.group(0))
        if number == int(frame_index):
            matched.append(path)
    if matched:
        return sorted(matched, key=lambda p: p.name.lower())[0]
    files = sorted(frame_dir.glob("*.png"), key=lambda p: p.name.lower())
    if files:
        return files[0]
    return None


def resolve_design_asset_paths(layout_id: str, frame_index: int) -> dict[str, Optional[Path]]:
    layout_text = str(layout_id or "").strip()
    frame_num = max(1, int(frame_index or 1))
    frame_root = _design_assets_base_dir(layout_text)

    candidate_layouts = [layout_text]
    # Legacy celebrity alias: if 2461 assets are missing, fallback to 2641 in same root.
    if layout_text == "2461":
        candidate_layouts.append("2641")

    chosen_layout = layout_text
    for cand in candidate_layouts:
        cand_dir = frame_root / "Frame2" / cand
        if cand_dir.is_dir() and any(cand_dir.glob("*.png")):
            chosen_layout = cand
            break

    frame1_dir = frame_root / "Frame1" / chosen_layout
    frame2_dir = frame_root / "Frame2" / chosen_layout
    preview_dir = frame_root / "showing_select_Frame" / chosen_layout

    frame1_path = _resolve_frame_by_index(frame1_dir, frame_num)
    frame2_path = _resolve_frame_by_index(frame2_dir, frame_num)
    preview_frame_path = _resolve_frame_by_index(preview_dir, frame_num)
    slot_ref_path = frame2_dir / "10.png"
    if not slot_ref_path.is_file():
        slot_ref_path = frame2_path

    if frame1_path is None:
        print(f"[DESIGN] missing asset: {frame1_dir / f'{frame_num}.png'}")
    if frame2_path is None:
        print(f"[DESIGN] missing asset: {frame2_dir / f'{frame_num}.png'}")
    if preview_frame_path is None:
        print(f"[DESIGN] missing asset: {preview_dir / f'{frame_num}.png'}")
    if slot_ref_path is None:
        print(f"[DESIGN] missing asset: {frame2_dir / '10.png'}")
    if chosen_layout != layout_text:
        print(
            f"[DESIGN] asset layout fallback requested={layout_text} "
            f"resolved={chosen_layout} root={frame_root}"
        )

    return {
        "frame1_path": frame1_path,
        "frame2_path": frame2_path,
        "preview_frame_path": preview_frame_path,
        "slot_ref_path": slot_ref_path,
    }


def _detect_transparent_slots(
    frame_path: Optional[Path],
    min_area: int,
    area_ratio_threshold: float = 0.22,
) -> tuple[list[tuple[int, int, int, int]], tuple[int, int]]:
    if frame_path is None or not frame_path.is_file():
        return [], (0, 0)
    try:
        resolved_path = str(frame_path.resolve())
    except Exception:
        resolved_path = str(frame_path)
    try:
        mtime_ns = int(frame_path.stat().st_mtime_ns)
    except Exception:
        mtime_ns = 0
    ratio_key = int(round(float(area_ratio_threshold) * 1000))
    cache_key = (resolved_path, int(min_area), ratio_key, mtime_ns)
    cached = _TRANSPARENT_SLOT_CACHE.get(cache_key)
    if cached is not None:
        cached_slots, cached_size = cached
        return [tuple(int(v) for v in rect) for rect in cached_slots], cached_size
    with Image.open(frame_path) as source:
        frame_rgba = source.convert("RGBA")
    components = _detect_transparent_slot_components(
        frame_rgba=frame_rgba,
        min_area=max(1, int(min_area)),
    )
    if not components:
        return [], frame_rgba.size
    max_area = max(area for _rect, area in components)
    threshold = max(min_area, int(max_area * area_ratio_threshold))
    filtered = [rect for rect, area in components if area >= threshold]
    if not filtered:
        filtered = [rect for rect, _area in components]
    result = _sort_rects_yx(filtered)
    _TRANSPARENT_SLOT_CACHE[cache_key] = (tuple(result), frame_rgba.size)
    return result, frame_rgba.size


def _compose_over_template(
    template_rgba: Image.Image,
    slots: list[tuple[int, int, int, int]],
    selected_paths: list[Path],
    is_gray: bool,
    flip_horizontal: bool,
) -> Image.Image:
    if not selected_paths:
        raise ValueError("selected_paths empty")
    base = Image.new("RGB", template_rgba.size, (255, 255, 255))
    for index, (x, y, w, h) in enumerate(slots):
        source_path = selected_paths[index % len(selected_paths)]
        with Image.open(source_path) as source:
            photo = _apply_photo_effects(source, is_gray=is_gray, flip_horizontal=flip_horizontal)
        fitted = _fit_cover_pil(photo, w, h)
        base.paste(fitted, (x, y))
    composed = base.convert("RGBA")
    composed.alpha_composite(template_rgba)
    return composed.convert("RGB")


class HotspotOverlay(QWidget):
    def __init__(self, screen: "ImageScreen") -> None:
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


class ImageScreen(QWidget):
    def __init__(
        self,
        main_window: "KioskMainWindow",
        screen_name: str,
        background_path: Path,
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.screen_name = screen_name
        self.hotspots: list[Hotspot] = []
        self._background = QPixmap(str(background_path))
        self._overlay = HotspotOverlay(self)

        if self._background.isNull():
            print(f"[WARN] Background image not found: {background_path}")

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


class CelebrityTemplateSelectScreen(ImageScreen):
    TITLE_RECT = (0, 62, 1920, 74)
    BACK_RECT = (77, 939, 100, 100)
    PREV_RECT = (118, 942, 120, 90)
    NEXT_RECT = (1682, 942, 120, 90)
    PAGE_RECT = (820, 952, 280, 64)
    CARD_RECTS = [
        (120, 180, 520, 620),
        (700, 180, 520, 620),
        (1280, 180, 520, 620),
    ]
    PREVIEW_INSET = (0, 0, 0, 112)  # left, top, right, bottom

    def __init__(self, main_window: "KioskMainWindow") -> None:
        background_path = ROOT_DIR / "assets" / "ui" / "13_celebrity_template_select" / "main.png"
        if not background_path.is_file():
            background_path = ROOT_DIR / "assets" / "ui" / "3_select_a_frame" / "please_select_a_frame.png"
        super().__init__(
            main_window,
            "celebrity_template_select",
            background_path,
        )
        self.templates: list[dict[str, object]] = []
        self.page_index: int = 0
        self._slot_template_indices: list[Optional[int]] = [None, None, None]

        self._title_label = QLabel("", self)
        self._title_label.setAlignment(ALIGN_CENTER)
        self._title_label.setStyleSheet(
            "QLabel { color: white; font-size: 44px; font-weight: 800; background-color: rgba(0,0,0,115); }"
        )
        self._title_label.setAttribute(WA_TRANSPARENT, True)
        self._title_label.hide()

        self._back_button = QPushButton("◀", self)
        self._back_button.setStyleSheet(
            "QPushButton { background-color: rgba(0,0,0,170); color: white; font-size: 42px; font-weight: 800; "
            "border: 4px solid rgba(255,255,255,180); border-radius: 50px; }"
            "QPushButton:pressed { background-color: rgba(0,0,0,220); }"
        )
        self._back_button.clicked.connect(self._on_back_clicked)
        if hasattr(Qt, "FocusPolicy"):
            self._back_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        else:
            self._back_button.setFocusPolicy(Qt.NoFocus)

        self._prev_button = QPushButton("◀", self)
        self._next_button = QPushButton("▶", self)
        for nav_btn in (self._prev_button, self._next_button):
            nav_btn.setStyleSheet(
                "QPushButton { background-color: rgba(0,0,0,160); color: white; font-size: 42px; font-weight: 800; "
                "border: 2px solid rgba(255,255,255,160); border-radius: 12px; }"
                "QPushButton:pressed { background-color: rgba(0,0,0,210); }"
            )
            if hasattr(Qt, "FocusPolicy"):
                nav_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            else:
                nav_btn.setFocusPolicy(Qt.NoFocus)
        self._prev_button.clicked.connect(lambda: self._change_page(-1))
        self._next_button.clicked.connect(lambda: self._change_page(+1))

        self._page_label = QLabel("page 1 / 1", self)
        self._page_label.setAlignment(ALIGN_CENTER)
        self._page_label.setStyleSheet(
            "QLabel { color: white; font-size: 28px; font-weight: 700; background-color: rgba(0,0,0,120); "
            "border-radius: 8px; }"
        )
        self._page_label.setAttribute(WA_TRANSPARENT, True)
        self._prev_button.hide()
        self._next_button.hide()
        self._page_label.hide()

        self._card_buttons: list[QToolButton] = []
        self._card_name_labels: list[QLabel] = []
        self._card_price_labels: list[QLabel] = []

        for slot in range(3):
            card_btn = QToolButton(self)
            card_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly if hasattr(Qt, "ToolButtonStyle") else Qt.ToolButtonIconOnly)
            card_btn.setStyleSheet(
                "QToolButton { background-color: rgba(0,0,0,120); border: 2px solid rgba(255,255,255,160); "
                "border-radius: 14px; color: white; font-size: 20px; font-weight: 700; }"
                "QToolButton:pressed { background-color: rgba(0,0,0,190); }"
            )
            if hasattr(Qt, "FocusPolicy"):
                card_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            else:
                card_btn.setFocusPolicy(Qt.NoFocus)
            card_btn.clicked.connect(lambda _checked=False, idx=slot: self._on_template_clicked(idx))
            self._card_buttons.append(card_btn)

            name_label = QLabel("", self)
            name_label.setAlignment(ALIGN_CENTER)
            name_label.setStyleSheet(
                "QLabel { color: white; font-size: 28px; font-weight: 800; background-color: rgba(0,0,0,145); "
                "border-radius: 8px; }"
            )
            name_label.setAttribute(WA_TRANSPARENT, True)
            self._card_name_labels.append(name_label)

            price_label = QLabel("", self)
            price_label.setAlignment(ALIGN_CENTER)
            price_label.setStyleSheet(
                "QLabel { color: #FFD34A; font-size: 30px; font-weight: 800; background-color: rgba(0,0,0,165); "
                "border-radius: 8px; }"
            )
            price_label.setAttribute(WA_TRANSPARENT, True)
            self._card_price_labels.append(price_label)

        self._layout_widgets()

    def _total_pages(self) -> int:
        return max(1, int(math.ceil(len(self.templates) / 3.0))) if self.templates else 1

    def _resolve_layout_price(self) -> tuple[str, int, str]:
        celeb_cfg = (
            self.main_window.get_celebrity_settings()
            if hasattr(self.main_window, "get_celebrity_settings")
            else dict(DEFAULT_CELEBRITY_SETTINGS)
        )
        layout_id = str(celeb_cfg.get("layout_id", DEFAULT_CELEBRITY_SETTINGS["layout_id"])).strip() or "2461"
        pricing = (
            self.main_window.get_payment_pricing_settings()
            if hasattr(self.main_window, "get_payment_pricing_settings")
            else dict(DEFAULT_PRICING_SETTINGS)
        )
        prefix = str(pricing.get("currency_prefix", DEFAULT_PRICING_SETTINGS["currency_prefix"]))
        try:
            default_price = max(0, int(pricing.get("default_price", DEFAULT_PRICING_SETTINGS["default_price"])))
        except Exception:
            default_price = int(DEFAULT_PRICING_SETTINGS["default_price"])
        by_layout = pricing.get("layouts") if isinstance(pricing.get("layouts"), dict) else {}
        raw = by_layout.get(layout_id, default_price) if isinstance(by_layout, dict) else default_price
        try:
            amount = max(0, int(raw))
        except Exception:
            amount = default_price
        return format_price(prefix, amount), amount, layout_id

    def _scan_templates(self) -> None:
        celeb_cfg = (
            self.main_window.get_celebrity_settings()
            if hasattr(self.main_window, "get_celebrity_settings")
            else dict(DEFAULT_CELEBRITY_SETTINGS)
        )
        root_text = str(celeb_cfg.get("templates_dir", DEFAULT_CELEBRITY_SETTINGS["templates_dir"])).strip()
        root = Path(root_text)
        found: list[dict[str, object]] = []
        if root.is_dir():
            dirs = sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
            for template_dir in dirs:
                preview_path = template_dir / "preview.png"
                overlays_dir = template_dir / "overlays"
                if not preview_path.is_file():
                    continue
                found.append(
                    {
                        "name": template_dir.name,
                        "dir": template_dir,
                        "preview": preview_path,
                        "overlays": overlays_dir,
                    }
                )
        self.templates = found
        total_pages = self._total_pages()
        if self.page_index >= total_pages:
            self.page_index = max(0, total_pages - 1)
        print(f"[CELEB] templates found N={len(self.templates)}")

    def _layout_widgets(self) -> None:
        self._back_button.setGeometry(self.design_rect_to_widget(self.BACK_RECT))

        for slot, rect in enumerate(self.CARD_RECTS):
            x, y, w, h = rect
            il, it, ir, ib = self.PREVIEW_INSET
            preview_rect = (x + il, y + it, max(1, w - il - ir), max(1, h - it - ib))
            name_rect = (x, y + h - 102, w, 42)
            price_rect = (x, y + h - 56, w, 48)

            button = self._card_buttons[slot]
            button.setGeometry(self.design_rect_to_widget(preview_rect))
            button.setIconSize(button.size())

            self._card_name_labels[slot].setGeometry(self.design_rect_to_widget(name_rect))
            self._card_price_labels[slot].setGeometry(self.design_rect_to_widget(price_rect))

            button.raise_()
            self._card_name_labels[slot].raise_()
            self._card_price_labels[slot].raise_()

    def _render_page(self) -> None:
        total_pages = self._total_pages()
        self.page_index = max(0, min(self.page_index, total_pages - 1))
        page_text = f"page {self.page_index + 1} / {total_pages}"
        self._page_label.setText(page_text)

        price_text, _amount, _layout_id = self._resolve_layout_price()
        start = self.page_index * 3

        for slot in range(3):
            index = start + slot
            self._slot_template_indices[slot] = None
            button = self._card_buttons[slot]
            name_label = self._card_name_labels[slot]
            price_label = self._card_price_labels[slot]

            if index >= len(self.templates):
                button.hide()
                button.setEnabled(False)
                button.setIcon(QIcon())
                button.setText("")
                name_label.hide()
                price_label.hide()
                continue

            item = self.templates[index]
            preview_path = item.get("preview")
            pixmap = QPixmap(str(preview_path)) if isinstance(preview_path, Path) else QPixmap()
            button.setEnabled(True)
            if not pixmap.isNull():
                button.setText("")
                button.setIcon(QIcon(pixmap))
                button.setIconSize(button.size())
            else:
                button.setIcon(QIcon())
                button.setText("미리보기 없음")

            name_label.setText(str(item.get("name", f"template_{index+1}")))
            price_label.setText(price_text)

            self._slot_template_indices[slot] = index
            button.show()
            name_label.show()
            price_label.show()

    def _change_page(self, delta: int) -> None:
        total_pages = self._total_pages()
        if total_pages <= 1:
            return
        self.page_index = max(0, min(self.page_index + int(delta), total_pages - 1))
        self._render_page()

    def _on_back_clicked(self) -> None:
        self.main_window.goto_screen("frame_select")

    def _on_template_clicked(self, slot: int) -> None:
        if slot < 0 or slot >= len(self._slot_template_indices):
            return
        template_index = self._slot_template_indices[slot]
        if template_index is None or template_index < 0 or template_index >= len(self.templates):
            return
        item = self.templates[template_index]
        template_dir = item.get("dir")
        template_name = str(item.get("name", "template"))
        if not isinstance(template_dir, Path):
            return
        self.main_window.apply_celebrity_template_selection(template_dir, template_name)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._scan_templates()
        self._layout_widgets()
        self._render_page()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()
        self._render_page()


class AiStyleSelectScreen(ImageScreen):
    TITLE_RECT = (0, 62, 1920, 74)
    BACK_RECT = (77, 939, 100, 100)
    CARD_RECTS = [
        (260, 230, 620, 250),
        (1040, 230, 620, 250),
        (260, 560, 620, 250),
        (1040, 560, 620, 250),
    ]
    SUBTITLE_RECT = (260, 860, 1400, 90)

    def __init__(self, main_window: "KioskMainWindow") -> None:
        background_path = ROOT_DIR / "assets" / "ui" / "14_ai_mode" / "main.png"
        if not background_path.is_file():
            background_path = ROOT_DIR / "assets" / "ui" / "3_select_a_frame" / "please_select_a_frame.png"
        super().__init__(main_window, "ai_style_select", background_path)
        self._style_ids: list[str] = list(DEFAULT_AI_STYLE_PRESETS.keys())[:4]

        self._title_label = QLabel("", self)
        self._title_label.setAlignment(ALIGN_CENTER)
        self._title_label.setStyleSheet(
            "QLabel { color: white; font-size: 44px; font-weight: 800; background-color: rgba(0,0,0,115); }"
        )
        self._title_label.setAttribute(WA_TRANSPARENT, True)
        self._title_label.hide()

        self._subtitle_label = QLabel("", self)
        self._subtitle_label.setAlignment(ALIGN_CENTER)
        self._subtitle_label.setStyleSheet(
            "QLabel { color: #FFE8A8; font-size: 30px; font-weight: 700; background-color: rgba(0,0,0,135); "
            "border-radius: 10px; }"
        )
        self._subtitle_label.setAttribute(WA_TRANSPARENT, True)
        self._subtitle_label.hide()

        self._back_button = QPushButton("◀", self)
        self._back_button.setStyleSheet(
            "QPushButton { background-color: rgba(0,0,0,170); color: white; font-size: 42px; font-weight: 800; "
            "border: 4px solid rgba(255,255,255,180); border-radius: 50px; }"
            "QPushButton:pressed { background-color: rgba(0,0,0,220); }"
        )
        self._back_button.clicked.connect(self._on_back_clicked)
        if hasattr(Qt, "FocusPolicy"):
            self._back_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        else:
            self._back_button.setFocusPolicy(Qt.NoFocus)

        self._style_buttons: list[QPushButton] = []
        for index in range(4):
            button = QPushButton("", self)
            button.setStyleSheet(
                "QPushButton { background-color: rgba(0,0,0,140); color: white; font-size: 36px; font-weight: 800; "
                "border: 2px solid rgba(255,255,255,170); border-radius: 14px; text-align: center; }"
                "QPushButton:pressed { background-color: rgba(0,0,0,210); }"
            )
            if hasattr(Qt, "FocusPolicy"):
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            else:
                button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(lambda _checked=False, idx=index: self._on_style_clicked_by_index(idx))
            self._style_buttons.append(button)

        self.reload_style_cards()
        self._layout_widgets()

    def _resolved_style_info(self) -> dict[str, dict[str, Any]]:
        if hasattr(self.main_window, "get_ai_style_settings"):
            data = self.main_window.get_ai_style_settings()
            if isinstance(data, dict) and data:
                return data
        return {key: dict(value) for key, value in AI_STYLE_PRESETS.items()}

    def reload_style_cards(self) -> None:
        style_info_map = self._resolved_style_info()
        style_items = list(style_info_map.items())
        enabled_items = [
            (style_id, info if isinstance(info, dict) else {})
            for style_id, info in style_items
            if bool((info if isinstance(info, dict) else {}).get("enabled", True))
        ]
        enabled_items.sort(key=lambda item: (int(item[1].get("order", 9999)), item[0]))
        style_ids = [style_id for style_id, _info in enabled_items]
        if not style_ids:
            style_ids = list(DEFAULT_AI_STYLE_PRESETS.keys())
        self._style_ids = style_ids[:4]

        for index, button in enumerate(self._style_buttons):
            if index >= len(self._style_ids):
                button.hide()
                continue
            style_id = self._style_ids[index]
            info = style_info_map.get(style_id, {})
            ko = str(info.get("label_ko", style_id)).strip() or style_id
            en = str(info.get("label_en", ko)).strip() or ko
            button.setText(f"{ko}\n{en}")
            button.show()

    def _layout_widgets(self) -> None:
        self._back_button.setGeometry(self.design_rect_to_widget(self.BACK_RECT))

        for index, button in enumerate(self._style_buttons):
            if index >= len(self.CARD_RECTS):
                button.hide()
                continue
            if index >= len(self._style_ids):
                button.hide()
                continue
            button.setGeometry(self.design_rect_to_widget(self.CARD_RECTS[index]))
            button.show()
            button.raise_()

    def _play_click_sound(self) -> None:
        try:
            if hasattr(self.main_window, "ui_sound"):
                self.main_window.ui_sound.play("click")
            if hasattr(self.main_window, "_suppress_nav_sound_until"):
                self.main_window._suppress_nav_sound_until = time.monotonic() + 0.35
        except Exception:
            pass

    def _on_back_clicked(self) -> None:
        self._play_click_sound()
        self.main_window.goto_screen("frame_select")

    def _on_style_clicked_by_index(self, index: int) -> None:
        if index < 0 or index >= len(self._style_ids):
            return
        self._play_click_sound()
        style_id = self._style_ids[index]
        self.main_window.apply_ai_style_selection(style_id)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.reload_style_cards()
        self._layout_widgets()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()


class SelectPhotoScreen(ImageScreen):
    AI_ORIGINAL_PANEL_RECT = (120, 205, 520, 730)
    AI_ORIGINAL_GRID_GAP = 18

    def __init__(self, main_window: "KioskMainWindow") -> None:
        self._base_dir = ROOT_DIR / "assets" / "ui" / "9_select_photo"
        super().__init__(main_window, "select_photo", self._base_dir / "main_2641.png")
        self.layout_id: Optional[str] = None
        self.background_path: Optional[Path] = None
        self.captured_paths: list[Path] = []
        self.print_slots: int = 0
        self.left_rects: list[tuple[int, int, int, int]] = []
        self.right_rects: list[tuple[int, int, int, int]] = []
        self.selected_paths: list[Optional[Path]] = []
        self.shot_to_slot: dict[str, int] = {}

        self._slot_cache: dict[str, tuple[list[tuple[int, int, int, int]], list[tuple[int, int, int, int]]]] = {}
        self._left_source_paths: list[Optional[Path]] = []
        self._left_thumb_paths: list[Optional[Path]] = []
        self._left_shot_index_by_key: dict[str, int] = {}
        self._left_labels: list[QLabel] = []
        self._left_buttons: list[QToolButton] = []
        self._right_labels: list[QLabel] = []
        self._right_buttons: list[QToolButton] = []
        self._ai_original_labels: list[QLabel] = []
        self._ai_original_rects: list[tuple[int, int, int, int]] = []
        self._ai_original_paths: list[Optional[Path]] = []
        self._ai_compare_labels: list[QLabel] = []
        self._ai_compare_rects: list[tuple[int, int, int, int]] = []
        self.selected_source_keys: list[Optional[str]] = []
        self._ai_candidate_by_source_key: dict[str, Path] = {}
        self._source_key_by_ai_candidate: dict[str, str] = {}
        self.prepared_bg_path: Optional[Path] = None
        self.prepared_left_rects: list[tuple[int, int, int, int]] = []
        self.prepared_right_rects: list[tuple[int, int, int, int]] = []
        self.prepared_thumb_paths: list[Path] = []

        self._bg_label = QLabel(self)
        self._bg_label.setAlignment(ALIGN_CENTER)
        self._bg_label.setScaledContents(True)
        self._bg_label.setAttribute(WA_TRANSPARENT, True)
        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._hide_notice)
        self._notice_label = QLabel("", self)
        self._notice_label.setAlignment(ALIGN_CENTER)
        self._notice_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0, 0, 0, 180); "
            "font-size: 42px; font-weight: 700; border: 2px solid rgba(255,255,255,150); }"
        )
        self._notice_label.hide()
        self._next_hint_rect = QRect(1920 - 121 - 60, 1080 - 110 - 60, 121, 110)
        self.next_hint_label = QLabel(self)
        self.next_hint_label.setAlignment(ALIGN_CENTER)
        self.next_hint_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        self.next_hint_label.setAttribute(WA_TRANSPARENT, True)
        next_hint_path = self._base_dir / "if_photo_all_selected.png"
        self._next_hint_pixmap = QPixmap(str(next_hint_path))
        if self._next_hint_pixmap.isNull():
            print(f"[SELECT_PHOTO] next hint image missing: {next_hint_path}")
        self._next_hint_visible = False
        self.next_hint_label.hide()

        self.next_hint_btn = QPushButton("", self)
        self.next_hint_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self.next_hint_btn.clicked.connect(self._on_next_hint_clicked)
        self.next_hint_btn.setEnabled(False)
        self.next_hint_btn.hide()
        self.setFocusPolicy(STRONG_FOCUS)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.setFocus()
        self._layout_select_photo_ui()
        self._refresh_views()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_select_photo_ui()
        self._notice_label.setGeometry(self.design_rect_to_widget((450, 430, 1020, 180)))
        self._refresh_views()

    def set_layout(self, layout_id: Optional[str]) -> None:
        self.set_context(
            layout_id,
            [str(p) for p in self.captured_paths],
            self.print_slots,
            prepared={
                "bg_path": str(self.prepared_bg_path) if self.prepared_bg_path else None,
                "left_rects": [list(r) for r in self.prepared_left_rects],
                "right_rects": [list(r) for r in self.prepared_right_rects],
                "thumb_paths": [str(p) for p in self.prepared_thumb_paths],
            },
        )

    def set_context(
        self,
        layout_id: Optional[str],
        captured_paths: list[str],
        print_slots: int,
        prepared: Optional[dict] = None,
    ) -> None:
        resolved_captured = self._resolve_captured_paths(captured_paths)
        prepared_dict = prepared if isinstance(prepared, dict) else {}
        self.prepared_bg_path = self._normalize_prepared_path(prepared_dict.get("bg_path"))
        self.prepared_left_rects = self._normalize_prepared_rects(prepared_dict.get("left_rects"))
        self.prepared_right_rects = self._normalize_prepared_rects(prepared_dict.get("right_rects"))
        self.prepared_thumb_paths = self._normalize_prepared_paths(prepared_dict.get("thumb_paths"))
        if layout_id is None and not resolved_captured and int(print_slots or 0) <= 0:
            self.layout_id = None
            self.background_path = None
            self._background = QPixmap()
            self._bg_label.setPixmap(QPixmap())
            self.captured_paths = []
            self.print_slots = 0
            self.left_rects = []
            self.right_rects = []
            self._left_source_paths = []
            self._left_thumb_paths = []
            self._left_shot_index_by_key = {}
            self.selected_paths = []
            self.selected_source_keys = []
            self.shot_to_slot = {}
            self._ai_candidate_by_source_key = {}
            self._source_key_by_ai_candidate = {}
            self.prepared_bg_path = None
            self.prepared_left_rects = []
            self.prepared_right_rects = []
            self.prepared_thumb_paths = []
            self._clear_slot_widgets()
            self._update_next_hint()
            self.update()
            return

        resolved_print_slots = max(
            1,
            int(print_slots or 0) or EXPECTED_SLOT_COUNT_BY_LAYOUT.get(layout_id or "", 4),
        )
        state_changed = (
            layout_id != self.layout_id
            or resolved_print_slots != self.print_slots
            or resolved_captured != self.captured_paths
        )
        self.layout_id = layout_id
        self.captured_paths = resolved_captured
        self.print_slots = resolved_print_slots
        self._apply_ai_candidate_mapping(prepared_dict, self.captured_paths)

        self._apply_background(layout_id)
        self._rebuild_slot_rects()
        self._rebuild_left_sources()

        if state_changed or len(self.selected_paths) != len(self.right_rects):
            self.selected_paths = [None] * len(self.right_rects)
            self.selected_source_keys = [None] * len(self.right_rects)
            self.shot_to_slot = {}
        else:
            self._reconcile_selection()

        self._rebuild_slot_widgets()
        self._layout_select_photo_ui()
        self._refresh_views()
        first_hole = self.right_rects[0] if self.right_rects else None
        print(
            f"[SELECT_PHOTO] layout={self.layout_id} "
            f"capture={len(self.captured_paths)} print_slots={self.print_slots} "
            f"hole={first_hole} left={len(self.left_rects)} right={len(self.right_rects)}"
        )

    @staticmethod
    def _normalize_prepared_path(value: object) -> Optional[Path]:
        if not isinstance(value, str) or not value.strip():
            return None
        path = Path(value)
        return path if path.is_file() else None

    @staticmethod
    def _normalize_prepared_paths(value: object) -> list[Path]:
        if not isinstance(value, list):
            return []
        paths: list[Path] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                continue
            path = Path(item)
            if path.is_file():
                paths.append(path)
        return paths

    @staticmethod
    def _normalize_prepared_rects(value: object) -> list[tuple[int, int, int, int]]:
        if not isinstance(value, list):
            return []
        rects: list[tuple[int, int, int, int]] = []
        for item in value:
            if not (isinstance(item, (list, tuple)) and len(item) == 4):
                continue
            try:
                x = int(item[0])
                y = int(item[1])
                w = int(item[2])
                h = int(item[3])
            except Exception:
                continue
            if w <= 0 or h <= 0:
                continue
            rects.append((x, y, w, h))
        rects.sort(key=lambda r: (r[1], r[0]))
        return rects

    def _apply_ai_candidate_mapping(
        self,
        prepared_dict: dict,
        resolved_captured: list[Path],
    ) -> None:
        self._ai_candidate_by_source_key = {}
        self._source_key_by_ai_candidate = {}
        if not self._is_ai_mode_4641():
            return

        candidate_paths = self._normalize_prepared_paths(prepared_dict.get("ai_candidate_paths"))
        raw_map = prepared_dict.get("ai_candidate_map")
        if isinstance(raw_map, dict):
            for raw_source, raw_candidate in raw_map.items():
                if not isinstance(raw_source, str) or not raw_source.strip():
                    continue
                if not isinstance(raw_candidate, str) or not raw_candidate.strip():
                    continue
                source_path = Path(raw_source)
                candidate_path = Path(raw_candidate)
                if not source_path.is_file() or not candidate_path.is_file():
                    continue
                source_key = str(source_path)
                self._ai_candidate_by_source_key[source_key] = candidate_path
                self._source_key_by_ai_candidate[str(candidate_path)] = source_key

        if resolved_captured and candidate_paths:
            for idx, source_path in enumerate(resolved_captured):
                if idx >= len(candidate_paths):
                    break
                source_key = str(source_path)
                if source_key in self._ai_candidate_by_source_key:
                    continue
                candidate_path = candidate_paths[idx]
                self._ai_candidate_by_source_key[source_key] = candidate_path
                self._source_key_by_ai_candidate[str(candidate_path)] = source_key

    def _resolve_captured_paths(self, captured_paths: list[str]) -> list[Path]:
        paths = [Path(p) for p in captured_paths if p]
        if not paths:
            session = self.main_window.get_active_session()
            if session is not None:
                if session.shot_paths:
                    paths = [Path(p) for p in session.shot_paths]
                elif session.shots_dir.is_dir():
                    paths = list(session.shots_dir.glob("shot_*.jpg"))

        existing = [p for p in paths if p.is_file()]

        def _shot_key(path: Path) -> tuple[int, str]:
            match = re.search(r"(\d+)", path.stem)
            if match:
                return (int(match.group(1)), path.name.lower())
            return (10_000, path.name.lower())

        return sorted(existing, key=_shot_key)

    def _find_background_path(self, layout_id: Optional[str]) -> Optional[Path]:
        if layout_id:
            exact = self._base_dir / f"main_{layout_id}.png"
            if exact.is_file():
                return exact
            candidates = sorted(
                [p for p in self._base_dir.glob("*.png") if layout_id in p.stem],
                key=lambda p: p.name.lower(),
            )
            if candidates:
                return candidates[0]
        fallback = self._base_dir / "main_2641.png"
        if fallback.is_file():
            return fallback
        any_png = sorted(self._base_dir.glob("*.png"), key=lambda p: p.name.lower())
        if any_png:
            return any_png[0]
        return None

    def _apply_background(self, layout_id: Optional[str]) -> None:
        candidate = self.prepared_bg_path
        if candidate is None:
            candidate = self._find_background_path(layout_id)
        self.background_path = candidate
        if candidate is None:
            self._background = QPixmap()
            self._bg_label.setPixmap(QPixmap())
            print(f"[SELECT_PHOTO] background missing for layout={layout_id}")
            self.update()
            return

        pixmap = QPixmap(str(candidate))
        if pixmap.isNull():
            self._background = QPixmap()
            self._bg_label.setPixmap(QPixmap())
            print(f"[SELECT_PHOTO] failed to load background: {candidate}")
        else:
            self._background = pixmap
            self._bg_label.setPixmap(pixmap)
        self.update()

    @staticmethod
    def _sort_design_rects(rects: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
        return sorted(rects, key=lambda r: (r[1], r[0]))

    @staticmethod
    def _split_rect_groups(
        rects: list[tuple[int, int, int, int]]
    ) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, int, int, int]]]:
        if len(rects) <= 1:
            return rects, []
        rects_by_center = sorted(rects, key=lambda r: (r[0] + r[2] / 2.0, r[1], r[0]))
        centers = [r[0] + r[2] / 2.0 for r in rects_by_center]
        best_gap = -1.0
        split_idx = -1
        for idx in range(len(centers) - 1):
            gap = centers[idx + 1] - centers[idx]
            if gap > best_gap:
                best_gap = gap
                split_idx = idx
        if split_idx < 0:
            midpoint = len(rects_by_center) // 2
            left = rects_by_center[:midpoint]
            right = rects_by_center[midpoint:]
        else:
            left = rects_by_center[: split_idx + 1]
            right = rects_by_center[split_idx + 1 :]
        if not left or not right:
            midpoint = len(rects_by_center) // 2
            left = rects_by_center[:midpoint]
            right = rects_by_center[midpoint:]
        if left and right:
            left_avg_x = sum(r[0] + r[2] / 2.0 for r in left) / len(left)
            right_avg_x = sum(r[0] + r[2] / 2.0 for r in right) / len(right)
            if left_avg_x > right_avg_x:
                left, right = right, left
        return (
            SelectPhotoScreen._sort_design_rects(left),
            SelectPhotoScreen._sort_design_rects(right),
        )

    def _right_holes_for_layout(self, layout_id: Optional[str]) -> list[tuple[int, int, int, int]]:
        if not layout_id:
            return []
        return [tuple(rect) for rect in RIGHT_HOLES.get(layout_id, [])]

    def _is_ai_mode_4641(self) -> bool:
        if str(self.layout_id or "").strip() != AI_LAYOUT_ID:
            return False
        if not hasattr(self.main_window, "is_ai_mode_active"):
            return False
        try:
            return bool(self.main_window.is_ai_mode_active())
        except Exception:
            return False

    @staticmethod
    def _bbox_from_rects(rects: list[tuple[int, int, int, int]]) -> Optional[tuple[int, int, int, int]]:
        if not rects:
            return None
        min_x = min(rect[0] for rect in rects)
        min_y = min(rect[1] for rect in rects)
        max_x = max(rect[0] + rect[2] for rect in rects)
        max_y = max(rect[1] + rect[3] for rect in rects)
        return (min_x, min_y, max_x - min_x, max_y - min_y)

    def _frame_bbox_for_layout(
        self,
        layout_id: Optional[str],
        right_rects: list[tuple[int, int, int, int]],
    ) -> tuple[int, int, int, int]:
        if layout_id and layout_id in FRAME_BBOX:
            bx0, by0, bx1, by1 = FRAME_BBOX[layout_id]
            if bx1 > bx0 and by1 > by0:
                return (bx0, by0, bx1 - bx0, by1 - by0)
            return (bx0, by0, max(1, bx1), max(1, by1))
        bbox = self._bbox_from_rects(right_rects)
        if bbox is not None:
            bx, by, bw, bh = bbox
            return (max(0, bx - 16), max(0, by - 16), bw + 32, bh + 32)
        return (980, 130, 860, 800)

    @staticmethod
    def _left_grid_shape(
        layout_id: Optional[str],
        capture_slots: int,
        hole_w: int,
        hole_h: int,
    ) -> tuple[int, int]:
        if capture_slots <= 0:
            return (0, 0)
        if layout_id in {"2641", "2461"} and capture_slots == 8:
            return (2, 4)
        if capture_slots == 8:
            return (2, 4) if hole_w >= hole_h else (4, 2)
        if capture_slots == 9:
            return (3, 3)
        if capture_slots == 10:
            return (2, 5) if hole_w >= hole_h else (5, 2)
        cols = max(1, min(4, int(math.ceil(math.sqrt(capture_slots)))))
        rows = max(1, int(math.ceil(capture_slots / cols)))
        return (cols, rows)

    def _build_left_grid_rects(
        self,
        layout_id: Optional[str],
        capture_slots: int,
        right_rects: list[tuple[int, int, int, int]],
    ) -> list[tuple[int, int, int, int]]:
        if capture_slots <= 0:
            return []

        if right_rects:
            hole_w = max(1, int(right_rects[0][2]))
            hole_h = max(1, int(right_rects[0][3]))
        else:
            hole_w, hole_h = (192, 136)

        cols, rows = self._left_grid_shape(layout_id, capture_slots, hole_w, hole_h)
        if cols <= 0 or rows <= 0:
            return []

        frame_x, frame_y, frame_w, frame_h = self._frame_bbox_for_layout(layout_id, right_rects)
        gap_x = 16
        gap_y = 16
        grid_width = cols * hole_w + max(0, cols - 1) * gap_x
        grid_height = rows * hole_h + max(0, rows - 1) * gap_y
        grid_right = frame_x - 80
        grid_x0 = grid_right - grid_width
        frame_center_y = frame_y + (frame_h / 2.0)
        grid_y0 = int(round(frame_center_y - (grid_height / 2.0)))

        grid_x0 = max(20, grid_x0)
        grid_y0 = max(20, min(DESIGN_HEIGHT - grid_height - 20, grid_y0))

        rects: list[tuple[int, int, int, int]] = []
        for idx in range(capture_slots):
            row = idx // cols
            col = idx % cols
            x = grid_x0 + col * (hole_w + gap_x)
            y = grid_y0 + row * (hole_h + gap_y)
            rects.append((x, y, hole_w, hole_h))
        return rects

    def _build_ai_original_rects(self) -> list[tuple[int, int, int, int]]:
        panel_x, panel_y, panel_w, panel_h = self.AI_ORIGINAL_PANEL_RECT
        gap = int(self.AI_ORIGINAL_GRID_GAP)
        cols, rows = (2, 2)
        # Keep original preview tiles visually aligned with AI tiles size.
        # If right slots are known, mirror that size; otherwise fallback to panel fit.
        cell_w = max(1, int((panel_w - gap * (cols - 1)) / cols))
        cell_h = max(1, int((panel_h - gap * (rows - 1)) / rows))
        if self.right_rects:
            avg_w = int(round(sum(max(1, int(r[2])) for r in self.right_rects) / len(self.right_rects)))
            avg_h = int(round(sum(max(1, int(r[3])) for r in self.right_rects) / len(self.right_rects)))
            target_w = max(1, avg_w)
            target_h = max(1, avg_h)
            need_w = target_w * cols + gap * (cols - 1)
            need_h = target_h * rows + gap * (rows - 1)
            if need_w > panel_w or need_h > panel_h:
                scale = min(float(panel_w) / float(need_w), float(panel_h) / float(need_h))
                target_w = max(1, int(target_w * scale))
                target_h = max(1, int(target_h * scale))
            cell_w, cell_h = target_w, target_h
        grid_w = cell_w * cols + gap * (cols - 1)
        grid_h = cell_h * rows + gap * (rows - 1)
        start_x = panel_x + max(0, int((panel_w - grid_w) / 2))
        start_y = panel_y + max(0, int((panel_h - grid_h) / 2))
        rects: list[tuple[int, int, int, int]] = []
        for idx in range(4):
            row = idx // cols
            col = idx % cols
            x = start_x + col * (cell_w + gap)
            y = start_y + row * (cell_h + gap)
            rects.append((x, y, cell_w, cell_h))
        return rects

    def _fallback_slot_rects(self, slot_count: int, side: str) -> list[tuple[int, int, int, int]]:
        if slot_count <= 0:
            return []
        if side == "left":
            ax, ay, aw, ah = (80, 120, 780, 820)
            if slot_count == 8:
                cols, rows = 2, 4
            elif slot_count == 9:
                cols, rows = 3, 3
            elif slot_count == 10:
                cols, rows = 2, 5
            else:
                cols = max(1, min(3, int(math.ceil(math.sqrt(slot_count)))))
                rows = max(1, int(math.ceil(slot_count / cols)))
        else:
            ax, ay, aw, ah = (980, 130, 860, 800)
            if slot_count == 4:
                cols, rows = 2, 2
            elif slot_count == 6:
                cols, rows = 2, 3
            elif slot_count == 8:
                cols, rows = 2, 4
            else:
                cols = 2 if slot_count > 1 else 1
                rows = max(1, int(math.ceil(slot_count / cols)))
        gap_x = 20
        gap_y = 16
        cell_w = max(1, int((aw - gap_x * (cols - 1)) / cols))
        cell_h = max(1, int((ah - gap_y * (rows - 1)) / rows))
        rects: list[tuple[int, int, int, int]] = []
        for i in range(slot_count):
            row = i // cols
            col = i % cols
            x = ax + col * (cell_w + gap_x)
            y = ay + row * (cell_h + gap_y)
            rects.append((x, y, cell_w, cell_h))
        return rects

    def _fit_rect_count(
        self,
        rects: list[tuple[int, int, int, int]],
        count: int,
        side: str,
    ) -> list[tuple[int, int, int, int]]:
        if count <= 0:
            return []
        filtered = [r for r in rects if r[2] > 0 and r[3] > 0]
        filtered = self._sort_design_rects(filtered)
        if len(filtered) == count:
            return filtered
        if len(filtered) > count:
            return filtered[:count]
        if not filtered:
            return self._fallback_slot_rects(count, side)
        combined = list(filtered)
        for rect in self._fallback_slot_rects(count, side):
            if len(combined) >= count:
                break
            combined.append(rect)
        return self._sort_design_rects(combined[:count])

    def _detect_rect_groups(
        self,
        expected_left: int,
        expected_right: int,
    ) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, int, int, int]]]:
        if self.background_path is None or not self.background_path.is_file():
            return [], []
        cache_key = str(self.background_path)
        cached = self._slot_cache.get(cache_key)
        if cached is not None:
            left_cached, right_cached = cached
            return list(left_cached), list(right_cached)

        all_rects: list[tuple[int, int, int, int]] = []
        try:
            with Image.open(self.background_path) as source:
                rgba = source.convert("RGBA")
            components = _detect_gray_slot_components(rgba)
            if components:
                components = sorted(components, key=lambda item: item[1], reverse=True)
                max_area = max(area for _rect, area in components)
                cutoff = max(4000, int(max_area * 0.08))
                all_rects = [rect for rect, area in components if area >= cutoff]
                if not all_rects:
                    all_rects = [rect for rect, _area in components[:24]]
        except Exception as exc:
            print(f"[SELECT_PHOTO] slot detect failed: {exc}")

        left_rects: list[tuple[int, int, int, int]] = []
        right_rects: list[tuple[int, int, int, int]] = []
        if all_rects:
            left_rects, right_rects = self._split_rect_groups(all_rects)
            if expected_right > 0 and len(right_rects) < expected_right and len(all_rects) >= expected_right:
                by_center = sorted(all_rects, key=lambda r: (r[0] + r[2] / 2.0, r[1], r[0]))
                right_rects = self._sort_design_rects(by_center[-expected_right:])
                left_rects = self._sort_design_rects(by_center[:-expected_right])
        self._slot_cache[cache_key] = (list(left_rects), list(right_rects))
        return left_rects, right_rects

    def _rebuild_slot_rects(self) -> None:
        expected_left = len(self.captured_paths)
        expected_right = self.print_slots

        table_right = self._right_holes_for_layout(self.layout_id)
        ai_compare_rects: list[tuple[int, int, int, int]] = []
        right_rects: list[tuple[int, int, int, int]] = []
        if table_right:
            sorted_right = self._sort_design_rects(table_right)
            if (
                self._is_ai_mode_4641()
                and expected_right == AI_SELECT_SLOTS
                and len(sorted_right) >= 4
            ):
                # AI 4641: selected AI photos map to RT(first), LB(second).
                right_rects = [sorted_right[1], sorted_right[2]]
                # Comparison original photos map to LT(first), RB(second).
                ai_compare_rects = [sorted_right[0], sorted_right[3]]
            else:
                right_rects = sorted_right
                if expected_right > 0:
                    right_rects = right_rects[:expected_right]
            if len(right_rects) < expected_right:
                fallback_right = self._fallback_slot_rects(expected_right, "right")
                right_rects.extend(fallback_right[len(right_rects) : expected_right])
        else:
            prepared_right = list(self.prepared_right_rects)
            if len(prepared_right) >= expected_right:
                right_rects = self._sort_design_rects(prepared_right[:expected_right])
            else:
                _detected_left, detected_right = self._detect_rect_groups(expected_left, expected_right)
                right_rects = self._fit_rect_count(
                    self._sort_design_rects(prepared_right + detected_right),
                    expected_right,
                    "right",
                )

        self.right_rects = right_rects
        if not self.right_rects and expected_right > 0:
            self.right_rects = self._fallback_slot_rects(expected_right, "right")
        if self._is_ai_mode_4641():
            # AI select screen: force normalized left grid so original shots are
            # rendered with stable, consistent size against right-side AI slots.
            left_rects = self._build_left_grid_rects(self.layout_id, expected_left, self.right_rects)
            if len(left_rects) < expected_left:
                left_rects.extend(self._fallback_slot_rects(expected_left, "left")[len(left_rects) : expected_left])
            left_rects = left_rects[:expected_left]
        else:
            prepared_left = list(self.prepared_left_rects)
            if len(prepared_left) >= expected_left:
                left_rects = self._sort_design_rects(prepared_left[:expected_left])
            else:
                detected_left, _detected_right = self._detect_rect_groups(expected_left, expected_right)
                combined_left = self._sort_design_rects(prepared_left + detected_left)
                if combined_left:
                    left_rects = self._fit_rect_count(combined_left, expected_left, "left")
                else:
                    left_rects = self._build_left_grid_rects(self.layout_id, expected_left, self.right_rects)
                    if len(left_rects) < expected_left:
                        left_rects.extend(self._fallback_slot_rects(expected_left, "left")[len(left_rects) : expected_left])
                    left_rects = left_rects[:expected_left]
        self.left_rects = left_rects
        self._ai_compare_rects = ai_compare_rects if self._is_ai_mode_4641() else []
        self._ai_original_rects = self._build_ai_original_rects() if self._is_ai_mode_4641() else []

    def _rebuild_left_sources(self) -> None:
        self._left_source_paths = []
        self._left_thumb_paths = []
        self._left_shot_index_by_key = {}
        self._ai_original_paths = []
        for index in range(len(self.left_rects)):
            source = self.captured_paths[index] if index < len(self.captured_paths) else None
            thumb = self.prepared_thumb_paths[index] if index < len(self.prepared_thumb_paths) else None
            if thumb is None:
                thumb = source
            if thumb is not None and not thumb.is_file():
                thumb = source
            self._left_source_paths.append(source)
            self._left_thumb_paths.append(thumb)
            if source is not None:
                self._left_shot_index_by_key[str(source)] = index
        if self._is_ai_mode_4641():
            for index in range(len(self._ai_original_rects)):
                source = self.captured_paths[index] if index < len(self.captured_paths) else None
                self._ai_original_paths.append(source)

    def _clear_slot_widgets(self) -> None:
        for widget in self._left_labels:
            widget.deleteLater()
        for widget in self._left_buttons:
            widget.deleteLater()
        for widget in self._right_labels:
            widget.deleteLater()
        for widget in self._right_buttons:
            widget.deleteLater()
        for widget in self._ai_original_labels:
            widget.deleteLater()
        for widget in self._ai_compare_labels:
            widget.deleteLater()
        self._left_labels = []
        self._left_buttons = []
        self._right_labels = []
        self._right_buttons = []
        self._ai_original_labels = []
        self._ai_compare_labels = []

    def _rebuild_slot_widgets(self) -> None:
        self._clear_slot_widgets()
        for index, _rect in enumerate(self.left_rects):
            label = QLabel("", self)
            label.setAlignment(ALIGN_CENTER)
            label.setScaledContents(False)
            label.setAttribute(WA_TRANSPARENT, True)
            button = QToolButton(self)
            button.setStyleSheet("QToolButton { background: transparent; border: 0px; }")
            button.clicked.connect(lambda _checked=False, idx=index: self._on_left_thumb_clicked(idx))
            self._left_labels.append(label)
            self._left_buttons.append(button)

        for index, _rect in enumerate(self.right_rects):
            label = QLabel("", self)
            label.setAlignment(ALIGN_CENTER)
            label.setScaledContents(False)
            label.setAttribute(WA_TRANSPARENT, True)
            button = QToolButton(self)
            button.setStyleSheet("QToolButton { background: transparent; border: 0px; }")
            button.clicked.connect(lambda _checked=False, idx=index: self._on_right_slot_clicked(idx))
            self._right_labels.append(label)
            self._right_buttons.append(button)

        for _idx, _rect in enumerate(self._ai_original_rects):
            label = QLabel("", self)
            label.setAlignment(ALIGN_CENTER)
            label.setScaledContents(False)
            label.setAttribute(WA_TRANSPARENT, True)
            self._ai_original_labels.append(label)

        for _idx, _rect in enumerate(self._ai_compare_rects):
            label = QLabel("", self)
            label.setAlignment(ALIGN_CENTER)
            label.setScaledContents(False)
            label.setAttribute(WA_TRANSPARENT, True)
            self._ai_compare_labels.append(label)

    def _layout_select_photo_ui(self) -> None:
        self._bg_label.setGeometry(self.design_rect_to_widget((0, 0, DESIGN_WIDTH, DESIGN_HEIGHT)))
        self._bg_label.lower()
        for index, rect in enumerate(self._ai_original_rects):
            if index >= len(self._ai_original_labels):
                break
            widget_rect = self.design_rect_to_widget(rect)
            self._ai_original_labels[index].setGeometry(widget_rect)
            self._ai_original_labels[index].raise_()
        for index, rect in enumerate(self.left_rects):
            if index >= len(self._left_labels):
                break
            widget_rect = self.design_rect_to_widget(rect)
            self._left_labels[index].setGeometry(widget_rect)
            self._left_buttons[index].setGeometry(widget_rect)
            self._left_buttons[index].raise_()
        for index, rect in enumerate(self.right_rects):
            if index >= len(self._right_labels):
                break
            widget_rect = self.design_rect_to_widget(rect)
            self._right_labels[index].setGeometry(widget_rect)
            self._right_buttons[index].setGeometry(widget_rect)
            self._right_buttons[index].raise_()
        for index, rect in enumerate(self._ai_compare_rects):
            if index >= len(self._ai_compare_labels):
                break
            widget_rect = self.design_rect_to_widget(rect)
            self._ai_compare_labels[index].setGeometry(widget_rect)
            self._ai_compare_labels[index].raise_()
        hint_rect = self.design_rect_to_widget(
            (
                self._next_hint_rect.x(),
                self._next_hint_rect.y(),
                self._next_hint_rect.width(),
                self._next_hint_rect.height(),
            )
        )
        self.next_hint_label.setGeometry(hint_rect)
        if not self._next_hint_pixmap.isNull():
            scaled = self._next_hint_pixmap.scaled(
                self.next_hint_label.size(),
                KEEP_ASPECT,
                SMOOTH_TRANSFORM,
            )
            self.next_hint_label.setPixmap(scaled)
        self.next_hint_btn.setGeometry(hint_rect)
        self.next_hint_label.raise_()
        self.next_hint_btn.raise_()
        self._notice_label.raise_()
        self._overlay.raise_()

    def _first_empty_slot(self) -> Optional[int]:
        for index, selected in enumerate(self.selected_paths):
            if selected is None:
                return index
        return None

    def _cover_pixmap(self, pixmap: QPixmap, target_size) -> QPixmap:
        if pixmap.isNull() or target_size.width() <= 0 or target_size.height() <= 0:
            return QPixmap()
        scaled = pixmap.scaled(target_size, KEEP_ASPECT_EXPAND, SMOOTH_TRANSFORM)
        sx = max(0, (scaled.width() - target_size.width()) // 2)
        sy = max(0, (scaled.height() - target_size.height()) // 2)
        return scaled.copy(sx, sy, target_size.width(), target_size.height())

    def _set_label_cover(self, label: QLabel, source_path: Optional[Path], empty_text: str) -> None:
        label.setText("")
        label.setPixmap(QPixmap())
        if source_path is not None and source_path.is_file():
            pixmap = QPixmap(str(source_path))
            if not pixmap.isNull():
                covered = self._cover_pixmap(pixmap, label.size())
                if not covered.isNull():
                    label.setPixmap(covered)
                    return
        label.setText(empty_text)

    def _reconcile_selection(self) -> None:
        valid_keys = {str(path) for path in self._left_source_paths if path is not None}
        if len(self.selected_source_keys) != len(self.selected_paths):
            self.selected_source_keys = list(self.selected_source_keys[: len(self.selected_paths)])
            while len(self.selected_source_keys) < len(self.selected_paths):
                self.selected_source_keys.append(None)
        if len(self.selected_paths) != len(self.right_rects):
            self.selected_paths = list(self.selected_paths[: len(self.right_rects)])
            self.selected_source_keys = list(self.selected_source_keys[: len(self.right_rects)])
            while len(self.selected_paths) < len(self.right_rects):
                self.selected_paths.append(None)
            while len(self.selected_source_keys) < len(self.right_rects):
                self.selected_source_keys.append(None)
        next_map: dict[str, int] = {}
        for index, shot_path in enumerate(self.selected_paths):
            if shot_path is None:
                if index < len(self.selected_source_keys):
                    self.selected_source_keys[index] = None
                continue
            source_key = self.selected_source_keys[index] if index < len(self.selected_source_keys) else None
            if source_key is None:
                raw_key = str(shot_path)
                if raw_key in valid_keys:
                    source_key = raw_key
                else:
                    source_key = self._source_key_by_ai_candidate.get(raw_key)
            if source_key is None or source_key not in valid_keys or source_key in next_map:
                self.selected_paths[index] = None
                if index < len(self.selected_source_keys):
                    self.selected_source_keys[index] = None
                continue
            if index < len(self.selected_source_keys):
                self.selected_source_keys[index] = source_key
            next_map[source_key] = index
        self.shot_to_slot = next_map

    def _refresh_left_views(self) -> None:
        for idx, label in enumerate(self._left_labels):
            shot_path = self._left_source_paths[idx] if idx < len(self._left_source_paths) else None
            thumb_path = self._left_thumb_paths[idx] if idx < len(self._left_thumb_paths) else None
            source_for_draw = thumb_path or shot_path
            fallback_text = str(idx + 1) if shot_path is not None else ""
            self._set_label_cover(label, source_for_draw, fallback_text)
            if shot_path is None:
                label.setStyleSheet(
                    "QLabel { color: rgba(255,255,255,120); background-color: rgba(0,0,0,60); "
                    "border: 2px dashed rgba(255,255,255,70); }"
                )
                continue
            shot_key = str(shot_path)
            if shot_key in self.shot_to_slot:
                label.setStyleSheet(
                    "QLabel { color: white; background-color: rgba(0,0,0,30); "
                    "border: 4px solid rgb(96, 240, 96); }"
                )
            else:
                label.setStyleSheet(
                    "QLabel { color: white; background-color: rgba(0,0,0,30); "
                    "border: 2px solid rgba(255,255,255,170); }"
                )

    def _refresh_ai_original_views(self) -> None:
        if not self._is_ai_mode_4641():
            for label in self._ai_original_labels:
                label.hide()
            return
        for idx, label in enumerate(self._ai_original_labels):
            source = self._ai_original_paths[idx] if idx < len(self._ai_original_paths) else None
            self._set_label_cover(label, source, str(idx + 1))
            if source is None:
                label.setStyleSheet(
                    "QLabel { color: rgba(255,255,255,180); background-color: rgba(0,0,0,60); "
                    "border: 2px dashed rgba(255,255,255,120); }"
                )
            else:
                label.setStyleSheet(
                    "QLabel { color: white; background-color: rgba(0,0,0,24); "
                    "border: 2px solid rgba(0,0,0,120); }"
                )
            label.show()

    def _refresh_ai_compare_views(self) -> None:
        if not self._is_ai_mode_4641():
            for label in self._ai_compare_labels:
                label.hide()
            return
        for idx, label in enumerate(self._ai_compare_labels):
            source_path: Optional[Path] = None
            if idx < len(self.selected_source_keys):
                source_key = self.selected_source_keys[idx]
                if source_key:
                    source = Path(source_key)
                    if source.is_file():
                        source_path = source
            self._set_label_cover(label, source_path, str(idx + 1))
            if source_path is None:
                label.setStyleSheet(
                    "QLabel { color: rgba(0,0,0,220); background-color: rgba(255,255,255,65); "
                    "border: 2px dashed rgba(0,0,0,140); }"
                )
            else:
                label.setStyleSheet(
                    "QLabel { color: white; background-color: rgba(0,0,0,24); "
                    "border: 3px solid rgb(255, 214, 64); }"
                )
            label.show()

    def _refresh_right_views(self) -> None:
        for idx, label in enumerate(self._right_labels):
            label.setText("")
            label.setPixmap(QPixmap())
            selected = self.selected_paths[idx] if idx < len(self.selected_paths) else None
            if selected is None:
                self._set_label_cover(label, None, str(idx + 1))
                label.setStyleSheet(
                    "QLabel { color: rgba(255,255,255,200); background-color: rgba(0,0,0,120); "
                    "border: 2px dashed rgba(255,255,255,160); }"
                )
                continue
            self._set_label_cover(label, selected, str(idx + 1))
            label.setStyleSheet(
                "QLabel { color: white; background-color: rgba(0,0,0,40); "
                "border: 3px solid rgb(255, 214, 64); }"
            )

    def _refresh_views(self) -> None:
        self._refresh_ai_original_views()
        self._refresh_left_views()
        self._refresh_ai_compare_views()
        self._refresh_right_views()
        self._update_next_hint()

    def _is_all_selected(self) -> bool:
        if not self.selected_paths:
            return False
        return all(path is not None for path in self.selected_paths)

    def _update_next_hint(self) -> None:
        complete = self._is_all_selected()
        if complete:
            self.next_hint_label.show()
            self.next_hint_btn.setEnabled(True)
            self.next_hint_btn.show()
            if not self._next_hint_visible:
                print("[SELECT_PHOTO] all_selected=1 -> show NEXT")
            self._next_hint_visible = True
        else:
            self.next_hint_label.hide()
            self.next_hint_btn.setEnabled(False)
            self.next_hint_btn.hide()
            if self._next_hint_visible:
                print("[SELECT_PHOTO] all_selected=0 -> hide NEXT")
            self._next_hint_visible = False

    def _on_next_hint_clicked(self) -> None:
        if not self._is_all_selected():
            return
        print("[SELECT_PHOTO] NEXT clicked")
        self.main_window._continue_from_select_photo()

    def _on_left_thumb_clicked(self, index: int) -> None:
        if index < 0 or index >= len(self._left_source_paths):
            return
        shot_path = self._left_source_paths[index]
        if shot_path is None:
            return
        shot_name = shot_path.name
        shot_key = str(shot_path)
        if shot_key in self.shot_to_slot:
            slot = self.shot_to_slot.pop(shot_key)
            if 0 <= slot < len(self.selected_paths):
                self.selected_paths[slot] = None
                if slot < len(self.selected_source_keys):
                    self.selected_source_keys[slot] = None
            print(f"[SELECT_PHOTO] unselect shot={shot_name} from slot={slot + 1}")
            self._refresh_views()
            return

        slot = self._first_empty_slot()
        if slot is None:
            print("[SELECT_PHOTO] blocked: slots full")
            self.show_notice("슬롯이 가득 찼습니다", duration_ms=800)
            return
        selected_path = self._ai_candidate_by_source_key.get(shot_key, shot_path)
        self.selected_paths[slot] = selected_path
        if slot >= len(self.selected_source_keys):
            self.selected_source_keys.extend([None] * (slot - len(self.selected_source_keys) + 1))
        self.selected_source_keys[slot] = shot_key
        self.shot_to_slot[shot_key] = slot
        if selected_path != shot_path:
            print(
                f"[SELECT_PHOTO] select shot={shot_name} -> slot={slot + 1} "
                f"mapped_ai={selected_path.name}"
            )
        else:
            print(f"[SELECT_PHOTO] select shot={shot_name} -> slot={slot + 1}")
        self._refresh_views()

    def _on_right_slot_clicked(self, slot: int) -> None:
        if slot < 0 or slot >= len(self.selected_paths):
            return
        shot_path = self.selected_paths[slot]
        if shot_path is None:
            return
        shot_name = shot_path.name
        source_key = self.selected_source_keys[slot] if slot < len(self.selected_source_keys) else None
        self.selected_paths[slot] = None
        if slot < len(self.selected_source_keys):
            self.selected_source_keys[slot] = None
        if source_key:
            self.shot_to_slot.pop(source_key, None)
        else:
            self.shot_to_slot.pop(str(shot_path), None)
        print(f"[SELECT_PHOTO] cancel slot={slot + 1} shot={shot_name}")
        self._refresh_views()

    def clear_active_slot(self) -> None:
        for slot in range(len(self.selected_paths) - 1, -1, -1):
            if self.selected_paths[slot] is not None:
                self._on_right_slot_clicked(slot)
                return

    def get_selected_paths(self) -> list[Optional[Path]]:
        return list(self.selected_paths)

    def get_selected_source_paths(self) -> list[Optional[Path]]:
        sources: list[Optional[Path]] = []
        for idx, selected in enumerate(self.selected_paths):
            source_key = self.selected_source_keys[idx] if idx < len(self.selected_source_keys) else None
            if source_key:
                source_path = Path(source_key)
                if source_path.is_file():
                    sources.append(source_path)
                    continue
            if isinstance(selected, Path) and selected.is_file():
                sources.append(selected)
            else:
                sources.append(None)
        return sources

    def selected_filled_count(self) -> int:
        return sum(1 for path in self.selected_paths if path is not None)

    def _hide_notice(self) -> None:
        self._notice_label.hide()

    def show_notice(self, message: str, duration_ms: int = 1000) -> None:
        self._notice_label.setText(message)
        self._notice_label.show()
        self._notice_label.raise_()
        self._notice_timer.start(max(200, int(duration_ms)))

    def keyPressEvent(self, event):  # noqa: N802
        key = event.key()
        text = event.text().strip()
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(self._left_source_paths):
                self._on_left_thumb_clicked(idx)
                return
        if key == KEY_BACKSPACE:
            self.clear_active_slot()
            print("[SELECT_PHOTO] cleared last selected slot")
            return
        super().keyPressEvent(event)


class PreloadSelectPhotoWorker(QThread):
    success = Signal(int, dict)
    failure = Signal(int, str, dict)
    progress = Signal(int, int, str, str)

    def __init__(
        self,
        session_dir: Optional[Path],
        layout_id: Optional[str],
        captured_paths: list[str],
        print_slots: int,
        request_token: int = 0,
        gif_enabled: bool = True,
        gif_interval_ms: int = 200,
        gif_max_width: int = 480,
        gif_frames_by_shot: Optional[dict[int, list[bytes]]] = None,
        ai_mode_4641: bool = False,
        ai_style_id: str = "",
        ai_remote_allowed: bool = True,
        ai_strict_mode: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.session_dir = Path(session_dir) if session_dir else None
        self.layout_id = layout_id
        self.captured_paths = [Path(p) for p in captured_paths if p]
        self.print_slots = max(1, int(print_slots or 0))
        self.request_token = int(request_token)
        self._base_dir = ROOT_DIR / "assets" / "ui" / "9_select_photo"
        self.gif_enabled = bool(gif_enabled)
        self.gif_interval_ms = max(50, int(gif_interval_ms or 200))
        self.gif_max_width = max(64, int(gif_max_width or 480))
        self.gif_frames_by_shot = gif_frames_by_shot or {}
        self.ai_mode_4641 = bool(ai_mode_4641)
        self.ai_style_id = str(ai_style_id or "").strip().lower()
        self.ai_remote_allowed = bool(ai_remote_allowed)
        self.ai_strict_mode = bool(ai_strict_mode)

    def _emit_progress(self, percent: int, ko_message: str, en_message: str) -> None:
        if not self.ai_mode_4641:
            return
        safe_percent = max(0, min(100, int(percent)))
        self.progress.emit(
            int(self.request_token),
            safe_percent,
            str(ko_message or "").strip(),
            str(en_message or "").strip(),
        )

    @staticmethod
    def _sort_rects(rects: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
        return sorted(rects, key=lambda r: (r[1], r[0]))

    def _find_background_path(self) -> Optional[Path]:
        layout_id = self.layout_id
        if layout_id:
            exact = self._base_dir / f"main_{layout_id}.png"
            if exact.is_file():
                return exact
            candidates = sorted(
                [p for p in self._base_dir.glob("*.png") if layout_id in p.stem],
                key=lambda p: p.name.lower(),
            )
            if candidates:
                return candidates[0]
        fallback = self._base_dir / "main_2641.png"
        if fallback.is_file():
            return fallback
        any_png = sorted(self._base_dir.glob("*.png"), key=lambda p: p.name.lower())
        if any_png:
            return any_png[0]
        return None

    @staticmethod
    def _split_rect_groups(
        rects: list[tuple[int, int, int, int]]
    ) -> tuple[list[tuple[int, int, int, int]], list[tuple[int, int, int, int]]]:
        if len(rects) <= 1:
            return rects, []

        rects_by_center = sorted(rects, key=lambda r: (r[0] + r[2] / 2.0, r[1]))
        centers = [r[0] + r[2] / 2.0 for r in rects_by_center]
        best_gap = -1.0
        split_idx = -1
        for idx in range(len(centers) - 1):
            gap = centers[idx + 1] - centers[idx]
            if gap > best_gap:
                best_gap = gap
                split_idx = idx

        if split_idx < 0:
            midpoint = len(rects_by_center) // 2
            left = rects_by_center[:midpoint]
            right = rects_by_center[midpoint:]
        else:
            left = rects_by_center[: split_idx + 1]
            right = rects_by_center[split_idx + 1 :]

        if not left or not right:
            midpoint = len(rects_by_center) // 2
            left = rects_by_center[:midpoint]
            right = rects_by_center[midpoint:]

        if left and right:
            left_avg_x = sum(r[0] + (r[2] / 2.0) for r in left) / len(left)
            right_avg_x = sum(r[0] + (r[2] / 2.0) for r in right) / len(right)
            if left_avg_x > right_avg_x:
                left, right = right, left

        return (
            PreloadSelectPhotoWorker._sort_rects(left),
            PreloadSelectPhotoWorker._sort_rects(right),
        )

    @staticmethod
    def _detect_gray_rects(background_path: Path) -> list[tuple[int, int, int, int]]:
        try:
            with Image.open(background_path) as source:
                rgba = source.convert("RGBA")
        except Exception:
            return []
        components = _detect_gray_slot_components(rgba)
        if not components:
            return []
        components = sorted(components, key=lambda item: item[1], reverse=True)
        max_area = max(area for _rect, area in components)
        area_cutoff = max(4000, int(max_area * 0.08))
        rects = [rect for rect, area in components if area >= area_cutoff]
        if not rects:
            rects = [rect for rect, _area in components[:24]]
        return rects

    @staticmethod
    def _cover_image(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
        if target_w <= 0 or target_h <= 0:
            return image.convert("RGB")
        source = image.convert("RGB")
        scale = max(target_w / source.width, target_h / source.height)
        resized_w = max(1, int(round(source.width * scale)))
        resized_h = max(1, int(round(source.height * scale)))
        if hasattr(Image, "Resampling"):
            resized = source.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
        else:
            resized = source.resize((resized_w, resized_h), Image.LANCZOS)
        left = max(0, (resized_w - target_w) // 2)
        top = max(0, (resized_h - target_h) // 2)
        return resized.crop((left, top, left + target_w, top + target_h))

    def _build_share_gif(self, payload: dict) -> None:
        if not self.gif_enabled:
            return
        if self.session_dir is None:
            print("[GIF] build skipped (session missing)")
            return

        frames: list[Image.Image] = []
        total_grabs = 0
        for shot_index in sorted(self.gif_frames_by_shot.keys()):
            bucket = self.gif_frames_by_shot.get(shot_index) or []
            for raw in bucket:
                total_grabs += 1
                try:
                    with Image.open(io.BytesIO(raw)) as source:
                        image = source.convert("RGB")
                        if image.width > self.gif_max_width:
                            ratio = self.gif_max_width / float(image.width)
                            target_h = max(1, int(round(image.height * ratio)))
                            if hasattr(Image, "Resampling"):
                                image = image.resize((self.gif_max_width, target_h), Image.Resampling.LANCZOS)
                            else:
                                image = image.resize((self.gif_max_width, target_h), Image.LANCZOS)
                        frames.append(image)
                except Exception:
                    continue

        print(f"[GIF] build start shots={len(self.gif_frames_by_shot)} frames={total_grabs}")
        if len(frames) < 2:
            print("[GIF] build skipped (not enough frames)")
            return

        share_dir = ensure_share_dir(self.session_dir)
        gif_path = share_dir / "video.gif"
        try:
            first = frames[0]
            rest = frames[1:]
            first.save(
                gif_path,
                format="GIF",
                save_all=True,
                append_images=rest,
                duration=self.gif_interval_ms,
                loop=0,
                optimize=False,
            )
            payload["video_gif_path"] = str(gif_path)
            print(f"[GIF] build ok path={gif_path} bytes={gif_path.stat().st_size}")
        finally:
            for image in frames:
                try:
                    image.close()
                except Exception:
                    pass

    def _build_ai_candidate_paths(self, payload: dict) -> list[Path]:
        if not self.ai_mode_4641:
            return []
        if self.session_dir is None:
            return []
        style_id = _resolve_preferred_ai_style_id(self.ai_style_id)
        ai_dir = self.session_dir / "ai"
        ai_dir.mkdir(parents=True, exist_ok=True)

        results: list[Path] = []
        candidate_map: dict[str, str] = {}
        total = max(1, len(self.captured_paths))
        for index, source_path in enumerate(self.captured_paths, start=1):
            if self.isInterruptionRequested():
                return results
            if not source_path.is_file():
                continue
            step_begin = 15 + int(((index - 1) / total) * 70)
            self._emit_progress(
                step_begin,
                f"AI 사진 생성중 ({index}/{total})",
                f"Generating AI photo ({index}/{total})",
            )
            out_path = ai_dir / f"ai_pick_{index:02d}_{style_id}.jpg"
            if out_path.is_file():
                results.append(out_path)
                candidate_map[str(source_path)] = str(out_path)
                step_done = 15 + int((index / total) * 70)
                self._emit_progress(
                    step_done,
                    f"AI 사진 준비됨 ({index}/{total})",
                    f"AI photo ready ({index}/{total})",
                )
                continue
            try:
                with Image.open(source_path) as source:
                    if self.ai_remote_allowed:
                        ai_image = _generate_ai_variant_image(
                            source,
                            style_id,
                            allow_local_fallback=not self.ai_strict_mode,
                        )
                    else:
                        ai_image = _apply_local_ai_style(source, style_id)
                    ai_image.convert("RGB").save(out_path, format="JPEG", quality=92)
                    results.append(out_path)
                    candidate_map[str(source_path)] = str(out_path)
            except Exception as exc:
                print(f"[AI_MODE] preload candidate failed shot={source_path.name} err={exc}")
                if self.ai_remote_allowed and self.ai_strict_mode:
                    raise RuntimeError(
                        f"ai_preload_failed_strict shot={source_path.name} err={exc}"
                    ) from exc
            step_done = 15 + int((index / total) * 70)
            self._emit_progress(
                step_done,
                f"AI 사진 준비됨 ({index}/{total})",
                f"AI photo ready ({index}/{total})",
            )
        if results:
            payload["ai_candidate_paths"] = [str(p) for p in results]
            payload["ai_candidate_map"] = candidate_map
            print(
                f"[AI_MODE] preload generated style={style_id} count={len(results)} "
                f"remote={1 if self.ai_remote_allowed else 0}"
            )
        return results

    def run(self) -> None:
        payload: dict = {
            "bg_path": None,
            "left_rects": [],
            "right_rects": [],
            "thumb_paths": [],
            "ai_candidate_paths": [],
            "ai_candidate_map": {},
            "video_gif_path": None,
        }
        try:
            self._emit_progress(3, "AI 생성 준비중", "Preparing AI generation")
            background_path = self._find_background_path()
            if background_path is not None:
                payload["bg_path"] = str(background_path)
                rects = self._detect_gray_rects(background_path)
                left_rects, right_rects = self._split_rect_groups(rects)
                if len(right_rects) < self.print_slots and len(rects) >= self.print_slots:
                    rects_by_center = sorted(rects, key=lambda r: (r[0] + r[2] / 2.0, r[1]))
                    right_rects = self._sort_rects(rects_by_center[-self.print_slots :])
                    left_rects = self._sort_rects(rects_by_center[: -self.print_slots])
                elif len(right_rects) > self.print_slots:
                    by_area = sorted(
                        right_rects,
                        key=lambda r: (r[2] * r[3], -r[1], -r[0]),
                        reverse=True,
                    )
                    right_rects = self._sort_rects(by_area[: self.print_slots])
                payload["left_rects"] = left_rects
                payload["right_rects"] = right_rects
            self._emit_progress(10, "레이아웃 분석중", "Analyzing layout")

            cache_root = self.session_dir if self.session_dir is not None else _resolve_runtime_out_dir()
            thumbs_dir = cache_root / "cache" / "thumbs"
            thumbs_dir.mkdir(parents=True, exist_ok=True)
            ai_candidates = self._build_ai_candidate_paths(payload)
            thumb_sources: list[Path] = list(self.captured_paths)
            thumb_pairs: list[tuple[Path, Optional[Path]]] = []
            if self.ai_mode_4641 and self.captured_paths:
                for idx, source_path in enumerate(self.captured_paths):
                    ai_path = ai_candidates[idx] if idx < len(ai_candidates) else None
                    thumb_pairs.append((source_path, ai_path if isinstance(ai_path, Path) and ai_path.is_file() else None))
            else:
                for source_path in thumb_sources:
                    thumb_pairs.append((source_path, None))

            left_rects = payload.get("left_rects") or []
            if self.ai_mode_4641:
                self._emit_progress(90, "썸네일 준비중", "Preparing thumbnails")
            for index, (source_path, ai_pair_path) in enumerate(thumb_pairs, start=1):
                if self.isInterruptionRequested():
                    return
                if not source_path.is_file():
                    continue
                target_w = 320
                target_h = 220
                if index - 1 < len(left_rects):
                    rect = left_rects[index - 1]
                    target_w = max(1, int(rect[2]))
                    target_h = max(1, int(rect[3]))
                elif left_rects:
                    rect = left_rects[-1]
                    target_w = max(1, int(rect[2]))
                    target_h = max(1, int(rect[3]))

                thumb_path = thumbs_dir / f"thumb_{index:02d}.jpg"
                source_for_thumb = ai_pair_path if self.ai_mode_4641 and ai_pair_path is not None else source_path
                with Image.open(source_for_thumb) as source:
                    covered = self._cover_image(source, target_w, target_h)
                covered.save(thumb_path, format="JPEG", quality=88)
                payload["thumb_paths"].append(str(thumb_path))
                if self.ai_mode_4641:
                    thumb_total = max(1, len(thumb_pairs))
                    thumb_pct = 90 + int((index / thumb_total) * 8)
                    self._emit_progress(
                        thumb_pct,
                        f"썸네일 생성중 ({index}/{thumb_total})",
                        f"Building thumbnails ({index}/{thumb_total})",
                    )

            self._build_share_gif(payload)
            self._emit_progress(100, "AI 생성 완료", "AI generation complete")
            self.success.emit(self.request_token, payload)
        except Exception as exc:
            self.failure.emit(self.request_token, str(exc), payload)


class DesignPreviewWorker(QThread):
    preview_ready = Signal(int, bytes, int, str)
    preview_error = Signal(int, str)

    def __init__(
        self,
        job_id: int,
        layout_id: str,
        selected_paths: list[Path],
        frame_index: int,
        is_gray: bool,
        flip_horizontal: bool,
        qr_enabled: bool,
        qr_value: Optional[str],
        preview_size: tuple[int, int],
        ai_mode_4641: bool = False,
        ai_style_id: str = "",
        ai_source_a: str = "",
        ai_source_b: str = "",
        ai_session_dir: str = "",
        ai_remote_allowed: bool = True,
        ai_strict_mode: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.job_id = int(job_id)
        self.layout_id = layout_id
        self.selected_paths = [Path(p) for p in selected_paths]
        self.frame_index = int(frame_index)
        self.is_gray = bool(is_gray)
        self.flip_horizontal = bool(flip_horizontal)
        self.qr_enabled = bool(qr_enabled)
        self.qr_value = str(qr_value or "").strip()
        self.preview_size = (
            max(1, int(preview_size[0])),
            max(1, int(preview_size[1])),
        )
        self.ai_mode_4641 = bool(ai_mode_4641)
        self.ai_style_id = str(ai_style_id or "").strip().lower()
        self.ai_source_a = Path(ai_source_a) if str(ai_source_a or "").strip() else None
        self.ai_source_b = Path(ai_source_b) if str(ai_source_b or "").strip() else None
        self.ai_session_dir = Path(ai_session_dir) if str(ai_session_dir or "").strip() else None
        self.ai_remote_allowed = bool(ai_remote_allowed)
        self.ai_strict_mode = bool(ai_strict_mode)

    @staticmethod
    def _fit_preview(image: Image.Image, preview_size: tuple[int, int]) -> Image.Image:
        target_w, target_h = preview_size
        if target_w <= 0 or target_h <= 0:
            return image.convert("RGBA")
        source = image.convert("RGBA")
        ratio = min(target_w / source.width, target_h / source.height)
        resized_w = max(1, int(round(source.width * ratio)))
        resized_h = max(1, int(round(source.height * ratio)))
        if hasattr(Image, "Resampling"):
            resized = source.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
        else:
            resized = source.resize((resized_w, resized_h), Image.LANCZOS)
        canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        x = (target_w - resized_w) // 2
        y = (target_h - resized_h) // 2
        canvas.paste(resized, (x, y), resized)
        return canvas

    def _build_ai_preview_paths(self) -> list[Path]:
        style_id = _resolve_preferred_ai_style_id(self.ai_style_id)
        if self.ai_source_a is None or not self.ai_source_a.is_file():
            raise RuntimeError("ai preview source_a missing")
        if self.ai_source_b is None or not self.ai_source_b.is_file():
            raise RuntimeError("ai preview source_b missing")
        if self.ai_session_dir is None:
            raise RuntimeError("ai preview session dir missing")

        ai_dir = self.ai_session_dir / "ai"
        ai_dir.mkdir(parents=True, exist_ok=True)
        out_a = ai_dir / f"ai_preview_01_{style_id}.jpg"
        out_b = ai_dir / f"ai_preview_02_{style_id}.jpg"

        if out_a.is_file() and out_b.is_file():
            print(
                f"[AI_MODE] cache hit purpose=preview style={style_id} "
                f"a={out_a.name} b={out_b.name}"
            )
            return [self.ai_source_a, out_a, out_b, self.ai_source_b]

        with Image.open(self.ai_source_a) as img_a:
            if self.ai_remote_allowed:
                ai_a = _generate_ai_variant_image(
                    img_a,
                    style_id,
                    allow_local_fallback=not self.ai_strict_mode,
                )
            else:
                ai_a = _apply_local_ai_style(img_a, style_id)
            ai_a.convert("RGB").save(out_a, format="JPEG", quality=95)
        with Image.open(self.ai_source_b) as img_b:
            if self.ai_remote_allowed:
                ai_b = _generate_ai_variant_image(
                    img_b,
                    style_id,
                    allow_local_fallback=not self.ai_strict_mode,
                )
            else:
                ai_b = _apply_local_ai_style(img_b, style_id)
            ai_b.convert("RGB").save(out_b, format="JPEG", quality=95)

        print(
            f"[AI_MODE] generated purpose=preview style={style_id} "
            f"remote={1 if self.ai_remote_allowed else 0} a={out_a.name} b={out_b.name}"
        )
        print(
            "[AI_MODE] preview map 4641 slots=LT:orig1 RT:ai1 LB:ai2 RB:orig2 "
            f"style={style_id}"
        )
        return [self.ai_source_a, out_a, out_b, self.ai_source_b]

    def run(self) -> None:
        started_at = time.perf_counter()
        try:
            selected_paths = list(self.selected_paths)
            if self.ai_mode_4641:
                selected_paths = self._build_ai_preview_paths()
            composed, slot_count, preview_frame_path = SelectDesignScreen.build_preview_image_static(
                layout_id=self.layout_id,
                frame_index=self.frame_index,
                selected_paths=selected_paths,
                is_gray=self.is_gray,
                flip_horizontal=self.flip_horizontal,
                qr_enabled=self.qr_enabled,
                qr_value=self.qr_value,
            )
            preview = self._fit_preview(composed, self.preview_size)
            buffer = io.BytesIO()
            preview.save(buffer, format="PNG")
            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
            print(
                f"[DESIGN] preview build layout={self.layout_id} idx={self.frame_index} "
                f"slots={slot_count} photos={len(selected_paths)} ok"
            )
            self.preview_ready.emit(self.job_id, buffer.getvalue(), elapsed_ms, str(preview_frame_path))
        except Exception as exc:
            self.preview_error.emit(self.job_id, str(exc))


class SelectDesignScreen(ImageScreen):
    DEFAULT_UI_DIR = ROOT_DIR / "assets" / "ui" / "10_select_Design"
    CELEBRITY_UI_DIR = ROOT_DIR / "assets" / "ui" / "10_select_Design_celebrity"
    PREVIEW_AREA = (120, 140, 980, 900)
    PREVIEW_AREA_BY_LAYOUT = {
        # Slightly smaller to keep clear of top title in design screen.
        "2641": (140, 180, 940, 830),
        # 4641 preview was overlapping top title; lower and shrink slightly.
        "4641": (140, 190, 930, 810),
        # 4661 preview also overlaps title area; move down and reduce size.
        "4661": (150, 200, 920, 790),
    }
    COLOR_ICON_RECT = (1291, 340, 79, 79)
    GRAY_ICON_RECT = (1410, 340, 79, 79)
    FLIP_ICON_RECT = (1350, 580, 79, 79)
    QR_BOX_RECT = (1183, 945, 58, 58)
    QR_CHECK_RECT = (1187, 949, 49, 49)
    STATE_TEXT_RECT = (1140, 170, 700, 80)
    COLOR_SWATCH_RECT = (1346, 789, 79, 79)

    @classmethod
    def _design_ui_dir_for_layout(cls, layout_id: Optional[str]) -> Path:
        key = str(layout_id or "").strip()
        if key == "2461" and cls.CELEBRITY_UI_DIR.is_dir():
            return cls.CELEBRITY_UI_DIR
        return cls.DEFAULT_UI_DIR

    def __init__(self, main_window: "KioskMainWindow") -> None:
        self._base_dir = self._design_ui_dir_for_layout(None)
        background = self._resolve_background_path()
        super().__init__(main_window, "select_design", background)
        self.layout_id: Optional[str] = None
        self.selected_print_paths: list[Path] = []
        self.frame_index = 1
        self.is_gray = False
        self.flip_horizontal = False
        self.qr_enabled = True
        self._frame_indices: list[int] = []
        self._preview_job_id = 0
        self._preview_workers: dict[int, DesignPreviewWorker] = {}
        self._pending_preview_render = False
        self._ai_loading_active_job: Optional[int] = None
        self._ai_loading_tick = 0
        self._ai_loading_is_ai_mode = False
        self._ai_loading_progress = 0

        self._bg_label = QLabel(self)
        self._bg_label.setAlignment(ALIGN_CENTER)
        self._bg_label.setScaledContents(True)
        self._bg_label.setAttribute(WA_TRANSPARENT, True)
        if not self._background.isNull():
            self._bg_label.setPixmap(self._background)

        self.preview_label = QLabel(self._bg_label)
        self.preview_label.setAlignment(ALIGN_CENTER)
        self.preview_label.setStyleSheet(
            "QLabel { background: transparent; border: 2px solid rgba(255,255,255,160); color: white; }"
        )
        self.preview_label.setAutoFillBackground(False)
        self.preview_label.setAttribute(WA_TRANSPARENT, True)
        self.preview_label.setAttribute(WA_TRANSLUCENT, True)

        self.color_swatch = QLabel(self._bg_label)
        self.color_swatch.setStyleSheet("QLabel { background: transparent; border: none; }")
        self.color_swatch.setAttribute(WA_TRANSPARENT, True)
        self.color_swatch.hide()

        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._hide_notice)
        self._notice_label = QLabel("", self._bg_label)
        self._notice_label.setAlignment(ALIGN_CENTER)
        self._notice_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0, 0, 0, 180); "
            "font-size: 42px; font-weight: 700; border: 2px solid rgba(255,255,255,150); }"
        )
        self._notice_label.hide()

        self._ai_loading_overlay = QWidget(self._bg_label)
        self._ai_loading_overlay.setStyleSheet(
            "QWidget { background-color: rgba(0, 0, 0, 190); border: 2px solid rgba(255,255,255,120); }"
        )
        self._ai_loading_title = QLabel("AI 생성중 / Generating AI Photos", self._ai_loading_overlay)
        self._ai_loading_title.setAlignment(ALIGN_CENTER)
        self._ai_loading_title.setStyleSheet(
            "QLabel { color: white; background: transparent; font-size: 30px; font-weight: 800; border: none; }"
        )
        self._ai_loading_bar_bg = QWidget(self._ai_loading_overlay)
        self._ai_loading_bar_bg.setStyleSheet(
            "QWidget { background-color: rgba(255,255,255,24); border: 1px solid rgba(255,255,255,110); "
            "border-radius: 8px; }"
        )
        self._ai_loading_bar_segments: list[QLabel] = []
        for _ in range(10):
            seg = QLabel(self._ai_loading_bar_bg)
            seg.setStyleSheet("QLabel { background-color: rgba(255,255,255,25); border-radius: 4px; }")
            self._ai_loading_bar_segments.append(seg)
        self._ai_loading_percent_label = QLabel("0%", self._ai_loading_overlay)
        self._ai_loading_percent_label.setAlignment(ALIGN_CENTER)
        self._ai_loading_percent_label.setStyleSheet(
            "QLabel { color: white; background: transparent; font-size: 30px; font-weight: 800; border: none; }"
        )
        self._ai_loading_hint_label = QLabel("잠시만 기다려주세요 / Please wait", self._ai_loading_overlay)
        self._ai_loading_hint_label.setAlignment(ALIGN_CENTER)
        self._ai_loading_hint_label.setStyleSheet(
            "QLabel { color: rgba(255,255,255,210); background: transparent; font-size: 24px; font-weight: 700; "
            "border: none; }"
        )
        self._ai_loading_overlay.hide()

        self._ai_loading_timer = QTimer(self)
        self._ai_loading_timer.setInterval(280)
        self._ai_loading_timer.timeout.connect(self._tick_ai_loading_overlay)

        self.state_label = QLabel(self._bg_label)
        self.state_label.setAlignment(ALIGN_CENTER)
        self.state_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0,0,0,130); font-size: 28px; font-weight: 700; }"
        )
        self.state_label.setAttribute(WA_TRANSPARENT, True)

        self.color_icon_label = QLabel(self._bg_label)
        self.gray_icon_label = QLabel(self._bg_label)
        self.flip_icon_label = QLabel(self._bg_label)
        self.qr_box_label = QLabel(self._bg_label)
        self.qr_check_label = QLabel(self._bg_label)

        icon_labels = [
            self.color_icon_label,
            self.gray_icon_label,
            self.flip_icon_label,
            self.qr_box_label,
            self.qr_check_label,
        ]
        for label in icon_labels:
            label.setAlignment(ALIGN_CENTER)
            label.setAttribute(WA_TRANSPARENT, True)

        self.qr_check_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        self.qr_box_label.setStyleSheet("QLabel { background: transparent; border: none; }")

        self._pix_color_on = QPixmap()
        self._pix_color_off = QPixmap()
        self._pix_gray_on = QPixmap()
        self._pix_gray_off = QPixmap()
        self._pix_flip_on = QPixmap()
        self._pix_flip_off = QPixmap()
        self._pix_qr_check = QPixmap()
        self._reload_design_ui_assets()

        self._layout_widgets()
        self.update_ui_state()
        self._update_color_swatch()
        print("[SELECT_DESIGN] preview parent=bg_label transparent=1")

    def _reload_design_ui_assets(self) -> None:
        background = self._resolve_background_path()
        self._background = QPixmap(str(background))
        if self._background.isNull():
            print(f"[SELECT_DESIGN] background missing: {background}")
        self._bg_label.setPixmap(self._background)
        self._pix_color_on = QPixmap(str(self._base_dir / "Filter" / "on" / "color.png"))
        self._pix_color_off = QPixmap(str(self._base_dir / "Filter" / "off" / "color_off.png"))
        self._pix_gray_on = QPixmap(str(self._base_dir / "Filter" / "on" / "gray.png"))
        self._pix_gray_off = QPixmap(str(self._base_dir / "Filter" / "off" / "gray_off.png"))
        self._pix_flip_on = QPixmap(str(self._base_dir / "Filter" / "on" / "horizontal.png"))
        self._pix_flip_off = QPixmap(str(self._base_dir / "Filter" / "off" / "horizontal_off.png"))
        self._pix_qr_check = QPixmap(str(self._base_dir / "QR_code_check_box.png"))

    def _resolve_background_path(self) -> Path:
        candidates = [
            self._base_dir / "main.png",
            self._base_dir / "please_select_a_design.png",
        ]
        for path in candidates:
            if path.is_file():
                return path
        scanned = sorted(self._base_dir.glob("*.png"), key=lambda p: p.name.lower())
        if scanned:
            return scanned[0]
        return self._base_dir / "main.png"

    @staticmethod
    def _extract_frame_number(path: Path) -> Optional[int]:
        stem = path.stem.strip()
        if stem.isdigit():
            return int(stem)
        match = re.search(r"\d+", stem)
        if match:
            return int(match.group(0))
        return None

    def _frame_dir(self, layout_id: Optional[str]) -> Path:
        layout_text = layout_id or "2641"
        direct = self._base_dir / "Frame" / "Frame2" / layout_text
        if direct.is_dir():
            return direct
        if str(layout_text).strip() == "2461":
            fallback = self._base_dir / "Frame" / "Frame2" / "2641"
            if fallback.is_dir():
                return fallback
        return direct

    def _available_frame_indices(self, layout_id: Optional[str]) -> list[int]:
        frame_dir = self._frame_dir(layout_id)
        if not frame_dir.is_dir():
            return list(range(1, 15))
        numbers: list[int] = []
        for path in frame_dir.glob("*.png"):
            number = self._extract_frame_number(path)
            if number is not None and number > 0:
                numbers.append(number)
        if not numbers:
            return list(range(1, 15))
        return sorted(set(numbers))

    def _resolve_frame_path(self, layout_id: Optional[str], frame_index: int) -> Optional[Path]:
        frame_dir = self._frame_dir(layout_id)
        if not frame_dir.is_dir():
            return None
        exact = frame_dir / f"{int(frame_index)}.png"
        if exact.is_file():
            return exact
        matched: list[Path] = []
        for path in frame_dir.glob("*.png"):
            number = self._extract_frame_number(path)
            if number == int(frame_index):
                matched.append(path)
        if matched:
            return sorted(matched, key=lambda p: p.name.lower())[0]
        fallback_files = sorted(frame_dir.glob("*.png"), key=lambda p: p.name.lower())
        if fallback_files:
            return fallback_files[0]
        return None

    def _layout_widgets(self) -> None:
        self._bg_label.setGeometry(self.design_rect_to_widget((0, 0, DESIGN_WIDTH, DESIGN_HEIGHT)))
        if not self._background.isNull():
            self._bg_label.setPixmap(self._background)
        self._bg_label.lower()
        self.preview_label.setGeometry(self.design_rect_to_widget(self._current_preview_area()))
        self.preview_label.raise_()
        swatch_rect = self.design_rect_to_widget(self.COLOR_SWATCH_RECT)
        self.color_swatch.setGeometry(swatch_rect)
        self.color_swatch.raise_()
        self.state_label.setGeometry(self.design_rect_to_widget(self.STATE_TEXT_RECT))
        self.color_icon_label.setGeometry(self.design_rect_to_widget(self.COLOR_ICON_RECT))
        self.gray_icon_label.setGeometry(self.design_rect_to_widget(self.GRAY_ICON_RECT))
        self.flip_icon_label.setGeometry(self.design_rect_to_widget(self.FLIP_ICON_RECT))
        self.qr_box_label.setGeometry(self.design_rect_to_widget(self.QR_BOX_RECT))
        self.qr_check_label.setGeometry(self.design_rect_to_widget(self.QR_CHECK_RECT))
        self._notice_label.setGeometry(self.design_rect_to_widget((450, 430, 1020, 180)))
        self._ai_loading_overlay.setGeometry(self.preview_label.geometry())
        self._layout_ai_loading_overlay()
        self.state_label.raise_()
        self.color_icon_label.raise_()
        self.gray_icon_label.raise_()
        self.flip_icon_label.raise_()
        self.color_swatch.raise_()
        self.qr_box_label.raise_()
        self.qr_check_label.raise_()
        if self._ai_loading_overlay.isVisible():
            self._ai_loading_overlay.raise_()
        self._notice_label.raise_()

    def _layout_ai_loading_overlay(self) -> None:
        if self._ai_loading_overlay.width() <= 0 or self._ai_loading_overlay.height() <= 0:
            return
        ow = self._ai_loading_overlay.width()
        oh = self._ai_loading_overlay.height()
        pad_x = max(16, int(ow * 0.06))
        title_h = max(40, int(oh * 0.18))
        bar_h = max(30, int(oh * 0.16))
        hint_h = max(34, int(oh * 0.14))
        y = max(10, int(oh * 0.14))
        self._ai_loading_title.setGeometry(pad_x, y, max(1, ow - (pad_x * 2)), title_h)
        y += title_h + max(10, int(oh * 0.08))

        percent_w = max(86, int(ow * 0.16))
        bar_total_w = max(120, ow - (pad_x * 2))
        bar_w = max(100, bar_total_w - percent_w - 12)
        self._ai_loading_bar_bg.setGeometry(pad_x, y, bar_w, bar_h)
        self._ai_loading_percent_label.setGeometry(pad_x + bar_w + 12, y, percent_w, bar_h)

        seg_pad = 8
        seg_gap = 6
        inner_w = max(10, bar_w - (seg_pad * 2))
        seg_w = max(6, int((inner_w - seg_gap * 9) / 10))
        seg_h = max(10, bar_h - (seg_pad * 2))
        cursor_x = seg_pad
        for seg in self._ai_loading_bar_segments:
            seg.setGeometry(cursor_x, seg_pad, seg_w, seg_h)
            cursor_x += seg_w + seg_gap

        y += bar_h + max(8, int(oh * 0.07))
        self._ai_loading_hint_label.setGeometry(pad_x, y, max(1, ow - (pad_x * 2)), hint_h)

    def _set_ai_loading_progress_visual(self, progress: int, ai_mode: bool = False) -> None:
        safe = max(0, min(100, int(progress)))
        self._ai_loading_percent_label.setText(f"{safe}%")
        filled = max(0, min(10, int((safe + 9) / 10)))
        for idx, seg in enumerate(self._ai_loading_bar_segments):
            if idx < filled:
                seg.setStyleSheet("QLabel { background-color: rgba(70, 190, 255, 230); border-radius: 4px; }")
            else:
                seg.setStyleSheet("QLabel { background-color: rgba(255,255,255,25); border-radius: 4px; }")
        if ai_mode:
            self._ai_loading_title.setText("AI 생성중 / Generating AI Photos")
            self._ai_loading_hint_label.setText("잠시만 기다려주세요 / Please wait")
        else:
            self._ai_loading_title.setText("미리보기 합성중 / Composing Preview")
            self._ai_loading_hint_label.setText("잠시만 기다려주세요 / Please wait")

    def _current_preview_area(self) -> tuple[int, int, int, int]:
        key = str(self.layout_id or "").strip()
        return self.PREVIEW_AREA_BY_LAYOUT.get(key, self.PREVIEW_AREA)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()
        self.update_ui_state()
        self._update_color_swatch()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._update_color_swatch()
        self._layout_widgets()
        if self._pending_preview_render or not self.preview_label.pixmap():
            self._pending_preview_render = False
            QTimer.singleShot(0, self.request_preview_render)

    def set_context(
        self,
        layout_id: Optional[str],
        selected_paths: list[str],
        frame_index: int = 1,
        is_gray: bool = False,
        flip_horizontal: bool = False,
        qr_enabled: bool = True,
    ) -> None:
        desired_base_dir = self._design_ui_dir_for_layout(layout_id)
        if desired_base_dir != self._base_dir:
            self._base_dir = desired_base_dir
            self._reload_design_ui_assets()
            print(f"[SELECT_DESIGN] ui_base={self._base_dir}")

        self.layout_id = layout_id
        self.selected_print_paths = [Path(p) for p in selected_paths if p and Path(p).is_file()]
        self._frame_indices = self._available_frame_indices(layout_id)
        if not self._frame_indices:
            self._frame_indices = list(range(1, 15))

        if frame_index in self._frame_indices:
            self.frame_index = int(frame_index)
        else:
            self.frame_index = int(self._frame_indices[0])
        self.is_gray = bool(is_gray)
        self.flip_horizontal = bool(flip_horizontal)
        self.qr_enabled = bool(qr_enabled)

        self.update_ui_state()
        self._update_color_swatch()
        self._layout_widgets()
        if self.isVisible():
            self.request_preview_render()
        else:
            self._pending_preview_render = True
        print(
            f"[SELECT_DESIGN] enter layout={self.layout_id} "
            f"selected={len(self.selected_print_paths)} frame={self.frame_index} "
            f"gray={1 if self.is_gray else 0} flip={1 if self.flip_horizontal else 0} "
            f"qr={1 if self.qr_enabled else 0}"
        )

    def set_layout(self, layout_id: Optional[str]) -> None:
        self.set_context(
            layout_id=layout_id,
            selected_paths=[str(p) for p in self.selected_print_paths],
            frame_index=self.frame_index,
            is_gray=self.is_gray,
            flip_horizontal=self.flip_horizontal,
            qr_enabled=self.qr_enabled,
        )

    def _set_icon_pixmap(self, label: QLabel, pixmap: QPixmap) -> None:
        if label.width() <= 0 or label.height() <= 0:
            return
        if pixmap.isNull():
            label.clear()
            return
        scaled = pixmap.scaled(label.size(), KEEP_ASPECT, SMOOTH_TRANSFORM)
        label.setPixmap(scaled)

    def update_ui_state(self) -> None:
        self._set_icon_pixmap(self.color_icon_label, self._pix_color_off if self.is_gray else self._pix_color_on)
        self._set_icon_pixmap(self.gray_icon_label, self._pix_gray_on if self.is_gray else self._pix_gray_off)
        self._set_icon_pixmap(self.flip_icon_label, self._pix_flip_on if self.flip_horizontal else self._pix_flip_off)
        self.qr_box_label.setPixmap(QPixmap())
        self.qr_box_label.setText("")
        if self.qr_enabled:
            self._set_icon_pixmap(self.qr_check_label, self._pix_qr_check)
            self.qr_check_label.show()
        else:
            self.qr_check_label.hide()
        self.state_label.setText(
            f"Frame {self.frame_index:02d} | {'GRAY' if self.is_gray else 'COLOR'} | "
            f"FLIP {'ON' if self.flip_horizontal else 'OFF'} | QR {'ON' if self.qr_enabled else 'OFF'}"
        )

    def _log_state_set(self) -> None:
        print(
            f"[SELECT_DESIGN] set frame={self.frame_index} "
            f"gray={1 if self.is_gray else 0} "
            f"flip={1 if self.flip_horizontal else 0} "
            f"qr={1 if self.qr_enabled else 0}"
        )

    def _update_color_swatch(self) -> None:
        swatch_path = self._base_dir / "Color" / f"{int(self.frame_index)}.png"
        if not swatch_path.is_file():
            self.color_swatch.hide()
            print(f"[SELECT_DESIGN] color swatch missing idx={self.frame_index}")
            return
        pixmap = QPixmap(str(swatch_path))
        if pixmap.isNull():
            self.color_swatch.hide()
            print(f"[SELECT_DESIGN] color swatch pixmap null idx={self.frame_index}")
            return
        scaled = pixmap.scaled(
            self.color_swatch.size(),
            KEEP_ASPECT,
            SMOOTH_TRANSFORM,
        )
        self.color_swatch.setPixmap(scaled)
        self.color_swatch.show()
        print(f"[SELECT_DESIGN] color swatch idx={self.frame_index} path={swatch_path}")

    def _hide_notice(self) -> None:
        self._notice_label.hide()

    def _tick_ai_loading_overlay(self) -> None:
        if self._ai_loading_active_job is None or not self._ai_loading_overlay.isVisible():
            return
        self._ai_loading_tick = (self._ai_loading_tick + 1) % 4
        if self._ai_loading_is_ai_mode:
            self._ai_loading_progress = min(97, max(0, int(self._ai_loading_progress)) + 2)
            self._set_ai_loading_progress_visual(self._ai_loading_progress, ai_mode=True)
        else:
            self._ai_loading_progress = min(95, max(0, int(self._ai_loading_progress)) + 3)
            self._set_ai_loading_progress_visual(self._ai_loading_progress, ai_mode=False)

    def _show_ai_loading_overlay(self, job_id: int, ai_mode: bool = False) -> None:
        self._ai_loading_active_job = int(job_id)
        self._ai_loading_tick = 0
        self._ai_loading_is_ai_mode = bool(ai_mode)
        self._ai_loading_progress = 8 if self._ai_loading_is_ai_mode else 12
        if self._ai_loading_is_ai_mode:
            self._set_ai_loading_progress_visual(self._ai_loading_progress, ai_mode=True)
            print(f"[AI_MODE] preview loading start job={job_id}")
        else:
            self._set_ai_loading_progress_visual(self._ai_loading_progress, ai_mode=False)
            print(f"[SELECT_DESIGN] preview loading start job={job_id}")
        self._layout_ai_loading_overlay()
        self._ai_loading_overlay.show()
        self._ai_loading_overlay.raise_()
        if not self._ai_loading_timer.isActive():
            self._ai_loading_timer.start()

    def _hide_ai_loading_overlay(self, job_id: Optional[int] = None) -> None:
        if job_id is not None and self._ai_loading_active_job != int(job_id):
            return
        if self._ai_loading_active_job is not None:
            if self._ai_loading_is_ai_mode:
                print(f"[AI_MODE] preview loading done job={self._ai_loading_active_job}")
            else:
                print(f"[SELECT_DESIGN] preview loading done job={self._ai_loading_active_job}")
        self._ai_loading_active_job = None
        self._ai_loading_is_ai_mode = False
        self._ai_loading_progress = 0
        self._ai_loading_timer.stop()
        self._ai_loading_overlay.hide()

    def show_notice(self, message: str, duration_ms: int = 1000) -> None:
        self._notice_label.setText(message)
        self._notice_label.show()
        self._notice_label.raise_()
        self._notice_timer.start(max(200, int(duration_ms)))

    def _advance_frame(self, delta: int) -> None:
        if not self._frame_indices:
            self._frame_indices = list(range(1, 15))
        if self.frame_index not in self._frame_indices:
            self.frame_index = self._frame_indices[0]
        try:
            current = self._frame_indices.index(self.frame_index)
        except ValueError:
            current = 0
        next_index = (current + int(delta)) % len(self._frame_indices)
        self.frame_index = int(self._frame_indices[next_index])
        self.update_ui_state()
        self._update_color_swatch()
        self._log_state_set()
        self.request_preview_render()

    def set_gray(self, gray_enabled: bool) -> None:
        self.is_gray = bool(gray_enabled)
        self.update_ui_state()
        self._log_state_set()
        self.request_preview_render()

    def toggle_flip(self) -> None:
        self.flip_horizontal = not self.flip_horizontal
        self.update_ui_state()
        self._log_state_set()
        self.request_preview_render()

    def toggle_qr(self) -> None:
        self.qr_enabled = not self.qr_enabled
        self.update_ui_state()
        self._log_state_set()
        self.request_preview_render()

    def request_preview_render(self) -> None:
        if not self.layout_id:
            self.preview_label.setText("layout missing")
            self.preview_label.setPixmap(QPixmap())
            self._hide_ai_loading_overlay()
            return
        selected_paths_for_preview: list[Path] = list(self.selected_print_paths)
        ai_mode_4641 = False
        ai_style_id = ""
        ai_source_a = ""
        ai_source_b = ""
        ai_session_dir = ""
        if self._is_ai_mode_4641():
            try:
                selected_pair = self._resolve_ai_selected_pair()
                if (
                    selected_pair is not None
                    and self._is_ai_generated_path(selected_pair[0])
                    and self._is_ai_generated_path(selected_pair[1])
                ):
                    orig_a, orig_b = self._resolve_ai_original_pair()
                    selected_paths_for_preview = [orig_a, selected_pair[0], selected_pair[1], orig_b]
                    ai_mode_4641 = False
                    print(
                        "[AI_MODE] preview reuse selected slots=LT:orig1 RT:selected1 LB:selected2 RB:orig2 "
                        f"s1={selected_pair[0].name} s2={selected_pair[1].name}"
                    )
                else:
                    style_id = self._resolve_ai_style_id()
                    source_a, source_b = self._resolve_ai_source_pair()
                    session = self.main_window.get_active_session() if hasattr(self.main_window, "get_active_session") else None
                    if session is not None and hasattr(session, "session_dir"):
                        ai_mode_4641 = True
                        ai_style_id = style_id
                        ai_source_a = str(source_a)
                        ai_source_b = str(source_b)
                        ai_session_dir = str(session.session_dir)
                    else:
                        print("[AI_MODE] preview fallback: session missing")
            except Exception as exc:
                print(f"[AI_MODE] preview fallback to selected paths err={exc}")
        if not selected_paths_for_preview:
            self.preview_label.setText("selected photos missing")
            self.preview_label.setPixmap(QPixmap())
            self._hide_ai_loading_overlay()
            return
        assets = resolve_design_asset_paths(self.layout_id, self.frame_index)
        if assets.get("preview_frame_path") is None and assets.get("frame2_path") is None:
            self.preview_label.setText("frame missing")
            self.preview_label.setPixmap(QPixmap())
            self._hide_ai_loading_overlay()
            print(f"[SELECT_DESIGN] frame missing layout={self.layout_id} frame={self.frame_index}")
            return

        self._preview_job_id += 1
        job_id = self._preview_job_id
        pw = max(1, int(self.preview_label.width()))
        ph = max(1, int(self.preview_label.height()))
        if pw < 120 or ph < 120:
            rx, ry, rw, rh = self._current_preview_area()
            fallback = self.design_rect_to_widget((rx, ry, rw, rh))
            pw = max(pw, int(fallback.width()))
            ph = max(ph, int(fallback.height()))
        preview_size = (pw, ph)
        worker = DesignPreviewWorker(
            job_id=job_id,
            layout_id=self.layout_id,
            selected_paths=selected_paths_for_preview,
            frame_index=self.frame_index,
            is_gray=self.is_gray,
            flip_horizontal=self.flip_horizontal,
            qr_enabled=self.qr_enabled,
            qr_value=self._resolve_print_qr_url(persist_session=False),
            preview_size=preview_size,
            ai_mode_4641=ai_mode_4641,
            ai_style_id=ai_style_id,
            ai_source_a=ai_source_a,
            ai_source_b=ai_source_b,
            ai_session_dir=ai_session_dir,
            ai_remote_allowed=True,
            ai_strict_mode=bool(
                hasattr(self.main_window, "is_ai_strict_mode_enabled")
                and self.main_window.is_ai_strict_mode_enabled()
            ),
            parent=self,
        )
        worker.preview_ready.connect(self._on_preview_ready)
        worker.preview_error.connect(self._on_preview_error)
        worker.finished.connect(lambda current_job=job_id: self._on_preview_finished(current_job))
        self._preview_workers[job_id] = worker
        self._show_ai_loading_overlay(job_id, ai_mode=ai_mode_4641)
        worker.start()

    def _on_preview_ready(self, job_id: int, png_bytes: bytes, elapsed_ms: int, frame_path: str) -> None:
        if int(job_id) != self._preview_job_id:
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(png_bytes, "PNG"):
            print(f"[SELECT_DESIGN] preview failed decode job={job_id}")
            return
        if pixmap.isNull():
            print(f"[SELECT_DESIGN] preview failed pixmap job={job_id}")
            return
        self.preview_label.setText("")
        target_size = self.preview_label.size()
        if pixmap.size() == target_size:
            self.preview_label.setPixmap(pixmap)
        else:
            scaled = pixmap.scaled(target_size, KEEP_ASPECT, SMOOTH_TRANSFORM)
            self.preview_label.setPixmap(scaled)
        self._hide_ai_loading_overlay(job_id)
        print(
            f"[SELECT_DESIGN] preview updated frame={self.frame_index} "
            f"gray={1 if self.is_gray else 0} flip={1 if self.flip_horizontal else 0} "
            f"job={job_id} (ms={elapsed_ms}) path={frame_path}"
        )

    def _on_preview_error(self, job_id: int, error_message: str) -> None:
        if int(job_id) != self._preview_job_id:
            return
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("preview failed")
        self._hide_ai_loading_overlay(job_id)
        print(f"[SELECT_DESIGN] preview failed job={job_id}: {error_message}")

    def _on_preview_finished(self, job_id: int) -> None:
        worker = self._preview_workers.pop(int(job_id), None)
        if worker is not None:
            worker.deleteLater()
        self._hide_ai_loading_overlay(job_id)

    def get_frame_path(self) -> Optional[Path]:
        if not self.layout_id:
            return None
        assets = resolve_design_asset_paths(self.layout_id, self.frame_index)
        frame2_path = assets.get("frame2_path")
        return frame2_path if frame2_path is not None and frame2_path.is_file() else None

    @staticmethod
    def build_preview_image_static(
        layout_id: str,
        frame_index: int,
        selected_paths: list[Path],
        is_gray: bool,
        flip_horizontal: bool,
        qr_enabled: bool = False,
        qr_value: Optional[str] = None,
    ) -> tuple[Image.Image, int, Path]:
        photos = [Path(p) for p in selected_paths if Path(p).is_file()]
        if not photos:
            raise RuntimeError("selected paths missing")

        assets = resolve_design_asset_paths(layout_id, frame_index)
        preview_frame_path = assets.get("preview_frame_path")
        if preview_frame_path is None or not preview_frame_path.is_file():
            preview_frame_path = assets.get("frame2_path")
        if preview_frame_path is None or not preview_frame_path.is_file():
            raise RuntimeError("preview frame missing")

        slot_ref_path = assets.get("slot_ref_path")
        if slot_ref_path is None or not slot_ref_path.is_file():
            slot_ref_path = assets.get("frame2_path")

        with Image.open(preview_frame_path) as source:
            preview_rgba = source.convert("RGBA")

        target_slots = max(1, len(photos))
        slots, preview_size = _detect_transparent_slots(preview_frame_path, min_area=240)
        if len(slots) < target_slots and slot_ref_path is not None and slot_ref_path.is_file():
            ref_slots, ref_size = _detect_transparent_slots(slot_ref_path, min_area=520)
            if ref_slots:
                slots = _scale_slots(ref_slots, ref_size, preview_rgba.size)

        if not slots:
            fallback_path = slot_ref_path if slot_ref_path is not None else preview_frame_path
            try:
                fallback_slots, _source = resolve_slots(fallback_path, layout_id)
                with Image.open(fallback_path) as fallback_source:
                    fallback_size = fallback_source.size
                slots = _scale_slots(fallback_slots, fallback_size, preview_rgba.size)
            except Exception:
                slots = []

        if not slots:
            raise RuntimeError("preview slots missing")
        slots = _normalize_slots_for_layout(layout_id, slots, preview_rgba.size)
        if len(slots) > target_slots:
            grouped_slots = _split_slots_into_copies(slots, target_slots)
            if grouped_slots and grouped_slots[0]:
                slots = grouped_slots[0][:target_slots]
            else:
                slots = slots[:target_slots]
        elif len(slots) < target_slots:
            fallback_used = _resolve_used_slots_for_canvas(
                layout_id=layout_id,
                slot_ref_path=slot_ref_path if slot_ref_path is not None else preview_frame_path,
                canvas_size=preview_rgba.size,
                photo_count=target_slots,
            )
            if fallback_used:
                slots = fallback_used[:target_slots]
        if len(slots) < target_slots:
            raise RuntimeError("preview slots incomplete")

        composed = _compose_over_template(
            template_rgba=preview_rgba,
            slots=slots,
            selected_paths=photos,
            is_gray=is_gray,
            flip_horizontal=flip_horizontal,
        )
        if qr_enabled and qr_value:
            preview_slots = [tuple(int(v) for v in s) for s in slots[: len(photos)]]
            layout_key = str(layout_id or "").strip()
            anchor_override = "rt" if layout_key == "6241" else None
            preview_qr_rect: Optional[tuple[int, int, int, int]] = _preview_qr_override_rect(
                layout_key,
                composed.size,
            )
            if preview_qr_rect is None:
                preview_qr_rect = _compute_print_qr_rect(
                layout_id=layout_id,
                canvas_size=composed.size,
                occupied_slots=preview_slots,
                anchor_override=anchor_override,
                )
            preview_scale = float(PREVIEW_QR_RECT_SCALE_BY_LAYOUT.get(layout_key, 1.0))
            if preview_qr_rect is not None and abs(preview_scale - 1.0) > 0.001:
                preview_qr_rect = _scale_rect_about_center(
                    preview_qr_rect,
                    composed.size,
                    preview_scale,
                )
            composed = _overlay_qr_on_image(
                image_rgb=composed,
                layout_id=layout_id,
                occupied_slots=preview_slots,
                qr_value=str(qr_value),
                log_prefix="[QR_PREVIEW]",
                use_dummy_qr=True,
                explicit_rect=preview_qr_rect,
            )
        return composed, len(slots), preview_frame_path

    @staticmethod
    def build_confirm_image_static(
        layout_id: str,
        frame_index: int,
        selected_paths: list[Path],
        is_gray: bool,
        flip_horizontal: bool,
    ) -> tuple[Image.Image, int, int, Path, list[tuple[int, int, int, int]]]:
        photos = [Path(p) for p in selected_paths if Path(p).is_file()]
        if not photos:
            raise RuntimeError("selected paths missing")

        assets = resolve_design_asset_paths(layout_id, frame_index)
        frame2_path = assets.get("frame2_path")
        if frame2_path is None or not frame2_path.is_file():
            raise RuntimeError("frame2 missing")
        frame1_path = assets.get("frame1_path")
        slot_ref_path = assets.get("slot_ref_path")
        if slot_ref_path is None or not slot_ref_path.is_file():
            slot_ref_path = frame2_path

        with Image.open(frame2_path) as overlay_source:
            frame2_rgba = overlay_source.convert("RGBA")

        if frame1_path is not None and frame1_path.is_file():
            with Image.open(frame1_path) as base_source:
                frame1_rgb = base_source.convert("RGB")
            if frame1_rgb.size != frame2_rgba.size:
                if hasattr(Image, "Resampling"):
                    frame1_rgb = frame1_rgb.resize(frame2_rgba.size, Image.Resampling.LANCZOS)
                else:
                    frame1_rgb = frame1_rgb.resize(frame2_rgba.size, Image.LANCZOS)
        else:
            frame1_rgb = Image.new("RGB", frame2_rgba.size, (255, 255, 255))

        used_slots = _resolve_used_slots_for_canvas(
            layout_id=layout_id,
            slot_ref_path=slot_ref_path,
            canvas_size=frame2_rgba.size,
            photo_count=len(photos),
        )
        if not used_slots:
            raise RuntimeError("confirm slots missing")

        copies_per_page = max(1, int(len(used_slots) / max(1, len(photos))))
        if layout_id in {"6241", "2641", "2461", "2462"}:
            print(
                f"[DESIGN] slot normalize layout={layout_id} "
                f"copies={copies_per_page} target={len(photos)}"
            )

        base = frame1_rgb.copy()
        for index, (x, y, w, h) in enumerate(used_slots):
            source_path = photos[index % len(photos)]
            with Image.open(source_path) as source:
                photo = _apply_photo_effects(
                    source,
                    is_gray=is_gray,
                    flip_horizontal=flip_horizontal,
                )
            fitted = _fit_cover_pil(photo, w, h)
            base.paste(fitted, (x, y))

        composed = base.convert("RGBA")
        composed.alpha_composite(frame2_rgba)
        return composed.convert("RGB"), len(used_slots), copies_per_page, frame2_path, used_slots

    def _resolve_print_qr_url(self, persist_session: bool = True) -> Optional[str]:
        if not self.qr_enabled:
            return None
        if not hasattr(self.main_window, "get_active_session"):
            return None
        session = self.main_window.get_active_session()
        if session is None:
            return None

        existing = getattr(session, "share_url", None)
        if isinstance(existing, str) and existing.strip():
            return existing.strip()

        base_page = DEFAULT_SHARE_SETTINGS["base_page_url"]
        if hasattr(self.main_window, "get_share_settings"):
            share_cfg = self.main_window.get_share_settings()
            if isinstance(share_cfg, dict):
                base_page = str(share_cfg.get("base_page_url", base_page)).strip() or base_page
        base_page = str(base_page).rstrip("/")
        session_id = str(getattr(session, "session_id", "") or session.session_dir.name)
        page_url = f"{base_page}/{session_id}"
        if persist_session:
            try:
                session.set_share_url(page_url)
            except Exception:
                try:
                    session.share_url = page_url
                except Exception:
                    pass
        return page_url

    def _apply_qr_overlay_to_print(
        self,
        image_rgb: Image.Image,
        occupied_slots: list[tuple[int, int, int, int]],
    ) -> Image.Image:
        if not self.qr_enabled:
            return image_rgb
        if not hasattr(self.main_window, "get_active_session"):
            return image_rgb
        session = self.main_window.get_active_session()
        if session is None:
            print("[QR_PRINT] skip: session missing")
            return image_rgb

        page_url = self._resolve_print_qr_url()
        if not page_url:
            print("[QR_PRINT] skip: page_url missing")
            return image_rgb

        try:
            qr_path = generate_qr_png(page_url, session.qr_dir / "qr.png")
            try:
                session.save_qr(qr_path)
            except Exception:
                pass
        except Exception as exc:
            print(f"[QR_PRINT] generate failed: {exc}")
            return image_rgb

        layout_key = str(self.layout_id or "").strip()
        # AI 4641 is always a single-sheet composition.
        # Keep one QR only (left-bottom by layout anchor), do not split per-copy.
        if layout_key == AI_LAYOUT_ID:
            normalized_slots = _normalize_slots_for_layout(layout_key, list(occupied_slots), image_rgb.size)
            return _overlay_qr_on_image(
                image_rgb=image_rgb,
                layout_id=layout_key,
                occupied_slots=normalized_slots,
                qr_value=page_url,
                log_prefix="[QR_PRINT] ai_single",
            )

        valid_photos = [Path(p) for p in self.selected_print_paths if Path(p).is_file()]
        photo_count = max(1, len(valid_photos))
        return _overlay_qr_per_copy_groups(
            image_rgb=image_rgb,
            layout_id=self.layout_id or "",
            occupied_slots=list(occupied_slots),
            photo_count=photo_count,
            qr_value=page_url,
            log_prefix="[QR_PRINT]",
        )

    @staticmethod
    def _emit_compose_progress(
        progress_cb: Optional[Callable[[int, str, str], None]],
        percent: int,
        ko: str,
        en: str,
    ) -> None:
        if not callable(progress_cb):
            return
        safe_percent = max(0, min(100, int(percent)))
        try:
            progress_cb(safe_percent, str(ko or "").strip(), str(en or "").strip())
        except Exception:
            pass

    def _is_ai_mode_4641(self) -> bool:
        mode = ""
        if hasattr(self.main_window, "compose_mode"):
            mode = str(getattr(self.main_window, "compose_mode", "")).strip().lower()
        return mode == "ai" and str(self.layout_id or "").strip() == AI_LAYOUT_ID

    def _resolve_ai_style_id(self) -> str:
        current_raw = str(getattr(self.main_window, "ai_style_id", "") or "").strip().lower()
        if current_raw in AI_STYLE_PRESETS:
            return current_raw

        session = None
        if hasattr(self.main_window, "get_active_session"):
            session = self.main_window.get_active_session()
        if session is not None:
            session_raw = str(getattr(session, "ai_style_id", "") or "").strip().lower()
            if session_raw in AI_STYLE_PRESETS:
                return session_raw

        for path in self.selected_print_paths:
            parsed = _extract_ai_style_id_from_path(path)
            if parsed in AI_STYLE_PRESETS:
                return parsed

        for raw in list(getattr(self.main_window, "selected_print_paths", []) or []):
            parsed = _extract_ai_style_id_from_path(raw)
            if parsed in AI_STYLE_PRESETS:
                return parsed

        fallback = _resolve_preferred_ai_style_id(current_raw)
        print(f"[AI_MODE] style fallback -> {fallback}")
        return fallback

    def _resolve_ai_source_pair(self) -> tuple[Path, Path]:
        candidates: list[Path] = []
        preferred_originals = list(getattr(self.main_window, "ai_selected_source_paths", []) or [])
        for raw in preferred_originals:
            path = Path(raw)
            if not path.is_file():
                continue
            if path in candidates:
                continue
            candidates.append(path)
            if len(candidates) >= AI_SELECT_SLOTS:
                break
        for path in self.selected_print_paths:
            if not isinstance(path, Path) or not path.is_file():
                continue
            if path in candidates:
                continue
            candidates.append(path)
            if len(candidates) >= AI_SELECT_SLOTS:
                break
        current_captured = list(getattr(self.main_window, "current_captured_paths", []) or [])
        for raw in current_captured:
            if not isinstance(raw, str) or not raw.strip():
                continue
            path = Path(raw)
            if path.is_file():
                if path in candidates:
                    continue
                candidates.append(path)
            if len(candidates) >= AI_SELECT_SLOTS:
                break
        if len(candidates) < AI_SELECT_SLOTS:
            for path in self.selected_print_paths:
                if not path.is_file():
                    continue
                if path in candidates:
                    continue
                candidates.append(path)
                if len(candidates) >= AI_SELECT_SLOTS:
                    break
        if not candidates:
            raise RuntimeError("ai source images missing")
        first = candidates[0]
        second = candidates[1] if len(candidates) > 1 else candidates[0]
        return first, second

    @staticmethod
    def _is_ai_generated_path(path: Path) -> bool:
        try:
            text = str(path).replace("\\", "/").lower()
            name = path.name.lower()
            return "/ai/" in text or name.startswith("ai_") or "ai_pick_" in name
        except Exception:
            return False

    def _resolve_ai_selected_pair(self) -> Optional[tuple[Path, Path]]:
        selected: list[Path] = []
        for path in self.selected_print_paths:
            if not isinstance(path, Path) or not path.is_file():
                continue
            selected.append(path)
            if len(selected) >= AI_SELECT_SLOTS:
                break
        if len(selected) < AI_SELECT_SLOTS:
            return None
        return selected[0], selected[1]

    @staticmethod
    def _ai_pair_style_ids(pair: tuple[Path, Path]) -> set[str]:
        styles: set[str] = set()
        for item in pair:
            parsed = _extract_ai_style_id_from_path(item)
            if parsed:
                styles.add(parsed)
        return styles

    def _resolve_ai_original_pair(self) -> tuple[Path, Path]:
        originals: list[Path] = []
        preferred_originals = list(getattr(self.main_window, "ai_selected_source_paths", []) or [])
        for raw in preferred_originals:
            path = Path(raw)
            if path.is_file():
                originals.append(path)
            if len(originals) >= AI_SELECT_SLOTS:
                break
        current_captured = list(getattr(self.main_window, "current_captured_paths", []) or [])
        for raw in current_captured:
            if not isinstance(raw, str) or not raw.strip():
                continue
            path = Path(raw)
            if path.is_file():
                originals.append(path)
            if len(originals) >= AI_SELECT_SLOTS:
                break
        if len(originals) < AI_SELECT_SLOTS:
            selected_pair = self._resolve_ai_selected_pair()
            if selected_pair is not None:
                originals = [selected_pair[0], selected_pair[1]]
        if not originals:
            raise RuntimeError("ai original images missing")
        first = originals[0]
        second = originals[1] if len(originals) > 1 else originals[0]
        return first, second

    def _is_ai_strict_mode_enabled(self) -> bool:
        if hasattr(self.main_window, "is_ai_strict_mode_enabled"):
            try:
                return bool(self.main_window.is_ai_strict_mode_enabled())
            except Exception:
                return True
        return True

    def _generate_ai_variants(
        self,
        source_a: Path,
        source_b: Path,
        style_id: str,
        purpose: str = "final",
        remote_allowed: bool = True,
        progress_cb: Optional[Callable[[int, str, str], None]] = None,
    ) -> tuple[Path, Path]:
        session = None
        if hasattr(self.main_window, "get_active_session"):
            session = self.main_window.get_active_session()
        if session is None:
            raise RuntimeError("session missing for ai generation")

        ai_dir = session.session_dir / "ai"
        ai_dir.mkdir(parents=True, exist_ok=True)
        purpose_key = str(purpose or "final").strip().lower() or "final"
        out_a = ai_dir / f"ai_{purpose_key}_01_{style_id}.jpg"
        out_b = ai_dir / f"ai_{purpose_key}_02_{style_id}.jpg"

        if out_a.is_file() and out_b.is_file():
            self._emit_compose_progress(progress_cb, 70, "AI 캐시 불러오는 중", "Loading AI cache")
            print(
                f"[AI_MODE] cache hit purpose={purpose_key} style={style_id} "
                f"a={out_a.name} b={out_b.name}"
            )
            return out_a, out_b

        self._emit_compose_progress(progress_cb, 28, "AI 변환 시작", "Starting AI transform")
        strict_mode = self._is_ai_strict_mode_enabled()
        with Image.open(source_a) as img_a:
            self._emit_compose_progress(progress_cb, 40, "AI 사진 1/2 생성중", "Generating AI photo 1/2")
            if remote_allowed:
                ai_a = _generate_ai_variant_image(
                    img_a,
                    style_id,
                    allow_local_fallback=not strict_mode,
                )
            else:
                ai_a = _apply_local_ai_style(img_a, style_id)
            ai_a.convert("RGB").save(out_a, format="JPEG", quality=95)
        self._emit_compose_progress(progress_cb, 58, "AI 사진 1/2 완료", "AI photo 1/2 ready")
        with Image.open(source_b) as img_b:
            self._emit_compose_progress(progress_cb, 72, "AI 사진 2/2 생성중", "Generating AI photo 2/2")
            if remote_allowed:
                ai_b = _generate_ai_variant_image(
                    img_b,
                    style_id,
                    allow_local_fallback=not strict_mode,
                )
            else:
                ai_b = _apply_local_ai_style(img_b, style_id)
            ai_b.convert("RGB").save(out_b, format="JPEG", quality=95)
        self._emit_compose_progress(progress_cb, 82, "AI 변환 완료", "AI transform complete")

        print(
            f"[AI_MODE] generated purpose={purpose_key} style={style_id} "
            f"remote={1 if remote_allowed else 0} a={out_a.name} b={out_b.name}"
        )
        return out_a, out_b

    def _build_preview_paths_ai_4641(self) -> list[Path]:
        style_id = self._resolve_ai_style_id()
        selected_pair = self._resolve_ai_selected_pair()
        if (
            selected_pair is not None
            and self._is_ai_generated_path(selected_pair[0])
            and self._is_ai_generated_path(selected_pair[1])
        ):
            selected_styles = self._ai_pair_style_ids(selected_pair)
            if style_id in selected_styles and len(selected_styles) == 1:
                source_a, source_b = self._resolve_ai_original_pair()
                print(
                    "[AI_MODE] preview map 4641 slots=LT:orig1 RT:selected1 LB:selected2 RB:orig2 "
                    f"s1={selected_pair[0].name} s2={selected_pair[1].name}"
                )
                return [source_a, selected_pair[0], selected_pair[1], source_b]
            print(
                "[AI_MODE] preview selected-style mismatch -> regenerate "
                f"selected={','.join(sorted(selected_styles)) or 'unknown'} target={style_id}"
            )
        source_a, source_b = self._resolve_ai_source_pair()
        ai_a, ai_b = self._generate_ai_variants(
            source_a=source_a,
            source_b=source_b,
            style_id=style_id,
            purpose="preview",
            remote_allowed=True,
        )
        print(
            "[AI_MODE] preview map 4641 slots=LT:orig1 RT:ai1 LB:ai2 RB:orig2 "
            f"style={style_id}"
        )
        return [source_a, ai_a, ai_b, source_b]

    def _build_final_print_ai_4641(
        self,
        progress_cb: Optional[Callable[[int, str, str], None]] = None,
    ) -> tuple[Image.Image, Path, int, int]:
        self._emit_compose_progress(progress_cb, 8, "AI 합성 준비중", "Preparing AI composition")
        style_id = self._resolve_ai_style_id()
        selected_pair = self._resolve_ai_selected_pair()
        if (
            selected_pair is not None
            and self._is_ai_generated_path(selected_pair[0])
            and self._is_ai_generated_path(selected_pair[1])
        ):
            selected_styles = self._ai_pair_style_ids(selected_pair)
            if style_id in selected_styles and len(selected_styles) == 1:
                source_a, source_b = self._resolve_ai_original_pair()
                ai_a, ai_b = selected_pair
                self._emit_compose_progress(progress_cb, 74, "선택 AI 반영중", "Applying selected AI photos")
                print(
                    "[AI_MODE] reuse selected ai purpose=final "
                    f"style={style_id} ai1={ai_a.name} ai2={ai_b.name}"
                )
            else:
                print(
                    "[AI_MODE] selected-style mismatch -> regenerate final "
                    f"selected={','.join(sorted(selected_styles)) or 'unknown'} target={style_id}"
                )
                source_a, source_b = self._resolve_ai_source_pair()
                ai_a, ai_b = self._generate_ai_variants(
                    source_a=source_a,
                    source_b=source_b,
                    style_id=style_id,
                    purpose="final",
                    remote_allowed=True,
                    progress_cb=progress_cb,
                )
        else:
            source_a, source_b = self._resolve_ai_source_pair()
            ai_a, ai_b = self._generate_ai_variants(
                source_a=source_a,
                source_b=source_b,
                style_id=style_id,
                purpose="final",
                remote_allowed=True,
                progress_cb=progress_cb,
            )

        self._emit_compose_progress(progress_cb, 88, "프레임 합성중", "Composing frame")
        mapped_paths = [source_a, ai_a, ai_b, source_b]
        composed, slot_count, copies_per_page, frame2_path, used_slots = self.build_confirm_image_static(
            layout_id=self.layout_id or AI_LAYOUT_ID,
            frame_index=self.frame_index,
            selected_paths=mapped_paths,
            is_gray=self.is_gray,
            flip_horizontal=self.flip_horizontal,
        )
        print(
            "[AI_MODE] compose 4641 slots=LT:orig1 RT:ai1 LB:ai2 RB:orig2 "
            f"style={style_id} source_a={source_a.name} source_b={source_b.name}"
        )
        if self.qr_enabled:
            self._emit_compose_progress(progress_cb, 95, "QR 배치중", "Applying QR")
            composed = self._apply_qr_overlay_to_print(composed, used_slots)
        self._emit_compose_progress(progress_cb, 99, "합성 마무리", "Finalizing composition")
        return composed, frame2_path, slot_count, copies_per_page

    def build_final_print(
        self,
        progress_cb: Optional[Callable[[int, str, str], None]] = None,
    ) -> tuple[Image.Image, Path, int, int]:
        if not self.layout_id:
            raise RuntimeError("layout_id missing")
        if self._is_ai_mode_4641():
            return self._build_final_print_ai_4641(progress_cb=progress_cb)
        self._emit_compose_progress(progress_cb, 22, "합성 준비중", "Preparing composition")
        composed, slot_count, copies_per_page, frame2_path, used_slots = self.build_confirm_image_static(
            layout_id=self.layout_id,
            frame_index=self.frame_index,
            selected_paths=self.selected_print_paths,
            is_gray=self.is_gray,
            flip_horizontal=self.flip_horizontal,
        )
        self._emit_compose_progress(progress_cb, 82, "프레임 합성 완료", "Frame composition done")
        if self.qr_enabled:
            self._emit_compose_progress(progress_cb, 92, "QR 배치중", "Applying QR")
            composed = self._apply_qr_overlay_to_print(composed, used_slots)
        self._emit_compose_progress(progress_cb, 99, "합성 마무리", "Finalizing composition")
        return composed, frame2_path, slot_count, copies_per_page


class AppThankYouScreen(ThankYouScreen):
    AUTO_BACK_MS = 20000
    QR_RECT = (775, 350, 370, 370)
    CANDIDATE_DIR_NAMES = [
        "12_Thank_you",
        "12_thank_you",
        "Thank_you",
        "thank_you",
    ]

    def __init__(
        self,
        main_window: "KioskMainWindow",
        image_path: Path,
        gif_rect: tuple[int, int, int, int],
    ) -> None:
        resolved_image = self._resolve_thank_you_image(image_path)
        super().__init__(main_window, resolved_image)
        self._gif_rect = gif_rect
        self._gif_label = QLabel(self)
        self._gif_label.setAlignment(ALIGN_CENTER)
        self._gif_label.setStyleSheet("QLabel { background: transparent; }")
        self._gif_label.setAttribute(WA_TRANSPARENT, True)
        self._gif_movie: Optional[QMovie] = None
        self._thankyou_token = 0
        self._active_token = 0
        self._update_gif_geometry()
        self._update_qr_geometry()
        self._gif_label.hide()

    @classmethod
    def _resolve_thank_you_image(cls, fallback_path: Path) -> Path:
        base_dir = ROOT_DIR / "assets" / "ui"
        candidate_dirs = [base_dir / name for name in cls.CANDIDATE_DIR_NAMES if (base_dir / name).is_dir()]

        def _rank(path: Path) -> tuple[int, str]:
            stem = path.stem.lower()
            if "thank" in stem or "you" in stem:
                return (0, path.name.lower())
            return (1, path.name.lower())

        for folder in candidate_dirs:
            pngs = sorted([p for p in folder.glob("*.png") if p.is_file()], key=_rank)
            if pngs:
                print(f"[THANKYOU] asset={pngs[0]}")
                return pngs[0]

        print(f"[THANKYOU] asset={fallback_path}")
        return fallback_path

    def _update_gif_geometry(self) -> None:
        self._gif_label.setGeometry(self.design_rect_to_widget(self._gif_rect))
        if self._gif_movie is not None:
            self._gif_movie.setScaledSize(self._gif_label.size())

    def _update_qr_geometry(self) -> None:
        if hasattr(self, "_qr_label"):
            self._qr_label.setGeometry(self.design_rect_to_widget(self.QR_RECT))

    def _stop_gif(self) -> None:
        if self._gif_movie is not None:
            try:
                self._gif_movie.stop()
            except Exception:
                pass
            self._gif_label.setMovie(None)
            self._gif_movie.deleteLater()
            self._gif_movie = None
        self._gif_label.hide()

    def _start_gif(self) -> None:
        self._stop_gif()
        session = self.main_window.get_active_session() if hasattr(self.main_window, "get_active_session") else None
        gif_path: Optional[Path] = None
        if session is not None:
            candidate = session.session_dir / "share" / "video.gif"
            if candidate.is_file():
                gif_path = candidate
        if gif_path is None:
            print("[THANKYOU] gif none")
            return
        movie = QMovie(str(gif_path))
        if not movie.isValid():
            print(f"[THANKYOU] gif invalid path={gif_path}")
            movie.deleteLater()
            return
        movie.setScaledSize(self._gif_label.size())
        self._gif_movie = movie
        self._gif_label.setMovie(movie)
        self._gif_label.show()
        movie.start()
        print(f"[THANKYOU] gif start path={gif_path}")

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._thankyou_token += 1
        token = self._thankyou_token
        self._active_token = token
        session = self.main_window.get_active_session() if hasattr(self.main_window, "get_active_session") else None
        session_id = session.session_id if session is not None else "none"
        qr_path: Optional[Path] = None
        if session is not None:
            raw_qr = getattr(session, "qr_path", None)
            if isinstance(raw_qr, Path) and raw_qr.is_file():
                qr_path = raw_qr
            elif isinstance(raw_qr, str) and raw_qr.strip() and Path(raw_qr).is_file():
                qr_path = Path(raw_qr)
            if qr_path is None:
                raw_alt = getattr(session, "qr_png_path", None)
                if isinstance(raw_alt, str) and raw_alt.strip() and Path(raw_alt).is_file():
                    qr_path = Path(raw_alt)
        self.set_qr_path(qr_path)
        print(f"[THANKYOU] enter session={session_id}")
        print(f"[THANKYOU] auto -> start in {self.AUTO_BACK_MS}ms")
        QTimer.singleShot(self.AUTO_BACK_MS, lambda t=token: self._thankyou_auto_back(t))
        self._stop_gif()

    def hideEvent(self, event):  # noqa: N802
        self._thankyou_token += 1
        self._active_token = 0
        self._stop_gif()
        super().hideEvent(event)

    def _thankyou_auto_back(self, token: int) -> None:
        if token != self._thankyou_token or token != self._active_token:
            return
        if not self.isVisible():
            return
        print("[THANKYOU] auto -> start")
        if hasattr(self.main_window, "go_start_from_thankyou"):
            self.main_window.go_start_from_thankyou(reason="auto")
        else:
            self.main_window.goto_screen("start")

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._update_gif_geometry()
        self._update_qr_geometry()


class AppHowManyPrintsScreen(HowManyPrintsScreen):
    NUMBER_RECT = (816, 385, 296, 315)

    def __init__(self, main_window) -> None:
        super().__init__(main_window)
        self.print_count = 2
        self.count_label = QLabel(self)
        self.count_label.setAlignment(ALIGN_CENTER)
        self.count_label.setStyleSheet(
            "QLabel { color: #2A1323; background: transparent; font-size: 140px; font-weight: 700; }"
        )
        self.count_label.setAttribute(WA_TRANSPARENT, True)
        self._layout_widgets()
        self.update_print_count_ui()

    def _normalize_even(self, value: int) -> int:
        normalized = max(2, min(10, int(value)))
        if normalized % 2 != 0:
            normalized -= 1
        if normalized < 2:
            normalized = 2
        return normalized

    def _layout_widgets(self) -> None:
        self.count_label.setGeometry(self.design_rect_to_widget(self.NUMBER_RECT))
        self.count_label.raise_()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()
        self.update_print_count_ui()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._layout_widgets()
        self.update_print_count_ui()

    def update_print_count_ui(self) -> None:
        self.count_label.setText(str(int(self.print_count)))

    def set_print_count(self, value: int) -> None:
        self.print_count = self._normalize_even(value)
        self.update_print_count_ui()

    def adjust_print_count(self, direction: int) -> tuple[int, int]:
        old_value = int(self.print_count)
        if direction > 0:
            new_value = min(10, old_value + 2)
        elif direction < 0:
            new_value = max(2, old_value - 2)
        else:
            new_value = old_value
        self.print_count = self._normalize_even(new_value)
        self.update_print_count_ui()
        return old_value, int(self.print_count)


class AppPaymentMethodScreen(PaymentMethodScreen):
    NEXT_RECT = (1750, 935, 121, 110)
    NOTICE_RECT = (450, 430, 1020, 180)
    METHOD_ROI = (0, 280, 1920, 540)

    def __init__(self, main_window) -> None:
        super().__init__(main_window)
        self._base_dir = ROOT_DIR / "assets" / "ui" / "5_Select_a_payment_Method"
        self._next_path = self._base_dir / "btn_next.png"
        self._enabled: dict[str, bool] = dict(DEFAULT_PAYMENT_METHODS)
        self.current_mode = "cashcard_mode"
        self.payment_mode = "cashcard"
        self.method_regions: dict[str, QRect] = {}
        self._main_path: Optional[Path] = None
        self._selected_paths: dict[str, Path] = {}
        self._pix_selected: dict[str, QPixmap] = {}
        self.payment_method: Optional[str] = None

        self._bg_label = QLabel(self)
        self._bg_label.setAlignment(ALIGN_CENTER)
        self._bg_label.setScaledContents(True)
        self._bg_label.setAttribute(WA_TRANSPARENT, True)

        self.next_label = QLabel(self._bg_label)
        self.next_label.setAlignment(ALIGN_CENTER)
        self.next_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        self.next_label.setAttribute(WA_TRANSPARENT, True)
        self.next_label.hide()

        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._hide_notice)
        self._notice_label = QLabel("", self)
        self._notice_label.setAlignment(ALIGN_CENTER)
        self._notice_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0, 0, 0, 180); "
            "font-size: 42px; font-weight: 700; border: 2px solid rgba(255,255,255,150); }"
        )
        self._notice_label.hide()

        self._pix_main = QPixmap()
        self._pix_next = self._load_pixmap(self._next_path, "next")
        self.apply_payment_methods(self._enabled)
        self._layout_widgets()

    @staticmethod
    def _normalize_enabled(enabled: Optional[dict]) -> dict[str, bool]:
        def _to_bool(value: object, default: bool) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return int(value) != 0
            if isinstance(value, str):
                text = value.strip().lower()
                if text in {"1", "true", "yes", "on", "y", "t"}:
                    return True
                if text in {"0", "false", "no", "off", "n", "f", ""}:
                    return False
            return bool(default)

        normalized = dict(DEFAULT_PAYMENT_METHODS)
        if isinstance(enabled, dict):
            for key in ("cash", "card", "coupon"):
                normalized[key] = _to_bool(enabled.get(key), bool(normalized[key]))
        if not (normalized["cash"] or normalized["card"] or normalized["coupon"]):
            normalized["cash"] = True
        return normalized

    @staticmethod
    def _resolve_mode(enabled: dict[str, bool]) -> str:
        cash = bool(enabled.get("cash", False))
        card = bool(enabled.get("card", False))
        coupon = bool(enabled.get("coupon", False))
        if cash and card and coupon:
            return "cashcardcoupon_mode"
        if cash and card:
            return "cashcard_mode"
        if cash and coupon:
            return "cashcoupon_mode"
        if card and coupon:
            return "cardcoupon_mode"
        if cash:
            return "cash_only"
        if card:
            return "card_only"
        if coupon:
            return "coupon_only"
        return "cash_only"

    @staticmethod
    def _resolve_payment_mode_name(enabled: dict[str, bool]) -> str:
        cash = bool(enabled.get("cash", False))
        card = bool(enabled.get("card", False))
        coupon = bool(enabled.get("coupon", False))
        if cash and card and coupon:
            return "cashcardcoupon"
        if cash and card:
            return "cashcard"
        if cash and coupon:
            return "cashcoupon"
        if card and coupon:
            return "cardcoupon"
        if cash:
            return "cashonly"
        if coupon:
            return "coupononly"
        if card:
            return "cardonly"
        return "cashonly"

    def _pick_asset_path(self, candidates: list[str]) -> Path:
        for rel in candidates:
            path = self._base_dir / rel
            if path.is_file():
                return path
        return self._base_dir / candidates[0]

    def _resolve_assets(self, mode: str) -> tuple[Path, dict[str, Path]]:
        if mode == "cashcardcoupon_mode":
            main_path = self._pick_asset_path(
                ["cashcardcoupon_mode/cashcardcouponmode_main.png", "cashcard_mode/cashcardmode_main.png"]
            )
            selected = {
                "cash": self._pick_asset_path(
                    ["cashcardcoupon_mode/ifcashcardcouponmode_cash.png", "cashcard_mode/ifcashcardmode_cash.png"]
                ),
                "card": self._pick_asset_path(
                    ["cashcardcoupon_mode/ifcashcardcouponmode_card.png", "cashcard_mode/ifcashcardmode_card.png"]
                ),
                "coupon": self._pick_asset_path(
                    [
                        "cashcardcoupon_mode/ifcashcardcouponmode_coupon.png",
                        "cashcoupon_mode/ifcashcouponmode_coupon.png",
                        "cardcoupon_mode/ifcardcouponmode_coupon.png",
                        "Paycoupon/coupon_main.png",
                    ]
                ),
            }
            return main_path, selected

        if mode == "cashcard_mode":
            main_path = self._pick_asset_path(["cashcard_mode/cashcardmode_main.png"])
            selected = {
                "cash": self._pick_asset_path(["cashcard_mode/ifcashcardmode_cash.png"]),
                "card": self._pick_asset_path(["cashcard_mode/ifcashcardmode_card.png"]),
            }
            return main_path, selected

        if mode == "cashcoupon_mode":
            main_path = self._pick_asset_path(
                ["cashcoupon_mode/cashcouponmode_main.png", "cashcardcoupon_mode/cashcardcouponmode_main.png"]
            )
            selected = {
                "cash": self._pick_asset_path(
                    ["cashcoupon_mode/ifcashcouponmode_cash.png", "cashcardcoupon_mode/ifcashcardcouponmode_cash.png"]
                ),
                "coupon": self._pick_asset_path(
                    [
                        "cashcoupon_mode/ifcashcouponmode_coupon.png",
                        "cashcardcoupon_mode/ifcashcardcouponmode_coupon.png",
                        "Paycoupon/coupon_main.png",
                    ]
                ),
            }
            return main_path, selected

        if mode == "cardcoupon_mode":
            main_path = self._pick_asset_path(
                ["cardcoupon_mode/cardcouponmode_main.png", "cashcardcoupon_mode/cashcardcouponmode_main.png"]
            )
            selected = {
                "card": self._pick_asset_path(
                    ["cardcoupon_mode/ifcardcouponmode_card.png", "cashcardcoupon_mode/ifcashcardcouponmode_card.png"]
                ),
                "coupon": self._pick_asset_path(
                    [
                        "cardcoupon_mode/ifcardcouponmode_coupon.png",
                        "cashcardcoupon_mode/ifcashcardcouponmode_coupon.png",
                        "Paycoupon/coupon_main.png",
                    ]
                ),
            }
            return main_path, selected

        if mode == "card_only":
            main_path = self._pick_asset_path(
                ["Paycardmain/card_main.png", "cardcoupon_mode/cardcouponmode_main.png"]
            )
            selected = {"card": main_path}
            return main_path, selected

        if mode == "coupon_only":
            main_path = self._pick_asset_path(
                ["Paycoupon/coupon_main.png", "cashcoupon_mode/cashcouponmode_main.png"]
            )
            selected = {
                "coupon": self._pick_asset_path(
                    ["Paycoupon/coupon_main.png", "cashcoupon_mode/ifcashcouponmode_coupon.png"]
                )
            }
            return main_path, selected

        main_path = self._pick_asset_path(
            ["Paycashmain/Cash_main.png", "cashcard_mode/cashcardmode_main.png"]
        )
        selected = {
            "cash": self._pick_asset_path(
                ["Paycashmain/Cash_main.png", "cashcard_mode/ifcashcardmode_cash.png"]
            )
        }
        return main_path, selected

    def _load_pixmap(self, path: Path, label: str) -> QPixmap:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            print(f"[PAYMENT] {label} image not found: {path}")
        return pixmap

    def _set_background(self, pixmap: QPixmap) -> None:
        if not pixmap.isNull():
            self._image = pixmap
            self._bg_label.setPixmap(pixmap)
        else:
            self._bg_label.setPixmap(QPixmap())
        self.update()

    def _layout_widgets(self) -> None:
        self._bg_label.setGeometry(self.design_rect_to_widget((0, 0, DESIGN_WIDTH, DESIGN_HEIGHT)))
        self._notice_label.setGeometry(self.design_rect_to_widget(self.NOTICE_RECT))
        next_rect = self.design_rect_to_widget(self.NEXT_RECT)
        self.next_label.setGeometry(next_rect)
        if not self._pix_next.isNull():
            scaled = self._pix_next.scaled(self.next_label.size(), KEEP_ASPECT, SMOOTH_TRANSFORM)
            self.next_label.setPixmap(scaled)
        self.next_label.raise_()
        self._notice_label.raise_()
        self._overlay.raise_()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()

    def _hide_notice(self) -> None:
        self._notice_label.hide()

    def show_notice(self, message: str, duration_ms: int = 1000) -> None:
        self._notice_label.setText(message)
        self._notice_label.show()
        self._notice_label.raise_()
        self._notice_timer.start(max(200, int(duration_ms)))

    def _update_next_overlay(self) -> None:
        if self.payment_method:
            self.next_label.show()
        else:
            self.next_label.hide()

    def is_method_enabled(self, method: str) -> bool:
        return bool(self._enabled.get((method or "").strip().lower(), False))

    def get_enabled_map(self) -> dict[str, bool]:
        return dict(self._enabled)

    def _default_method(self) -> str:
        if self._enabled.get("cash"):
            return "cash"
        if self._enabled.get("card"):
            return "card"
        if self._enabled.get("coupon"):
            return "coupon"
        return "cash"

    def get_main_asset_path(self) -> Optional[Path]:
        return self._main_path

    def get_selected_asset_path(self, method: str) -> Optional[Path]:
        key = (method or "").strip().lower()
        path = self._selected_paths.get(key)
        if isinstance(path, Path) and path.is_file():
            return path
        return None

    def get_mode(self) -> str:
        return str(self.current_mode)

    def get_payment_mode(self) -> str:
        return str(self.payment_mode)

    def _build_method_regions(self) -> None:
        x, y, w, h = self.METHOD_ROI
        self.method_regions = {}

        if self.payment_mode == "cashcardcoupon":
            self.method_regions["cash"] = QRect(0, y, 640, h)
            self.method_regions["card"] = QRect(640, y, 640, h)
            self.method_regions["coupon"] = QRect(1280, y, 640, h)
            return

        left = QRect(0, y, 960, h)
        right = QRect(960, y, 960, h)
        full = QRect(x, y, w, h)
        if self.payment_mode == "cashcard":
            self.method_regions["cash"] = left
            self.method_regions["card"] = right
        elif self.payment_mode == "cashcoupon":
            self.method_regions["cash"] = left
            self.method_regions["coupon"] = right
        elif self.payment_mode == "cardcoupon":
            self.method_regions["card"] = left
            self.method_regions["coupon"] = right
        elif self.payment_mode == "coupononly":
            self.method_regions["coupon"] = full
        elif self.payment_mode == "cardonly":
            self.method_regions["card"] = full
        else:
            self.method_regions["cash"] = full

    def pick_method_at(self, x: int, y: int) -> Optional[str]:
        for method, rect in self.method_regions.items():
            if not self.is_method_enabled(method):
                continue
            if rect.contains(int(x), int(y)):
                return method
        return None

    def detect_method_rects(
        self,
        roi: tuple[int, int, int, int] = (0, 250, 1920, 850),
        thr: int = 18,
        pad: int = 16,
    ) -> dict[str, Optional[list[int]]]:
        result: dict[str, Optional[list[int]]] = {"cash": None, "card": None, "coupon": None}
        main_path = self.get_main_asset_path()
        if main_path is None or not main_path.is_file():
            return result
        for method in ("cash", "card", "coupon"):
            if not self.is_method_enabled(method):
                continue
            selected = self.get_selected_asset_path(method)
            if selected is None:
                continue
            result[method] = detect_button_bbox(main_path, selected, roi=roi, thr=thr, pad=pad)
        return result

    def apply_payment_methods(self, enabled: Optional[dict]) -> None:
        normalized = self._normalize_enabled(enabled)
        self._enabled = normalized
        self.payment_mode = self._resolve_payment_mode_name(normalized)
        self.current_mode = self._resolve_mode(normalized)
        self._main_path, self._selected_paths = self._resolve_assets(self.current_mode)
        self._pix_main = self._load_pixmap(self._main_path, "main")
        self._pix_selected = {
            key: self._load_pixmap(path, key) for key, path in self._selected_paths.items()
        }
        current = self.payment_method if self.payment_method and self.is_method_enabled(self.payment_method) else None
        self._set_background(self._pix_main)
        self.payment_method = None
        self.set_payment_method(current or self._default_method())
        self._build_method_regions()

    def set_payment_method(self, method: Optional[str]) -> None:
        normalized = (method or "").strip().lower()
        if normalized and self.is_method_enabled(normalized):
            self.payment_method = normalized
            selected_pix = self._pix_selected.get(normalized)
            if selected_pix is not None and not selected_pix.isNull():
                self._set_background(selected_pix)
            else:
                self._set_background(self._pix_main)
        else:
            self.payment_method = None
            self._set_background(self._pix_main)
        self._update_next_overlay()

    def set_default_method(self) -> None:
        default_method = self._default_method()
        self.set_payment_method(default_method)
        print(f"[PAYMENT] method={self.payment_method or default_method} (default)")

    def set_default_cash(self) -> None:
        self.set_default_method()


class PayCashScreen(ImageScreen):
    BACK_RECT = (77, 939, 100, 100)
    PAYMENT_RECT = (1181, 445, 250, 88)
    INSERTED_RECT = (1181, 582, 250, 88)
    NOTICE_RECT = (450, 430, 1020, 180)

    def __init__(self, main_window: "KioskMainWindow") -> None:
        path = ROOT_DIR / "assets" / "ui" / "5_Select_a_payment_Method" / "Paycashmain" / "Cash_main.png"
        super().__init__(main_window, "pay_cash", path)
        self._bg_label = QLabel(self)
        self._bg_label.setAlignment(ALIGN_CENTER)
        self._bg_label.setScaledContents(True)
        self._bg_label.setAttribute(WA_TRANSPARENT, True)

        value_style = (
            "QLabel { color: #111; background: transparent; font-size: 58px; font-weight: 700; }"
        )
        self.payment_label = QLabel("0", self._bg_label)
        self.payment_label.setAlignment(ALIGN_CENTER)
        self.payment_label.setStyleSheet(value_style)
        self.payment_label.setAttribute(WA_TRANSPARENT, True)

        self.inserted_label = QLabel("0", self._bg_label)
        self.inserted_label.setAlignment(ALIGN_CENTER)
        self.inserted_label.setStyleSheet(value_style)
        self.inserted_label.setAttribute(WA_TRANSPARENT, True)

        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._hide_notice)
        self._notice_label = QLabel("", self)
        self._notice_label.setAlignment(ALIGN_CENTER)
        self._notice_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0, 0, 0, 180); "
            "font-size: 42px; font-weight: 700; border: 2px solid rgba(255,255,255,150); }"
        )
        self._notice_label.hide()
        self._layout_widgets()

    def _layout_widgets(self) -> None:
        self._bg_label.setGeometry(self.design_rect_to_widget((0, 0, DESIGN_WIDTH, DESIGN_HEIGHT)))
        self.payment_label.setGeometry(self.design_rect_to_widget(self.PAYMENT_RECT))
        self.inserted_label.setGeometry(self.design_rect_to_widget(self.INSERTED_RECT))
        self._notice_label.setGeometry(self.design_rect_to_widget(self.NOTICE_RECT))
        self._bg_label.setPixmap(self._background)
        self._notice_label.raise_()
        self._overlay.raise_()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._layout_widgets()

    def set_amounts(self, required_amount: int, inserted_amount: int) -> None:
        self.payment_label.setText(money_fmt(required_amount))
        self.inserted_label.setText(money_fmt(inserted_amount))

    def _hide_notice(self) -> None:
        self._notice_label.hide()

    def show_notice(self, message: str, duration_ms: int = 1000) -> None:
        self._notice_label.setText(message)
        self._notice_label.show()
        self._notice_label.raise_()
        self._notice_timer.start(max(200, int(duration_ms)))


class CouponRemainingMethodScreen(ImageScreen):
    CASH_RECT = (519, 377, 369, 376)
    CARD_RECT = (1012, 377, 369, 376)
    BACK_RECT = (77, 939, 100, 100)
    NOTICE_RECT = (450, 430, 1020, 180)

    def __init__(self, main_window: "KioskMainWindow") -> None:
        path = (
            ROOT_DIR
            / "assets"
            / "ui"
            / "5_Select_a_payment_Method"
            / "Paycoupon"
            / "Coupon_if_remaining_amount _select_remining payment_method.png"
        )
        super().__init__(main_window, "coupon_remaining_method", path)
        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._hide_notice)
        self._notice_label = QLabel("", self)
        self._notice_label.setAlignment(ALIGN_CENTER)
        self._notice_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0, 0, 0, 180); "
            "font-size: 42px; font-weight: 700; border: 2px solid rgba(255,255,255,150); }"
        )
        self._notice_label.hide()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._notice_label.setGeometry(self.design_rect_to_widget(self.NOTICE_RECT))

    def _hide_notice(self) -> None:
        self._notice_label.hide()

    def show_notice(self, message: str, duration_ms: int = 1000) -> None:
        self._notice_label.setText(message)
        self._notice_label.show()
        self._notice_label.raise_()
        self._notice_timer.start(max(200, int(duration_ms)))


class PayCashRemainingScreen(ImageScreen):
    BACK_RECT = (77, 940, 100, 100)
    PAYMENT_RECT = (1181, 382, 250, 88)
    COUPON_RECT = (1181, 519, 250, 88)
    REMAINING_RECT = (1181, 656, 250, 87)
    NOTICE_RECT = (450, 430, 1020, 180)

    def __init__(self, main_window: "KioskMainWindow") -> None:
        path = (
            ROOT_DIR
            / "assets"
            / "ui"
            / "5_Select_a_payment_Method"
            / "Paycashmain"
            / "Cash_if_remaining_amount.png"
        )
        super().__init__(main_window, "pay_cash_remaining", path)
        self._bg_label = QLabel(self)
        self._bg_label.setAlignment(ALIGN_CENTER)
        self._bg_label.setScaledContents(True)
        self._bg_label.setAttribute(WA_TRANSPARENT, True)

        value_style = (
            "QLabel { color: #111; background: transparent; font-size: 56px; font-weight: 700; }"
        )
        self.payment_label = QLabel("0", self._bg_label)
        self.payment_label.setAlignment(ALIGN_CENTER)
        self.payment_label.setStyleSheet(value_style)
        self.payment_label.setAttribute(WA_TRANSPARENT, True)

        self.coupon_label = QLabel("0", self._bg_label)
        self.coupon_label.setAlignment(ALIGN_CENTER)
        self.coupon_label.setStyleSheet(value_style)
        self.coupon_label.setAttribute(WA_TRANSPARENT, True)

        self.remaining_label = QLabel("0", self._bg_label)
        self.remaining_label.setAlignment(ALIGN_CENTER)
        self.remaining_label.setStyleSheet(value_style)
        self.remaining_label.setAttribute(WA_TRANSPARENT, True)

        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._hide_notice)
        self._notice_label = QLabel("", self)
        self._notice_label.setAlignment(ALIGN_CENTER)
        self._notice_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0, 0, 0, 180); "
            "font-size: 42px; font-weight: 700; border: 2px solid rgba(255,255,255,150); }"
        )
        self._notice_label.hide()
        self._layout_widgets()

    def _layout_widgets(self) -> None:
        self._bg_label.setGeometry(self.design_rect_to_widget((0, 0, DESIGN_WIDTH, DESIGN_HEIGHT)))
        self.payment_label.setGeometry(self.design_rect_to_widget(self.PAYMENT_RECT))
        self.coupon_label.setGeometry(self.design_rect_to_widget(self.COUPON_RECT))
        self.remaining_label.setGeometry(self.design_rect_to_widget(self.REMAINING_RECT))
        self._notice_label.setGeometry(self.design_rect_to_widget(self.NOTICE_RECT))
        self._bg_label.setPixmap(self._background)
        self._notice_label.raise_()
        self._overlay.raise_()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._layout_widgets()

    def set_amounts(self, required_amount: int, coupon_value: int, inserted_amount: int) -> None:
        remaining = max(0, int(required_amount) - int(coupon_value) - int(inserted_amount))
        self.payment_label.setText(money_fmt(required_amount))
        self.coupon_label.setText(money_fmt(coupon_value))
        self.remaining_label.setText(money_fmt(remaining))

    def _hide_notice(self) -> None:
        self._notice_label.hide()

    def show_notice(self, message: str, duration_ms: int = 1000) -> None:
        self._notice_label.setText(message)
        self._notice_label.show()
        self._notice_label.raise_()
        self._notice_timer.start(max(200, int(duration_ms)))


class CouponInputScreen(ImageScreen):
    INPUT_RECT = (1024, 452, 538, 38)
    INPUT_LABEL_RECT = (1036, 448, 514, 46)
    NOTICE_RECT = (520, 790, 880, 120)
    INVALID_OVERLAY_RECT = (487, 399, 946, 281)
    INVALID_CANCEL_RECT = (875, 582, 164, 71)
    BTN_CANCEL_RECT = (1032, 684, 145, 57)
    BTN_CONFIRM_RECT = (1204, 682, 146, 61)
    BTN_BACK_RECT = (40, 900, 220, 220)
    KEY_RECTS = {
        "0": (824, 549, 64, 59),
        "1": (891, 549, 65, 59),
        "2": (959, 549, 64, 59),
        "3": (1026, 549, 65, 59),
        "4": (1093, 549, 65, 59),
        "5": (1161, 549, 65, 59),
        "6": (1228, 549, 65, 59),
        "7": (1296, 549, 65, 59),
        "8": (1363, 549, 65, 59),
        "9": (1431, 549, 64, 59),
        "backspace": (1498, 549, 65, 59),
    }

    def __init__(self, main_window: "KioskMainWindow") -> None:
        self._bg_path = self._resolve_background_path()
        super().__init__(main_window, "coupon_input", self._bg_path)
        self.coupon_buf = ""
        self.coupon_len = 6
        self._coupon_enabled = bool(DEFAULT_COUPON_SETTINGS["enabled"])
        self._accept_any_in_test = bool(DEFAULT_COUPON_SETTINGS["accept_any_in_test"])
        self._valid_codes = [str(code) for code in DEFAULT_COUPON_SETTINGS["valid_codes"]]
        self._submitting = False
        self._invalid_overlay_visible = False
        self._invalid_overlay_path = self._resolve_invalid_overlay_path()
        self._invalid_overlay_pixmap = QPixmap(str(self._invalid_overlay_path))
        if self._invalid_overlay_pixmap.isNull():
            print(f"[COUPON] invalid overlay image missing: {self._invalid_overlay_path}")

        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._hide_notice)
        self._notice_label = QLabel("", self)
        self._notice_label.setAlignment(ALIGN_CENTER)
        self._notice_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0, 0, 0, 185); "
            "font-size: 40px; font-weight: 700; border: 2px solid rgba(255,255,255,150); "
            "border-radius: 8px; }"
        )
        self._notice_label.hide()

        self._input_label = QLabel("", self)
        self._input_label.setAlignment(ALIGN_CENTER)
        self._input_label.setStyleSheet(
            "QLabel { background: transparent; color: #111111; "
            "font-family: Consolas, Arial; font-size: 30px; font-weight: 700; }"
        )
        self._input_label.setAttribute(WA_TRANSPARENT, True)

        self._invalid_overlay_label = QLabel(self)
        self._invalid_overlay_label.setAlignment(ALIGN_CENTER)
        self._invalid_overlay_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        self._invalid_overlay_label.setAttribute(WA_TRANSPARENT, True)
        if not self._invalid_overlay_pixmap.isNull():
            self._invalid_overlay_label.setPixmap(self._invalid_overlay_pixmap)
        self._invalid_overlay_label.hide()

        self.setFocusPolicy(STRONG_FOCUS)
        self._layout_widgets()
        self._update_coupon_display()

    @staticmethod
    def _resolve_background_path() -> Path:
        direct_candidates = [
            ROOT_DIR / "assets" / "ui" / "5_Select_a_payment_Method" / "Paycoupon" / "coupon_main.png",
            ROOT_DIR / "assets" / "ui" / "5_Select_a_payment_Method" / "cashcardcoupon_mode" / "cashcardcouponmode_main.png",
        ]
        for candidate in direct_candidates:
            if candidate.is_file():
                return candidate

        root = ROOT_DIR / "assets" / "ui"
        if root.is_dir():
            pngs = [p for p in root.rglob("*.png") if "coupon" in p.stem.lower()]
            if pngs:
                def _rank(path: Path) -> tuple[int, str]:
                    stem = path.stem.lower()
                    if "main" in stem:
                        return (0, path.name.lower())
                    return (1, path.name.lower())
                return sorted(pngs, key=_rank)[0]

        return ROOT_DIR / "assets" / "ui" / "5_Select_a_payment_Method" / "Paycoupon" / "coupon_main.png"

    @staticmethod
    def _resolve_invalid_overlay_path() -> Path:
        return (
            ROOT_DIR
            / "assets"
            / "ui"
            / "5_Select_a_payment_Method"
            / "Paycoupon"
            / "if_invalid_couponcode_warning.png"
        )

    def _load_coupon_settings(self) -> None:
        settings = (
            self.main_window.get_coupon_settings()
            if hasattr(self.main_window, "get_coupon_settings")
            else dict(DEFAULT_COUPON_SETTINGS)
        )
        self.coupon_len = 6
        self._coupon_enabled = bool(settings.get("enabled", True))
        self._accept_any_in_test = bool(settings.get("accept_any_in_test", True))
        raw_codes = settings.get("valid_codes", [])
        if isinstance(raw_codes, list):
            self._valid_codes = [str(code).strip() for code in raw_codes if str(code).strip()]
        else:
            self._valid_codes = []
        self._layout_widgets()
        self._update_coupon_display()

    def _layout_widgets(self) -> None:
        self._notice_label.setGeometry(self.design_rect_to_widget(self.NOTICE_RECT))
        self._input_label.setGeometry(self.design_rect_to_widget(self.INPUT_LABEL_RECT))
        self._invalid_overlay_label.setGeometry(self.design_rect_to_widget(self.INVALID_OVERLAY_RECT))
        if not self._invalid_overlay_pixmap.isNull():
            scaled = self._invalid_overlay_pixmap.scaled(
                self._invalid_overlay_label.size(),
                KEEP_ASPECT,
                SMOOTH_TRANSFORM,
            )
            self._invalid_overlay_label.setPixmap(scaled)

    def _format_coupon_display(self, digits: str) -> str:
        digits_only = "".join(ch for ch in str(digits) if ch.isdigit())
        digits_only = digits_only[:6]
        padded = digits_only.ljust(6, "*")
        return f"{padded[:3]}-{padded[3:6]}"

    def _update_coupon_display(self) -> None:
        self._input_label.setText(self._format_coupon_display(self.coupon_buf))

    def _hide_notice(self) -> None:
        self._notice_label.hide()

    def _show_notice(self, text: str, duration_ms: int = 1000) -> None:
        self._notice_label.setText(text)
        self._notice_label.show()
        self._notice_label.raise_()
        self._notice_timer.start(max(200, int(duration_ms)))

    def _on_digit(self, digit: str) -> None:
        if self._invalid_overlay_visible:
            return
        if self._submitting:
            return
        if len(self.coupon_buf) >= self.coupon_len:
            return
        self.coupon_buf += digit
        self._update_coupon_display()
        print(f"[COUPON] digit={digit} buf={self.coupon_buf} len={len(self.coupon_buf)}")

    def _on_clear(self) -> None:
        if self._invalid_overlay_visible:
            return
        if self._submitting:
            return
        self.coupon_buf = ""
        self._update_coupon_display()
        print("[COUPON] clear")

    def _on_backspace(self) -> None:
        if self._invalid_overlay_visible:
            return
        if self._submitting:
            return
        if self.coupon_buf:
            self.coupon_buf = self.coupon_buf[:-1]
        self._update_coupon_display()
        print(f"[COUPON] backspace buf={self.coupon_buf}")

    def _go_back(self) -> None:
        self._hide_invalid_overlay(clear_input=True)
        back_target = "payment_method"
        try:
            single_method = self.main_window._single_enabled_payment_method()
            if single_method == "coupon":
                # Avoid coupon-only loop: coupon_input -> payment_method -> coupon_input.
                back_target = "how_many_prints"
        except Exception:
            pass
        print(f"[COUPON] back -> {back_target}")
        self.main_window.goto_screen(back_target)

    @staticmethod
    def _point_in_rect(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
        rx, ry, rw, rh = [int(v) for v in rect]
        return rw > 0 and rh > 0 and rx <= x < (rx + rw) and ry <= y < (ry + rh)

    def _show_invalid_overlay(self) -> None:
        self._invalid_overlay_visible = True
        self._invalid_overlay_label.show()
        self._invalid_overlay_label.raise_()

    def _hide_invalid_overlay(self, clear_input: bool = False) -> None:
        self._invalid_overlay_visible = False
        self._invalid_overlay_label.hide()
        if clear_input:
            self.coupon_buf = ""
            self._update_coupon_display()

    def _pick_action_at(self, x: int, y: int) -> Optional[str]:
        if self._point_in_rect(x, y, self.BTN_BACK_RECT):
            return "back"
        if self._point_in_rect(x, y, self.BTN_CANCEL_RECT):
            return "cancel"
        if self._point_in_rect(x, y, self.BTN_CONFIRM_RECT):
            return "confirm"
        for key, rect in self.KEY_RECTS.items():
            if self._point_in_rect(x, y, rect):
                if key == "backspace":
                    return "backspace"
                return f"digit:{key}"
        return None

    def handle_design_click(self, x: int, y: int) -> bool:
        if self._invalid_overlay_visible:
            if self._point_in_rect(x, y, self.INVALID_CANCEL_RECT):
                self._hide_invalid_overlay(clear_input=True)
                print("[COUPON] invalid overlay cancel")
            return True

        action = self._pick_action_at(x, y)
        if action is None:
            return False
        if action.startswith("digit:"):
            self._on_digit(action.split(":", 1)[1])
            return True
        if action == "backspace":
            self._on_backspace()
            return True
        if action == "confirm":
            self.submit_coupon()
            return True
        if action in {"cancel", "back"}:
            self._go_back()
            return True
        return False

    def submit_coupon(self) -> None:
        if self._submitting:
            return
        if len(self.coupon_buf) != self.coupon_len:
            self._show_notice("쿠폰번호 6자리를 입력하세요", duration_ms=800)
            print(f"[COUPON] submit blocked len={len(self.coupon_buf)}")
            return
        if not self._coupon_enabled:
            print("[COUPON] fail disabled")
            self._show_notice("쿠폰 사용이 비활성화되었습니다", duration_ms=1000)
            self.coupon_buf = ""
            self._update_coupon_display()
            return

        code = self.coupon_buf
        print(f"[COUPON] confirm code={code}")
        self._submitting = True
        admin_settings = getattr(self.main_window, "admin_settings", {})
        test_mode = bool(admin_settings.get("test_mode", False)) if isinstance(admin_settings, dict) else False
        required = int(getattr(self.main_window, "current_required_amount", 0) or 0)
        if required <= 0 and hasattr(self.main_window, "_refresh_required_amount"):
            try:
                required = int(self.main_window._refresh_required_amount())
            except Exception:
                required = 0

        server_checked = False
        server_valid = False
        server_amount = 0
        server_reason = ""
        if hasattr(self.main_window, "_verify_coupon_with_server"):
            try:
                server_result = self.main_window._verify_coupon_with_server(code, required)
                if isinstance(server_result, dict):
                    server_checked = bool(server_result.get("checked", False))
                    server_valid = bool(server_result.get("valid", False))
                    server_amount = int(server_result.get("coupon_amount", 0) or 0)
                    server_reason = str(server_result.get("reason", "") or "").strip()
            except Exception as exc:
                print(f"[COUPON] server check exception: {exc}")

        if server_checked:
            if server_valid:
                print(f"[COUPON] ok(server) code={code} amount={server_amount} required={required}")
                if hasattr(self.main_window, "_handle_coupon_success"):
                    self.main_window._handle_coupon_success(code, server_amount)
                else:
                    self.main_window.goto_screen("payment_complete_success")
                self._submitting = False
                return
            reason_msg = {
                "NOT_FOUND": "등록되지 않은 쿠폰입니다",
                "USED": "이미 사용된 쿠폰입니다",
                "EXPIRED": "만료된 쿠폰입니다",
                "INVALID_FORMAT": "쿠폰 형식이 올바르지 않습니다",
                "DEVICE_LOCKED": "장치가 잠겨 쿠폰 검증이 불가합니다",
            }.get(server_reason, "쿠폰이 올바르지 않습니다")
            print(f"[COUPON] fail(server) code={code} reason={server_reason}")
            self._show_notice(reason_msg, duration_ms=1200)
            self.coupon_buf = ""
            self._update_coupon_display()
            self._show_invalid_overlay()
            self._submitting = False
            return

        # If server-coupon environment is configured, do not fall back to local-only
        # codes when server check is unavailable. This prevents kiosk-side coupon
        # acceptance that later fails during /sales/complete sync.
        server_configured = False
        try:
            if hasattr(self.main_window, "_coupon_check_url") and hasattr(self.main_window, "_build_kiosk_api_auth_headers"):
                _ = self.main_window._coupon_check_url()
                _ = self.main_window._build_kiosk_api_auth_headers()
                server_configured = True
        except Exception:
            server_configured = False
        if server_configured and not test_mode:
            print("[COUPON] server unavailable -> block local fallback")
            self._show_notice("쿠폰 서버 통신 오류입니다. 잠시 후 다시 시도해주세요", duration_ms=1300)
            self.coupon_buf = ""
            self._update_coupon_display()
            self._show_invalid_overlay()
            self._submitting = False
            return

        is_ok = False
        coupon_value = 0
        if test_mode and self._accept_any_in_test:
            is_ok = True
            coupon_value = required if required > 0 else 0
        elif code in self._valid_codes:
            is_ok = True
            if hasattr(self.main_window, "_resolve_coupon_value"):
                try:
                    coupon_value = int(self.main_window._resolve_coupon_value(code))
                except Exception:
                    coupon_value = 0

        if is_ok:
            print("[COUPON] ok(local) -> apply coupon flow")
            if hasattr(self.main_window, "_handle_coupon_success"):
                self.main_window._handle_coupon_success(code, coupon_value)
            else:
                self.main_window.goto_screen("payment_complete_success")
            self._submitting = False
            return

        print("[COUPON] fail(local) -> show invalid overlay")
        self._show_notice("쿠폰이 올바르지 않습니다", duration_ms=1000)
        self.coupon_buf = ""
        self._update_coupon_display()
        self._show_invalid_overlay()
        self._submitting = False

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.setFocus()
        self._submitting = False
        self._load_coupon_settings()
        self.coupon_buf = ""
        self._update_coupon_display()
        self._hide_invalid_overlay(clear_input=False)
        self._hide_notice()
        print("[COUPON] enter")

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()


class AppPaymentCompleteSuccessScreen(StaticImageScreen):
    AUTO_MS = 1200
    CANDIDATE_DIR_NAMES = [
        "6_Payment_Completed",
        "6_payment_completed",
        "6_Payment_complete",
        "6_payment_complete",
        "6_Payment_Completed_Success",
        "6_payment_complete_success",
    ]

    def __init__(self, main_window) -> None:
        self._asset_path = self._resolve_success_asset_path()
        super().__init__(
            main_window,
            "payment_complete_success",
            self._asset_path,
            missing_text="Payment complete",
        )
        self._entered_token = 0
        self._active_token = 0
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._on_auto_timer)

    @classmethod
    def _resolve_success_asset_path(cls) -> Path:
        base = ROOT_DIR / "assets" / "ui"
        dirs = [base / name for name in cls.CANDIDATE_DIR_NAMES if (base / name).is_dir()]

        def _rank(path: Path) -> tuple[int, str]:
            name = path.stem.lower()
            if "success" in name:
                return (0, path.name.lower())
            if "completed" in name:
                return (1, path.name.lower())
            if "complete" in name:
                return (2, path.name.lower())
            return (3, path.name.lower())

        for folder in dirs:
            pngs = sorted([p for p in folder.glob("*.png") if p.is_file()], key=_rank)
            if pngs:
                chosen = pngs[0]
                print(f"[PAYMENT_COMPLETE] asset={chosen}")
                return chosen

        fallback = ROOT_DIR / "assets" / "ui" / "6_payment_complete" / "payment_success.png"
        print(f"[PAYMENT_COMPLETE] asset={fallback}")
        return fallback

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._entered_token += 1
        self._active_token = self._entered_token
        method = getattr(self.main_window, "current_payment_method", None) or "unknown"
        prints = getattr(self.main_window, "current_print_count", 2)
        session = self.main_window.get_active_session() if hasattr(self.main_window, "get_active_session") else None
        if session is not None:
            try:
                prints = int(getattr(session, "print_count", prints))
            except Exception:
                pass
        print(f"[PAYMENT_COMPLETE] enter method={method} prints={prints}")
        print(f"[PAYMENT_COMPLETE] auto -> camera in {self.AUTO_MS}ms")
        self._auto_timer.start(self.AUTO_MS)

    def hideEvent(self, event):  # noqa: N802
        self._active_token = 0
        if self._auto_timer.isActive():
            self._auto_timer.stop()
        super().hideEvent(event)

    def _on_auto_timer(self) -> None:
        if not self.isVisible():
            return
        if self._active_token != self._entered_token:
            return
        if hasattr(self.main_window, "handle_payment_complete_success"):
            try:
                self.main_window.handle_payment_complete_success()
            except Exception as exc:
                print(f"[PAYMENT_COMPLETE] auto transition failed: {exc}")
                try:
                    self.main_window.goto_screen("frame_select")
                except Exception:
                    pass


class BootHealthCheckWorker(QObject):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        camera_backend: str,
        camera_dll_path: str,
        printer_ds620_candidates: list[str],
        printer_rx1hs_candidates: list[str],
        internet_api_base_url: str = "",
    ) -> None:
        super().__init__()
        self.camera_backend = str(camera_backend or "auto")
        self.camera_dll_path = str(camera_dll_path or "")
        self.internet_api_base_url = _normalize_kiosk_api_base_url(internet_api_base_url)
        self.printer_ds620_candidates = [
            str(item).strip()
            for item in list(printer_ds620_candidates or [])
            if str(item).strip()
        ]
        self.printer_rx1hs_candidates = [
            str(item).strip()
            for item in list(printer_rx1hs_candidates or [])
            if str(item).strip()
        ]

    @staticmethod
    def _check_printer_candidates(candidates: list[str]) -> tuple[bool, str]:
        unique: list[str] = []
        seen: set[str] = set()
        for raw in list(candidates or []):
            name = str(raw or "").strip()
            if not name:
                continue
            key = re.sub(r"[^a-z0-9]+", "", name.lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(name)
        if not unique:
            return False, "프린터 이름 미설정"
        first_msg = ""
        for idx, name in enumerate(unique):
            ok, msg = get_printer_health(name)
            if ok:
                return True, str(msg)
            if idx == 0:
                first_msg = str(msg)
        return False, first_msg or "printer health check failed"

    def run(self) -> None:
        try:
            results: dict[str, dict[str, Any]] = {}
            cam_ok, cam_msg = get_camera_health(self.camera_dll_path, self.camera_backend)
            results["camera"] = {"ok": bool(cam_ok), "msg": str(cam_msg)}

            ds_ok, ds_msg = self._check_printer_candidates(self.printer_ds620_candidates)
            results["printer_ds620"] = {"ok": bool(ds_ok), "msg": str(ds_msg)}

            rx_ok, rx_msg = self._check_printer_candidates(self.printer_rx1hs_candidates)
            results["printer_rx1hs"] = {"ok": bool(rx_ok), "msg": str(rx_msg)}

            net_ok, net_msg = check_internet(
                timeout=1.0,
                api_base_url=self.internet_api_base_url,
            )
            results["internet"] = {"ok": bool(net_ok), "msg": str(net_msg)}
            self.completed.emit(results)
        except Exception as exc:
            self.failed.emit(str(exc))


class BootHealthCheckScreen(ImageScreen):
    AUTO_START_MS = 1000
    PANEL_RECT = (260, 110, 1400, 860)
    NOTICE_RECT = (120, 925, 1680, 90)
    STATUS_ROWS: list[tuple[str, str]] = [
        ("camera", "Camera"),
        ("printer_ds620", "Printer DS620/STRIP"),
        ("printer_rx1hs", "Printer RX1HS"),
        ("internet", "Internet"),
    ]

    def __init__(self, main_window: "KioskMainWindow") -> None:
        super().__init__(
            main_window,
            "boot_healthcheck",
            ROOT_DIR / "assets" / "ui" / "2_Start" / "start_1.png",
        )
        self._token = 0
        self._active_token = 0
        self._running = False
        self._all_ok = False
        self._thread: Optional[QThread] = None
        self._worker: Optional[BootHealthCheckWorker] = None
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._on_auto_start)

        self._panel = QWidget(self)
        self._panel.setStyleSheet(
            "QWidget { background-color: rgba(10, 14, 24, 228); "
            "border: 2px solid rgba(255,255,255,80); border-radius: 18px; }"
        )
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(42, 30, 42, 30)
        panel_layout.setSpacing(18)

        title = QLabel("SYSTEM HEALTH CHECK", self._panel)
        title.setStyleSheet("color: white; font-size: 40px; font-weight: 800;")
        title.setAlignment(ALIGN_CENTER)
        panel_layout.addWidget(title)

        self._status_rows: dict[str, dict[str, QLabel]] = {}
        for key, text in self.STATUS_ROWS:
            row_widget = QWidget(self._panel)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(8, 10, 8, 10)
            row_layout.setSpacing(14)

            dot_label = QLabel("●", row_widget)
            dot_label.setStyleSheet("color: #9AA4B2; font-size: 28px; font-weight: 700;")
            dot_label.setFixedWidth(30)

            name_label = QLabel(text, row_widget)
            name_label.setStyleSheet("color: white; font-size: 28px; font-weight: 700;")
            name_label.setFixedWidth(300)

            msg_label = QLabel("대기중...", row_widget)
            msg_label.setStyleSheet("color: #C5CEDA; font-size: 24px;")
            msg_label.setWordWrap(True)
            if hasattr(Qt, "AlignmentFlag"):
                msg_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            else:
                msg_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            row_layout.addWidget(dot_label)
            row_layout.addWidget(name_label)
            row_layout.addWidget(msg_label, 1)
            panel_layout.addWidget(row_widget)

            self._status_rows[key] = {
                "dot": dot_label,
                "msg": msg_label,
            }

        panel_layout.addStretch(1)

        button_row = QWidget(self._panel)
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(14)

        self.retry_button = QPushButton("재시도", button_row)
        self.start_button = QPushButton("시작", button_row)
        self.force_button = QPushButton("경고 무시하고 시작", button_row)
        for btn in (self.retry_button, self.start_button, self.force_button):
            btn.setMinimumHeight(64)
            btn.setStyleSheet(
                "QPushButton { background: rgba(255,255,255,30); color: white; "
                "font-size: 26px; font-weight: 700; border-radius: 12px; padding: 8px 24px; } "
                "QPushButton:disabled { color: rgba(255,255,255,100); background: rgba(255,255,255,18); } "
                "QPushButton:hover:!disabled { background: rgba(255,255,255,45); }"
            )
        self.retry_button.clicked.connect(self.start_check)
        self.start_button.clicked.connect(self._on_start_clicked)
        self.force_button.clicked.connect(self._on_force_clicked)

        button_layout.addWidget(self.retry_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.force_button)
        panel_layout.addWidget(button_row)

        self._notice = QLabel("", self)
        self._notice.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0,0,0,170); "
            "font-size: 24px; font-weight: 600; border-radius: 8px; padding: 8px 12px; }"
        )
        self._notice.setAlignment(ALIGN_CENTER)
        self._notice.hide()

        self._layout_widgets()
        self._set_pending_rows()
        self.start_button.setEnabled(False)

    def _layout_widgets(self) -> None:
        self._panel.setGeometry(self.design_rect_to_widget(self.PANEL_RECT))
        self._notice.setGeometry(self.design_rect_to_widget(self.NOTICE_RECT))
        self._panel.raise_()
        self._notice.raise_()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_widgets()

    def _refresh_force_button(self) -> None:
        allow_force = bool(self.main_window.is_test_mode()) if hasattr(self.main_window, "is_test_mode") else False
        self.force_button.setVisible(allow_force)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._refresh_force_button()
        if bool(
            getattr(self.main_window, "_boot_checked", False)
            or getattr(self.main_window, "boot_check_done", False)
        ):
            QTimer.singleShot(0, lambda: self.main_window.goto_screen("start"))
            return
        self.start_check()

    def hideEvent(self, event):  # noqa: N802
        self._token += 1
        self._active_token = 0
        self._auto_timer.stop()
        super().hideEvent(event)

    def _set_pending_rows(self) -> None:
        for key, _text in self.STATUS_ROWS:
            row = self._status_rows.get(key)
            if not row:
                continue
            row["dot"].setStyleSheet("color: #9AA4B2; font-size: 28px; font-weight: 700;")
            row["msg"].setStyleSheet("color: #C5CEDA; font-size: 24px;")
            row["msg"].setText("대기중...")

    def _set_row_result(self, key: str, ok: bool, message: str) -> None:
        row = self._status_rows.get(key)
        if not row:
            return
        if ok:
            row["dot"].setStyleSheet("color: #2EE57B; font-size: 28px; font-weight: 700;")
            row["msg"].setStyleSheet("color: #D9FEE8; font-size: 24px;")
        else:
            row["dot"].setStyleSheet("color: #FF4C5A; font-size: 28px; font-weight: 700;")
            row["msg"].setStyleSheet("color: #FFD9DE; font-size: 24px;")
        row["msg"].setText(str(message))

    def _collect_check_inputs(self) -> dict:
        printing = self.main_window.get_printing_settings() if hasattr(self.main_window, "get_printing_settings") else {}
        share = self.main_window.get_share_settings() if hasattr(self.main_window, "get_share_settings") else {}
        internet_api_base_url = ""
        if isinstance(share, dict):
            internet_api_base_url = _normalize_kiosk_api_base_url(share.get("api_base_url", ""))
        if not internet_api_base_url:
            internet_api_base_url = _normalize_kiosk_api_base_url(
                DEFAULT_SHARE_SETTINGS.get("api_base_url", "")
            )
        ds620_candidates: list[str] = []
        rx1hs_candidates: list[str] = []
        if hasattr(self.main_window, "_resolve_printer_candidates_for_model"):
            ds620_candidates.extend(
                self.main_window._resolve_printer_candidates_for_model(
                    model="DS620",
                    primary_name="",
                    settings=printing,
                )
            )
            strip_candidates = self.main_window._resolve_printer_candidates_for_model(
                model="DS620_STRIP",
                primary_name="",
                settings=printing,
            )
            for cand in strip_candidates:
                token = re.sub(r"[^a-z0-9]+", "", str(cand).strip().lower())
                exists = any(
                    re.sub(r"[^a-z0-9]+", "", str(item).strip().lower()) == token
                    for item in ds620_candidates
                )
                if token and not exists:
                    ds620_candidates.append(str(cand).strip())
            rx1hs_candidates.extend(
                self.main_window._resolve_printer_candidates_for_model(
                    model="RX1HS",
                    primary_name="",
                    settings=printing,
                )
            )
        elif hasattr(self.main_window, "_resolve_printer_name_for_model"):
            ds620 = self.main_window._resolve_printer_name_for_model("DS620", printing)
            rx1hs = self.main_window._resolve_printer_name_for_model("RX1HS", printing)
            if ds620:
                ds620_candidates.append(ds620)
            if rx1hs:
                rx1hs_candidates.append(rx1hs)
        return {
            "camera_backend": self.main_window._resolve_requested_camera_backend()
            if hasattr(self.main_window, "_resolve_requested_camera_backend")
            else "auto",
            "camera_dll_path": self.main_window._resolve_canon_edsdk_dll_path()
            if hasattr(self.main_window, "_resolve_canon_edsdk_dll_path")
            else "",
            "internet_api_base_url": internet_api_base_url,
            "printer_ds620_candidates": ds620_candidates,
            "printer_rx1hs_candidates": rx1hs_candidates,
        }

    def start_check(self) -> None:
        if self._running:
            return
        self._notice.hide()
        self._auto_timer.stop()
        self._set_pending_rows()
        self._all_ok = False
        self.start_button.setEnabled(False)
        self.retry_button.setEnabled(False)

        payload = self._collect_check_inputs()
        self._token += 1
        token = self._token
        self._active_token = token
        self._running = True

        worker = BootHealthCheckWorker(
            camera_backend=str(payload.get("camera_backend", "auto")),
            camera_dll_path=str(payload.get("camera_dll_path", "")),
            printer_ds620_candidates=list(payload.get("printer_ds620_candidates", [])),
            printer_rx1hs_candidates=list(payload.get("printer_rx1hs_candidates", [])),
            internet_api_base_url=str(payload.get("internet_api_base_url", "")),
        )
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.completed.connect(self._on_worker_completed)
        worker.failed.connect(self._on_worker_failed)
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_worker_finished)
        self._worker = worker
        self._thread = thread
        thread.start()

    def _on_worker_completed(self, result: dict) -> None:
        self._on_check_completed(self._active_token, result)

    def _on_worker_failed(self, message: str) -> None:
        self._on_check_failed(self._active_token, message)

    def _on_worker_finished(self) -> None:
        self._running = False
        self.retry_button.setEnabled(True)
        self._thread = None
        self._worker = None

    def _on_check_completed(self, token: int, result: dict) -> None:
        if token != self._token:
            return
        status_map: dict[str, bool] = {}
        for key, _name in self.STATUS_ROWS:
            row_result = result.get(key, {}) if isinstance(result, dict) else {}
            ok = bool(row_result.get("ok", False))
            message = str(row_result.get("msg", "unknown"))
            self._set_row_result(key, ok, message)
            status_map[key] = ok
            log_key = _health_log_key(key)
            print(f"[HEALTH] {log_key}={'OK' if ok else 'FAIL'} msg={message}")

        camera_ok = bool(status_map.get("camera", False))
        internet_ok = bool(status_map.get("internet", False))
        ds620_ok = bool(status_map.get("printer_ds620", False))
        rx1hs_ok = bool(status_map.get("printer_rx1hs", False))
        printer_any_ok = ds620_ok or rx1hs_ok
        all_ok = camera_ok and internet_ok and printer_any_ok
        print(
            f"[HEALTH] printer_any={'OK' if printer_any_ok else 'FAIL'} "
            f"msg=DS620={1 if ds620_ok else 0} RX1HS={1 if rx1hs_ok else 0}"
        )

        self._all_ok = all_ok
        self.start_button.setEnabled(all_ok)
        if all_ok:
            self._notice.setText("점검 완료. 잠시 후 시작합니다.")
            self._notice.show()
            self._auto_timer.start(self.AUTO_START_MS)
        else:
            if not printer_any_ok:
                self._notice.setText("프린터(DS620/RX1HS) 중 1대 이상 연결이 필요합니다.")
            else:
                self._notice.setText("점검 실패 항목이 있습니다. 재시도하거나 관리자에게 문의하세요.")
            self._notice.show()

    def _on_check_failed(self, token: int, message: str) -> None:
        if token != self._token:
            return
        self._all_ok = False
        self.start_button.setEnabled(False)
        for key, _name in self.STATUS_ROWS:
            self._set_row_result(key, False, "check failed")
        print(f"[HEALTH] boot_check=FAIL {message}")
        self._notice.setText(f"점검 실패: {message}")
        self._notice.show()

    def _on_start_clicked(self) -> None:
        if not self._all_ok:
            return
        if hasattr(self.main_window, "complete_boot_healthcheck"):
            self.main_window.complete_boot_healthcheck(force=False)

    def _on_force_clicked(self) -> None:
        if hasattr(self.main_window, "complete_boot_healthcheck"):
            self.main_window.complete_boot_healthcheck(force=True)

    def _on_auto_start(self) -> None:
        if not self._all_ok:
            return
        if not self.isVisible():
            return
        if hasattr(self.main_window, "complete_boot_healthcheck"):
            self.main_window.complete_boot_healthcheck(force=False)


class AppQrUploadWorker(QObject):
    upload_ok = Signal(str, str)
    upload_fail = Signal(str)
    finished = Signal()

    def __init__(
        self,
        session: Optional[Session],
        share_settings: dict,
        layout_id: Optional[str],
        print_slots: int,
        capture_slots: int,
        design_index: Optional[int],
    ) -> None:
        super().__init__()
        self.session = session
        self.share_settings = dict(share_settings)
        self.layout_id = layout_id
        self.print_slots = int(print_slots or 0)
        self.capture_slots = int(capture_slots or 0)
        self.design_index = design_index

    @staticmethod
    def _as_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return bool(default)

    @classmethod
    def _env_flag(cls, key: str, default: bool = False) -> bool:
        return cls._as_bool(os.environ.get(key), default)

    def _upload_dry_run_enabled(self) -> bool:
        cfg_value = self.share_settings.get("upload_dry_run")
        cfg_enabled = self._as_bool(cfg_value, False)
        env_enabled = self._env_flag("UPLOAD_DRY_RUN", False)
        return cfg_enabled or env_enabled

    def _timeout_sec(self) -> float:
        raw = self.share_settings.get("timeout_sec", DEFAULT_SHARE_SETTINGS.get("timeout_sec", 12.0))
        try:
            timeout = float(raw)
        except Exception:
            timeout = float(DEFAULT_SHARE_SETTINGS.get("timeout_sec", 12.0))
        return min(60.0, max(3.0, timeout))

    def _api_base_url(self) -> str:
        configured = _normalize_kiosk_api_base_url(self.share_settings.get("api_base_url", ""))
        if configured:
            return configured
        base_page = str(self.share_settings.get("base_page_url", "")).strip()
        if not base_page:
            return ""
        split = urlsplit(base_page)
        if split.scheme and split.netloc:
            return _normalize_kiosk_api_base_url(f"{split.scheme}://{split.netloc}")
        return _normalize_kiosk_api_base_url(base_page)

    def _device_headers(self) -> dict[str, str]:
        device_code = str(self.share_settings.get("device_code", "")).strip() or str(
            os.environ.get("KIOSK_DEVICE_CODE", "")
        ).strip()
        device_token = str(self.share_settings.get("device_token", "")).strip() or str(
            os.environ.get("KIOSK_DEVICE_TOKEN", "")
        ).strip()
        if not device_code:
            raise RuntimeError("share.device_code missing")
        if not device_token:
            raise RuntimeError("share.device_token missing")
        return {
            "X-Device-Code": device_code,
            "X-Device-Token": device_token,
            "Accept": "application/json",
        }

    @staticmethod
    def _response_error_text(response: Any) -> str:
        try:
            text = str(response.text or "").strip()
        except Exception:
            text = ""
        text = text.replace("\r", " ").replace("\n", " ").strip()
        if len(text) > 240:
            text = text[:240] + "..."
        return text

    def _consume_server_lock_response(self, response: Any, trigger: str) -> tuple[bool, Optional[dict[str, Any]]]:
        payload: Optional[dict[str, Any]] = None
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                payload = parsed
        except Exception:
            payload = None

        if isinstance(payload, dict):
            lock_payload = payload.get("device_lock")
            if isinstance(lock_payload, dict):
                self._apply_server_lock_payload(lock_payload, trigger=trigger)
            elif str(payload.get("reason", "")).strip().upper() == "DEVICE_LOCKED":
                self._apply_server_lock_payload(
                    {
                        "locked": True,
                        "lock_reason": str(payload.get("lock_reason", "")).strip(),
                        "locked_at": str(payload.get("locked_at", "")).strip(),
                    },
                    trigger=trigger,
                )
                return True, payload
        return False, payload

    def _post_json(self, client: Any, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        response = client.post(url, json=payload, headers=headers, timeout=self._timeout_sec())
        lock_hit, parsed_payload = self._consume_server_lock_response(response, trigger="share_api")
        if lock_hit:
            raise RuntimeError(f"{url} HTTP {response.status_code}: DEVICE_LOCKED")
        if int(response.status_code) >= 400:
            raise RuntimeError(
                f"{url} HTTP {response.status_code}: {self._response_error_text(response)}"
            )
        data = parsed_payload
        if data is None:
            try:
                data = response.json()
            except Exception:
                raise RuntimeError(f"{url} invalid json response")
        if not isinstance(data, dict):
            raise RuntimeError(f"{url} invalid json payload")
        return data

    def _post_file(
        self,
        client: Any,
        url: str,
        token: str,
        kind: str,
        file_path: Path,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        with file_path.open("rb") as handle:
            files = {"file": (file_path.name, handle, content_type)}
            data = {"token": token, "kind": kind}
            response = client.post(url, data=data, files=files, headers=headers, timeout=self._timeout_sec())
        lock_hit, parsed_payload = self._consume_server_lock_response(response, trigger="share_api")
        if lock_hit:
            raise RuntimeError(f"{url} HTTP {response.status_code}: DEVICE_LOCKED")
        if int(response.status_code) >= 400:
            raise RuntimeError(
                f"{url} HTTP {response.status_code}: {self._response_error_text(response)}"
            )
        payload = parsed_payload
        if payload is None:
            try:
                payload = response.json()
            except Exception:
                raise RuntimeError(f"{url} invalid json response")
        if not isinstance(payload, dict):
            raise RuntimeError(f"{url} invalid json payload")
        return payload

    def _build_dummy_urls(self, session_id: str) -> tuple[str, str, str, str]:
        base_page_url = str(
            self.share_settings.get("base_page_url", DEFAULT_SHARE_SETTINGS["base_page_url"])
        ).rstrip("/")
        base_file_url = str(
            self.share_settings.get("base_file_url", DEFAULT_SHARE_SETTINGS["base_file_url"])
        ).rstrip("/")
        page_url = f"{base_page_url}/{session_id}"
        frame_url = f"{base_file_url}/{session_id}/frame.png"
        image_url = f"{base_file_url}/{session_id}/print.jpg"
        video_url = f"{base_file_url}/{session_id}/video.gif"
        return page_url, frame_url, image_url, video_url

    def _upload_via_server(
        self,
        session_id: str,
        image_local: Path,
        frame_local: Path,
        video_local: Path,
    ) -> tuple[str, dict[str, dict[str, Any]], str]:
        if requests is None:
            raise RuntimeError("requests module not installed")
        api_base_url = self._api_base_url()
        if not api_base_url:
            raise RuntimeError("share.api_base_url missing")
        headers = self._device_headers()
        init_url = f"{api_base_url}/kiosk/share/init"
        upload_url = f"{api_base_url}/kiosk/share/upload"
        finalize_url = f"{api_base_url}/kiosk/share/finalize"

        with requests.Session() as client:
            # Use kiosk session_id as share token so printed QR(/s/<session_id>) matches final share link.
            init_payload = {"session_id": session_id, "token": session_id}
            init_data = self._post_json(client, init_url, init_payload, headers)
            token = str(init_data.get("token", "")).strip()
            page_url = str(init_data.get("share_url", "")).strip()
            if not token:
                raise RuntimeError("share init missing token")
            print(f"[UPLOAD] init ok token={token} share_url={page_url}")

            files_meta: dict[str, dict[str, Any]] = {}
            upload_specs = [
                ("PRINT", image_local, "image"),
                ("FRAME", frame_local, "frame"),
                ("GIF", video_local, "video"),
            ]
            for kind, file_path, local_key in upload_specs:
                if not file_path.is_file():
                    continue
                upload_data = self._post_file(client, upload_url, token, kind, file_path, headers)
                entry: dict[str, Any] = {"name": file_path.name}
                key_value = str(upload_data.get("key", "")).strip()
                if key_value:
                    entry["key"] = key_value
                size_bytes = upload_data.get("size_bytes")
                if isinstance(size_bytes, int):
                    entry["size_bytes"] = size_bytes
                files_meta[local_key] = entry
                print(
                    f"[UPLOAD] file ok kind={kind} "
                    f"key={entry.get('key', '')} size={entry.get('size_bytes', 0)}"
                )

            finalize_payload = {
                "token": token,
                "meta": {
                    "layout_id": self.layout_id,
                    "print_slots": self.print_slots,
                    "capture_slots": self.capture_slots,
                    "design_index": self.design_index,
                },
            }
            finalize_data = self._post_json(client, finalize_url, finalize_payload, headers)
            finalized_share_url = str(finalize_data.get("share_url", "")).strip()
            if finalized_share_url:
                page_url = finalized_share_url
            if not page_url:
                relative_url = str(finalize_data.get("url", "")).strip()
                if relative_url.startswith("/"):
                    split = urlsplit(api_base_url)
                    page_url = f"{split.scheme}://{split.netloc}{relative_url}"
            if not page_url:
                base_page_url = str(
                    self.share_settings.get("base_page_url", DEFAULT_SHARE_SETTINGS["base_page_url"])
                ).rstrip("/")
                page_url = f"{base_page_url}/{token}"

            print(f"[UPLOAD] finalize ok share_url={page_url}")
            return page_url, files_meta, token

    def run(self) -> None:
        try:
            if self.session is None:
                raise RuntimeError("session missing")
            session_id = self.session.session_id or self.session.session_dir.name
            share_dir = ensure_share_dir(self.session.session_dir)
            share_json_path = share_dir / "share.json"
            frame_local = share_dir / "frame.png"
            image_local = share_dir / "print.jpg"
            video_local = share_dir / "video.gif"

            dry_run_upload = self._upload_dry_run_enabled()
            file_entries: dict[str, dict[str, Any]] = {}
            server_token = ""
            if dry_run_upload:
                print("[UPLOAD] DRY_RUN reason=upload_dry_run")
                time.sleep(1.0)
                page_url, frame_url, image_url, video_url = self._build_dummy_urls(session_id)
                if frame_local.is_file():
                    file_entries["frame"] = {"name": "frame.png", "url": frame_url}
                if image_local.is_file():
                    file_entries["image"] = {"name": "print.jpg", "url": image_url}
                if video_local.is_file():
                    file_entries["video"] = {"name": "video.gif", "url": video_url}
            else:
                page_url, server_files, server_token = self._upload_via_server(
                    session_id=session_id,
                    image_local=image_local,
                    frame_local=frame_local,
                    video_local=video_local,
                )
                file_entries.update(server_files)

            payload: dict[str, Any] = {
                "session_id": session_id,
                "page_url": page_url,
                "files": file_entries,
                "layout_id": self.layout_id,
                "print_slots": self.print_slots,
                "capture_slots": self.capture_slots,
                "design_index": self.design_index,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "upload_mode": "dry_run" if dry_run_upload else "server",
            }
            if server_token:
                payload["share_token"] = server_token

            _write_json_atomic(share_json_path, payload)
            print(f"[SHARE] share.json written path={share_json_path}")

            qr_path = generate_qr_png(page_url, self.session.qr_dir / "qr.png")
            print(f"[QR] qr.png saved path={qr_path}")
            self.upload_ok.emit(page_url, str(qr_path))
        except Exception as exc:
            self.upload_fail.emit(str(exc))
        finally:
            self.finished.emit()


class AppQrGeneratingScreen(ImageScreen):
    FRAME_INTERVAL_MS = 180
    MIN_HOLD_MS = 20000
    FAIL_NOTICE_MS = 1000
    GIF_RECT = (700, 280, 520, 520)

    def __init__(self, main_window: "KioskMainWindow") -> None:
        self._base_dir = ROOT_DIR / "assets" / "ui" / "11_Qrcode"
        initial_path = self._resolve_background_path()
        super().__init__(main_window, "qr_generating", initial_path)
        self._frame_paths = [initial_path]
        self._frame_pixmaps: list[QPixmap] = []
        for path in self._frame_paths:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self._frame_pixmaps.append(pixmap)
        if not self._frame_pixmaps:
            self._frame_pixmaps = [QPixmap(str(initial_path))]

        self._frame_index = 0
        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(self.FRAME_INTERVAL_MS)
        self._frame_timer.timeout.connect(self._advance_frame)

        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._hide_notice)
        self._notice_label = QLabel("", self)
        self._notice_label.setAlignment(ALIGN_CENTER)
        self._notice_label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(0, 0, 0, 180); "
            "font-size: 42px; font-weight: 700; border: 2px solid rgba(255,255,255,140); }"
        )
        self._notice_label.hide()
        self._gif_label = QLabel(self)
        self._gif_label.setAlignment(ALIGN_CENTER)
        self._gif_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        self._gif_label.setAttribute(WA_TRANSPARENT, True)
        self._gif_label.hide()
        self._gif_movie: Optional[QMovie] = None

        self._token = 0
        self._active_token = 0
        self._thread: Optional[QThread] = None
        self._worker: Optional[AppQrUploadWorker] = None
        self._entered_monotonic = 0.0
        self._upload_completed = False
        self._pending_page_url: Optional[str] = None
        self._pending_qr_path: Optional[Path] = None
        self._transition_scheduled = False

    @staticmethod
    def _frame_sort_key(path: Path) -> tuple[int, int, str]:
        stem = path.stem.strip().lower()
        match = re.search(r"(\d+)", stem)
        if match:
            return (0, int(match.group(1)), path.name.lower())
        return (1, 0, path.name.lower())

    def _resolve_background_path(self) -> Path:
        preferred = self._base_dir / "Generation_QR_code.png"
        if preferred.is_file():
            return preferred
        if not self._base_dir.is_dir():
            return preferred
        pngs = sorted(
            [p for p in self._base_dir.glob("*.png") if p.is_file()],
            key=self._frame_sort_key,
        )
        return pngs[0] if pngs else preferred

    def _set_background_frame(self, index: int) -> None:
        if not self._frame_pixmaps:
            return
        safe_index = max(0, min(index, len(self._frame_pixmaps) - 1))
        self._frame_index = safe_index
        pixmap = self._frame_pixmaps[safe_index]
        if not pixmap.isNull():
            self._background = pixmap
            self.update()

    def _advance_frame(self) -> None:
        if len(self._frame_pixmaps) <= 1:
            return
        self._frame_index = (self._frame_index + 1) % len(self._frame_pixmaps)
        self._set_background_frame(self._frame_index)

    def _show_notice(self, message: str, duration_ms: int = FAIL_NOTICE_MS) -> None:
        self._notice_label.setText(message)
        self._notice_label.show()
        self._notice_label.raise_()
        self._notice_timer.start(max(200, int(duration_ms)))

    def _hide_notice(self) -> None:
        self._notice_label.hide()

    def _layout_gif(self) -> None:
        self._gif_label.setGeometry(self.design_rect_to_widget(self.GIF_RECT))
        if self._gif_movie is not None:
            self._gif_movie.setScaledSize(self._gif_label.size())

    def _stop_gif(self) -> None:
        if self._gif_movie is not None:
            try:
                self._gif_movie.stop()
            except Exception:
                pass
            self._gif_label.setMovie(None)
            self._gif_movie.deleteLater()
            self._gif_movie = None
        self._gif_label.hide()

    def _find_gif_path(self) -> Optional[Path]:
        session = self.main_window.get_active_session() if hasattr(self.main_window, "get_active_session") else None
        if session is None:
            return None
        share_dir = Path(session.session_dir) / "share"
        preferred = share_dir / "video.gif"
        if preferred.is_file():
            return preferred
        gif_files = sorted([p for p in share_dir.glob("*.gif") if p.is_file()], key=lambda p: p.name.lower())
        return gif_files[0] if gif_files else None

    def _start_gif(self) -> None:
        self._stop_gif()
        gif_path = self._find_gif_path()
        if gif_path is None:
            print("[GIF] missing")
            return
        movie = QMovie(str(gif_path))
        if not movie.isValid():
            print(f"[GIF] missing path={gif_path}")
            movie.deleteLater()
            return
        movie.setScaledSize(self._gif_label.size())
        self._gif_movie = movie
        self._gif_label.setMovie(movie)
        self._gif_label.show()
        movie.start()
        print(f"[GIF] show path={gif_path}")

    def _schedule_thank_you_transition(self, page_url: Optional[str], qr_path: Optional[Path]) -> None:
        if self._transition_scheduled:
            return
        self._transition_scheduled = True
        elapsed_ms = int(max(0.0, time.monotonic() - self._entered_monotonic) * 1000)
        remaining_ms = max(0, self.MIN_HOLD_MS - elapsed_ms)
        ready_url = page_url or ""
        print(f"[QR] ready url={ready_url} -> will advance in {remaining_ms} ms")
        QTimer.singleShot(
            remaining_ms,
            lambda t=self._token, q=qr_path: self._go_thank_you_if_active(t, q),
        )

    def _go_thank_you_if_active(self, token: int, qr_path: Optional[Path]) -> None:
        if token != self._token:
            return
        if not self.isVisible():
            return
        print("[NAV] qr_generating -> thank_you")
        if hasattr(self.main_window, "handle_qr_generating_done"):
            self.main_window.handle_qr_generating_done(qr_path)
        else:
            self.main_window.goto_screen("thank_you")

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._notice_label.setGeometry(self.design_rect_to_widget((450, 430, 1020, 180)))
        self._layout_gif()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._token += 1
        self._active_token = self._token
        self._entered_monotonic = time.monotonic()
        self._upload_completed = False
        self._pending_page_url = None
        self._pending_qr_path = None
        self._transition_scheduled = False
        print(f"[QR] generating enter t0={self._entered_monotonic:.3f}")
        self._set_background_frame(0)
        self._layout_gif()
        self._start_gif()
        self._hide_notice()
        if len(self._frame_pixmaps) > 1:
            self._frame_timer.start()
        self._start_upload_worker(self._active_token)

    def hideEvent(self, event):  # noqa: N802
        self._token += 1
        self._active_token = 0
        self._frame_timer.stop()
        self._notice_timer.stop()
        self._hide_notice()
        self._stop_gif()
        super().hideEvent(event)

    def _start_upload_worker(self, token: int) -> None:
        session = self.main_window.get_active_session() if hasattr(self.main_window, "get_active_session") else None
        if session is None:
            print("[UPLOAD] fail: session missing")
            self._on_worker_fail("session missing")
            return
        if hasattr(self.main_window, "check_runtime_internet_health"):
            net_ok, net_msg = self.main_window.check_runtime_internet_health()
            if not net_ok:
                self._on_worker_fail(f"internet offline: {net_msg}")
                return
        if self._thread is not None and self._thread.isRunning():
            print("[QR] upload worker already running")
            return

        share_settings = (
            self.main_window.get_share_settings()
            if hasattr(self.main_window, "get_share_settings")
            else dict(DEFAULT_SHARE_SETTINGS)
        )
        worker = AppQrUploadWorker(
            session=session,
            share_settings=share_settings,
            layout_id=getattr(self.main_window, "current_layout_id", None),
            print_slots=int(getattr(self.main_window, "current_print_slots", 0) or 0),
            capture_slots=int(getattr(self.main_window, "current_capture_slots", 0) or 0),
            design_index=getattr(self.main_window, "current_design_index", None),
        )
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.upload_ok.connect(self._on_worker_ok)
        worker.upload_fail.connect(self._on_worker_fail)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        self._thread = thread
        self._worker = worker
        self._active_token = token
        thread.start()

    def _on_worker_ok(self, page_url: str, qr_png_path: str) -> None:
        if self._active_token != self._token:
            return
        print(f"[UPLOAD] ok url={page_url}")
        qr_path = Path(qr_png_path)
        session = self.main_window.get_active_session() if hasattr(self.main_window, "get_active_session") else None
        if session is not None:
            try:
                if qr_path.is_file():
                    qr_path = session.save_qr(qr_path)
                session.set_share_url(page_url)
                session.page_url = page_url
                session.qr_png_path = str(qr_path)
            except Exception as exc:
                print(f"[QR] session update failed: {exc}")
        self._upload_completed = True
        self._pending_page_url = page_url
        self._pending_qr_path = qr_path if qr_path.is_file() else None
        self._schedule_thank_you_transition(self._pending_page_url, self._pending_qr_path)

    def _on_worker_fail(self, error_message: str) -> None:
        if self._active_token != self._token:
            return
        print(f"[UPLOAD] fail: {error_message}")
        self._show_notice("업로드 실패", duration_ms=self.FAIL_NOTICE_MS)
        self._upload_completed = True
        self._pending_page_url = None
        self._pending_qr_path = None
        self._schedule_thank_you_transition(None, None)

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None


class AppQrCodeScreen(ImageScreen):
    AUTO_NEXT_MS = 20000

    def __init__(self, main_window: "KioskMainWindow") -> None:
        self._base_dir = ROOT_DIR / "assets" / "ui" / "11_Qrcode"
        self._background_path = self._resolve_background_path()
        super().__init__(main_window, "qr_code", self._background_path)
        self._qr_design_rect, self._qr_rect_source = detect_qr_placeholder_rect(self._background_path)
        print(
            "[QR_UI] placeholder rect="
            f"({self._qr_design_rect[0]},{self._qr_design_rect[1]},"
            f"{self._qr_design_rect[2]},{self._qr_design_rect[3]}) "
            f"source={self._qr_rect_source}"
        )
        self._qr_label = QLabel(self)
        self._qr_label.setAlignment(ALIGN_CENTER)
        self._qr_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        self._qr_label.setAttribute(WA_TRANSPARENT, True)
        self._qr_source: Optional[QPixmap] = None
        self._qr_path: Optional[Path] = None
        self._page_url: Optional[str] = None
        self._token = 0
        self._active_token = 0
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._on_auto_next)
        self._layout_qr_label()

    def _resolve_background_path(self) -> Path:
        fallback = self._base_dir / "Generation_QR_code.png"
        if not self._base_dir.is_dir():
            return fallback
        pngs = [p for p in self._base_dir.glob("*.png") if p.is_file()]
        if not pngs:
            return fallback

        def _rank(path: Path) -> tuple[int, str]:
            name = path.stem.lower()
            if "main" in name:
                return (0, path.name.lower())
            if "qr" in name or "code" in name:
                return (1, path.name.lower())
            if "generat" in name:
                return (3, path.name.lower())
            return (2, path.name.lower())

        return sorted(pngs, key=_rank)[0]

    def _layout_qr_label(self) -> None:
        self._qr_label.setGeometry(self.design_rect_to_widget(self._qr_design_rect))
        self._render_qr()

    def _render_qr(self) -> None:
        if self._qr_source is None:
            self._qr_label.clear()
            self._qr_label.hide()
            return
        rect = self._qr_label.contentsRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        scaled = self._qr_source.scaled(rect.size(), KEEP_ASPECT, SMOOTH_TRANSFORM)
        self._qr_label.setPixmap(scaled)
        self._qr_label.show()

    def set_qr_context(self, qr_path: Optional[Path], page_url: Optional[str]) -> None:
        self._page_url = page_url
        self._qr_path = qr_path if isinstance(qr_path, Path) else None
        self._qr_source = None
        if self._qr_path is not None and self._qr_path.is_file():
            pixmap = QPixmap(str(self._qr_path))
            if not pixmap.isNull():
                self._qr_source = pixmap
        self._render_qr()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._token += 1
        self._active_token = self._token
        session = self.main_window.get_active_session() if hasattr(self.main_window, "get_active_session") else None
        qr_path: Optional[Path] = None
        page_url: Optional[str] = None
        if session is not None:
            page_url = getattr(session, "share_url", None)
            raw_qr_path = getattr(session, "qr_path", None)
            if isinstance(raw_qr_path, Path):
                qr_path = raw_qr_path
            elif isinstance(raw_qr_path, str) and raw_qr_path.strip():
                qr_path = Path(raw_qr_path)
            if qr_path is None:
                alt = getattr(session, "qr_png_path", None)
                if isinstance(alt, str) and alt.strip():
                    qr_path = Path(alt)
        self.set_qr_context(qr_path, page_url)
        self._auto_timer.start(self.AUTO_NEXT_MS)

    def hideEvent(self, event):  # noqa: N802
        self._active_token = 0
        if self._auto_timer.isActive():
            self._auto_timer.stop()
        super().hideEvent(event)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._layout_qr_label()

    def _on_auto_next(self) -> None:
        if not self.isVisible():
            return
        if self._active_token != self._token:
            return
        self.main_window.goto_screen("thank_you")


class MainPrintWorker(QObject):
    success = Signal()
    failure = Signal(str)

    def __init__(
        self,
        image_path: Path,
        printer_name: str,
        copies: int,
        model: str,
        form_name: str,
        strip_split: bool,
        strip_sets: int,
        layout_id: Optional[str],
        enabled: bool,
        dry_run: bool,
        test_mode: bool,
    ) -> None:
        super().__init__()
        self.image_path = Path(image_path)
        self.printer_name = str(printer_name or "")
        self.copies = max(1, int(copies))
        self.model = str(model or "DS620")
        self.form_name = str(form_name or "")
        self.strip_split = bool(strip_split)
        self.strip_sets = max(1, int(strip_sets))
        self.layout_id = str(layout_id or "")
        self.enabled = bool(enabled)
        self.dry_run = bool(dry_run)
        self.test_mode = bool(test_mode)
        self.call_timeout_sec = max(10.0, float(os.environ.get("KIOSK_PRINT_CALL_TIMEOUT_SEC", "45") or 45))

    def _run_single_print_call(self, image_path: Path) -> None:
        error_box: dict[str, Exception] = {}

        def _target() -> None:
            try:
                win_print_image(
                    self.printer_name,
                    str(image_path),
                    copies=1,
                    form_name=self.form_name,
                )
            except Exception as exc:
                error_box["error"] = exc

        thread = threading.Thread(target=_target, name="print_call", daemon=True)
        thread.start()
        thread.join(self.call_timeout_sec)
        if thread.is_alive():
            raise TimeoutError(
                f"print call timeout after {self.call_timeout_sec:.0f}s "
                f"(printer={self.printer_name})"
            )
        if "error" in error_box:
            raise error_box["error"]

    def run(self) -> None:
        try:
            exists = self.image_path.is_file()
            size = self.image_path.stat().st_size if exists else 0
            print(
                f"[PRINT] request image={self.image_path} exists={1 if exists else 0} "
                f"size={size}"
            )
            print(
                f"[PRINT] mode enabled={1 if self.enabled else 0} "
                f"dry_run={1 if self.dry_run else 0} test_mode={1 if self.test_mode else 0}"
            )
            print(
                f"[PRINT] target model={self.model} win_name=\"{self.printer_name}\" "
                f"copies={self.copies} form=\"{self.form_name}\""
            )

            if not self.enabled:
                print("[PRINT] blocked: printing.enabled=0")
                if self.test_mode:
                    print("[PRINT] disabled but test_mode=1 -> success")
                    self.success.emit()
                    return
                raise RuntimeError("printing is disabled")

            if self.dry_run or self.test_mode:
                reason = "dry_run" if self.dry_run else "test_mode"
                print(f"[PRINT] DRY_RUN reason={reason}")
                time.sleep(0.2)
                self.success.emit()
                return

            if not exists:
                raise FileNotFoundError(f"print image missing: {self.image_path}")
            if self.strip_split:
                print(
                    f"[PRINT] STRIP layout={self.layout_id or 'unknown'} "
                    f"print_count={self.strip_sets * 2} sets={self.strip_sets}"
                )
                part_a, part_b = _split_print_image_for_2x6(self.image_path)
                for _set_index in range(self.strip_sets):
                    print("[PRINT] strip part A -> 2x6")
                    self._run_single_print_call(part_a)
                    print("[PRINT] strip part B -> 2x6")
                    self._run_single_print_call(part_b)
            else:
                for copy_index in range(max(1, int(self.copies))):
                    print(
                        f"[PRINT] fullsheet copy {copy_index + 1}/{max(1, int(self.copies))} -> 4x6"
                    )
                    self._run_single_print_call(self.image_path)
            print(
                f"[PRINT] sent to spooler ok printer=\"{self.printer_name}\" "
                f"copies={self.copies}"
            )
            self.success.emit()
        except Exception as exc:
            print(f"[PRINT] ERROR {exc!r}")
            self.failure.emit(str(exc))


class BillAcceptorWorker(QThread):
    log = Signal(str)
    bill_accepted = Signal(int, int, int)
    failed = Signal(str)

    DEFAULT_ACCEPT_STATUS_CODES = {0x05, 0x0B}
    DEFAULT_BILL_TO_AMOUNT = {
        1: 1000,
        5: 5000,
        10: 10000,
    }

    def __init__(self, settings: dict, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.settings = dict(settings or {})
        self._running = True
        self._serial_conn = None
        self._insert_enabled = False
        self._last_status: Optional[int] = None
        self._accept_status_codes = self._resolve_accept_status_codes()
        self._bill_to_amount_map = self._resolve_bill_to_amount_map()

    def request_stop(self) -> None:
        self._running = False
        self.requestInterruption()

    def _log(self, message: str) -> None:
        self.log.emit(str(message))

    def _profile_data(self) -> dict:
        profile_key = str(self.settings.get("profile", DEFAULT_BILL_ACCEPTOR_SETTINGS["profile"])).strip()
        if profile_key not in BILL_PROFILES:
            profile_key = str(DEFAULT_BILL_ACCEPTOR_SETTINGS["profile"])
        return dict(BILL_PROFILES.get(profile_key, {}))

    def _resolve_accept_status_codes(self) -> set[int]:
        profile_data = self._profile_data()
        result = set(self.DEFAULT_ACCEPT_STATUS_CODES)
        raw_codes = profile_data.get("recognition_status")
        if isinstance(raw_codes, (list, tuple, set)):
            parsed: set[int] = set()
            for code in raw_codes:
                try:
                    value = int(code) & 0xFF
                except Exception:
                    continue
                parsed.add(value)
            if parsed:
                result = parsed
        return result

    def _resolve_bill_to_amount_map(self) -> dict[int, int]:
        result = dict(self.DEFAULT_BILL_TO_AMOUNT)
        profile_data = self._profile_data()

        def _apply(raw_map: Any) -> None:
            if not isinstance(raw_map, dict):
                return
            for raw_key, raw_amount in raw_map.items():
                try:
                    bill_code = int(raw_key) & 0xFF
                    amount = int(raw_amount)
                except Exception:
                    continue
                if amount > 0:
                    result[bill_code] = amount

        _apply(profile_data.get("bill_to_amount"))
        _apply(self.settings.get("bill_to_amount"))
        return result

    def _resolve_config_byte(self) -> int:
        profile_data = self._profile_data()
        denoms: dict[str, bool] = dict(DEFAULT_BILL_ACCEPTOR_SETTINGS["denoms"])
        profile_denoms = profile_data.get("default_denoms")
        if isinstance(profile_denoms, dict):
            for key in denoms.keys():
                denoms[key] = bool(profile_denoms.get(key, denoms[key]))
        raw_denoms = self.settings.get("denoms")
        if isinstance(raw_denoms, dict):
            for key in denoms.keys():
                denoms[key] = bool(raw_denoms.get(key, denoms[key]))

        cfg = 0x10  # auto stack ON
        if denoms.get("1000"):
            cfg |= 0x01
        if denoms.get("5000"):
            cfg |= 0x02
        if denoms.get("10000"):
            cfg |= 0x04
        if denoms.get("50000"):
            cfg |= 0x08
        return int(cfg) & 0xFF

    @staticmethod
    def _is_ok_response(packet: tuple[int, int, int], suffix: Any = None) -> bool:
        b2, b3, b4 = packet
        if chr(int(b2)).upper() != "O":
            return False
        if chr(int(b3)).upper() != "K":
            return False
        if suffix is None:
            return True
        expected = chr(_packet_byte(suffix)).lower()
        return chr(int(b4)).lower() == expected

    def _send(self, cmd: tuple[Any, Any, Any], timeout: float = 0.5, retries: int = 3, validator=None) -> tuple[int, int, int]:
        if self._serial_conn is None:
            raise RuntimeError("serial not open")
        return send_cmd_with_retry(
            self._serial_conn,
            cmd,
            timeout=timeout,
            retries=retries,
            validator=validator,
        )

    def cmd_get_status(self) -> int:
        packet = self._send(("G", "A", "?"))
        return int(packet[2]) & 0xFF

    def cmd_get_billdata(self) -> int:
        packet = self._send(("G", "B", "?"))
        return int(packet[2]) & 0xFF

    def cmd_get_error(self) -> int:
        packet = self._send(("G", "E", "?"))
        return int(packet[2]) & 0xFF

    def cmd_set_config(self, cfg: int) -> None:
        packet = self._send(("S", "C", int(cfg) & 0xFF), validator=lambda resp: self._is_ok_response(resp, "c"))
        if not self._is_ok_response(packet, "c"):
            raise RuntimeError(f"set_config unexpected response={packet}")

    def cmd_insert_enable(self) -> None:
        packet = self._send(("S", "A", 0x0D), validator=lambda resp: self._is_ok_response(resp, "a"))
        if not self._is_ok_response(packet, "a"):
            raise RuntimeError(f"insert_enable unexpected response={packet}")

    def cmd_insert_disable(self) -> None:
        packet = self._send(("S", "A", 0x0E), validator=lambda resp: self._is_ok_response(resp, "a"))
        if not self._is_ok_response(packet, "a"):
            raise RuntimeError(f"insert_disable unexpected response={packet}")

    def cmd_reset(self) -> None:
        packet = self._send(("R", "S", "T"), validator=lambda resp: self._is_ok_response(resp, "a"))
        if not self._is_ok_response(packet, "a"):
            raise RuntimeError(f"reset unexpected response={packet}")
        time.sleep(2.5)

    def _resolve_probe_bauds(self, profile_data: dict, fallback_baud: int) -> list[int]:
        values: list[int] = []
        for candidate in [fallback_baud, profile_data.get("baud"), self.settings.get("baud")]:
            try:
                parsed = int(candidate)
            except Exception:
                continue
            if parsed > 0:
                values.append(parsed)
        raw_probe = profile_data.get("probe_bauds")
        if isinstance(raw_probe, (list, tuple, set)):
            for item in raw_probe:
                try:
                    parsed = int(item)
                except Exception:
                    continue
                if parsed > 0:
                    values.append(parsed)
        dedup: list[int] = []
        for value in values:
            if value not in dedup:
                dedup.append(value)
        return dedup or [9600]

    def _resolve_probe_parities(self, profile_data: dict, fallback_parity: str) -> list[str]:
        values: list[str] = []
        for candidate in [fallback_parity, profile_data.get("parity"), self.settings.get("parity")]:
            text = str(candidate or "").strip().upper()
            if text in {"N", "E", "O"}:
                values.append(text)
        raw_probe = profile_data.get("probe_parities")
        if isinstance(raw_probe, (list, tuple, set)):
            for item in raw_probe:
                text = str(item or "").strip().upper()
                if text in {"N", "E", "O"}:
                    values.append(text)
        dedup: list[str] = []
        for value in values:
            if value not in dedup:
                dedup.append(value)
        return dedup or ["N"]

    def _resolve_probe_stopbits(self, profile_data: dict, fallback_stopbits: int) -> list[int]:
        values: list[int] = []
        for candidate in [fallback_stopbits, profile_data.get("stopbits"), self.settings.get("stopbits")]:
            try:
                parsed = int(candidate)
            except Exception:
                continue
            if parsed in {1, 2}:
                values.append(parsed)
        raw_probe = profile_data.get("probe_stopbits")
        if isinstance(raw_probe, (list, tuple, set)):
            for item in raw_probe:
                try:
                    parsed = int(item)
                except Exception:
                    continue
                if parsed in {1, 2}:
                    values.append(parsed)
        dedup: list[int] = []
        for value in values:
            if value not in dedup:
                dedup.append(value)
        return dedup or [1]

    def _resolve_probe_bytesizes(self, profile_data: dict, fallback_bytesize: int) -> list[int]:
        values: list[int] = []
        for candidate in [fallback_bytesize, profile_data.get("bytesize"), self.settings.get("bytesize")]:
            try:
                parsed = int(candidate)
            except Exception:
                continue
            if parsed in {7, 8}:
                values.append(parsed)
        raw_probe = profile_data.get("probe_bytesizes")
        if isinstance(raw_probe, (list, tuple, set)):
            for item in raw_probe:
                try:
                    parsed = int(item)
                except Exception:
                    continue
                if parsed in {7, 8}:
                    values.append(parsed)
        dedup: list[int] = []
        for value in values:
            if value not in dedup:
                dedup.append(value)
        return dedup or [8]

    def _open_serial_connection(
        self,
        port: str,
        baud: int,
        parity: Any,
        bytesize: int,
        stopbits: Any,
    ):
        return serial.Serial(
            port=normalize_serial_port(port),
            baudrate=int(baud),
            bytesize=int(bytesize),
            parity=parity,
            stopbits=stopbits,
            timeout=0.05,
            write_timeout=0.5,
        )

    def _auto_open_serial_connection(
        self,
        profile_data: dict,
        parity_text: str,
        bytesize: int,
        stopbits_value: int,
        fallback_baud: int,
    ) -> tuple[Any, str, int, str, int, int]:
        ports = _list_serial_port_names()
        if not ports:
            raise RuntimeError("bill auto-detect failed: no serial ports")
        bauds = self._resolve_probe_bauds(profile_data, fallback_baud)
        parity_candidates = self._resolve_probe_parities(profile_data, parity_text)
        stopbits_candidates = self._resolve_probe_stopbits(profile_data, stopbits_value)
        bytesize_candidates = self._resolve_probe_bytesizes(profile_data, bytesize)
        parity_map = {
            "N": serial.PARITY_NONE,
            "E": serial.PARITY_EVEN,
            "O": serial.PARITY_ODD,
        }
        last_error = "probe timeout"
        for raw_port in ports:
            for baud in bauds:
                for byte_candidate in bytesize_candidates:
                    for parity_candidate in parity_candidates:
                        for stop_candidate in stopbits_candidates:
                            conn = None
                            try:
                                stopbits = serial.STOPBITS_TWO if int(stop_candidate) == 2 else serial.STOPBITS_ONE
                                conn = self._open_serial_connection(
                                    raw_port,
                                    baud,
                                    parity_map.get(parity_candidate, serial.PARITY_NONE),
                                    int(byte_candidate),
                                    stopbits,
                                )
                                self._log(
                                    f"[BILL] probe port={raw_port} baud={baud} "
                                    f"mode={parity_candidate}{int(byte_candidate)}{int(stop_candidate)}"
                                )
                                send_cmd_with_retry(
                                    conn,
                                    ("G", "A", "?"),
                                    timeout=0.35,
                                    retries=1,
                                )
                                self._log(
                                    f"[BILL] auto-detect matched port={raw_port} baud={baud} "
                                    f"mode={parity_candidate}{int(byte_candidate)}{int(stop_candidate)}"
                                )
                                return (
                                    conn,
                                    normalize_serial_port(raw_port),
                                    int(baud),
                                    str(parity_candidate),
                                    int(stop_candidate),
                                    int(byte_candidate),
                                )
                            except Exception as exc:
                                last_error = str(exc)
                                if conn is not None:
                                    try:
                                        conn.close()
                                    except Exception:
                                        pass
                                continue
        raise RuntimeError(
            "bill auto-detect failed: "
            f"{last_error} (check device mode: RS-232 vs MDB/ccTalk)"
        )

    def run(self) -> None:
        if serial is None:
            self.failed.emit("pyserial not installed")
            return
        if not bool(self.settings.get("enabled", False)):
            self.failed.emit("bill_acceptor disabled")
            return

        profile_data = self._profile_data()
        profile_key = str(self.settings.get("profile", DEFAULT_BILL_ACCEPTOR_SETTINGS["profile"])).strip()
        strict_init = bool(profile_data.get("strict_init", True))
        supports_reset = bool(profile_data.get("supports_reset", True))
        supports_config_bits = bool(profile_data.get("supports_config_bits", True))
        supports_insert_control = bool(profile_data.get("supports_insert_control", True))
        requested_port = str(
            self.settings.get(
                "port",
                profile_data.get("default_port", DEFAULT_BILL_ACCEPTOR_SETTINGS["port"]),
            )
        ).strip()
        if not requested_port:
            requested_port = str(profile_data.get("default_port", DEFAULT_BILL_ACCEPTOR_SETTINGS["port"])).strip()
        baud = int(self.settings.get("baud", profile_data.get("baud", DEFAULT_BILL_ACCEPTOR_SETTINGS["baud"])))
        parity_text = str(profile_data.get("parity", "N")).strip().upper()
        bytesize = int(profile_data.get("bytesize", 8))
        stopbits_value = int(profile_data.get("stopbits", 1))
        parity_map = {
            "N": serial.PARITY_NONE,
            "E": serial.PARITY_EVEN,
            "O": serial.PARITY_ODD,
        }
        parity = parity_map.get(parity_text, serial.PARITY_NONE)
        stopbits = serial.STOPBITS_TWO if stopbits_value == 2 else serial.STOPBITS_ONE

        try:
            port = normalize_serial_port(requested_port)
            actual_baud = int(baud)
            if _is_auto_serial_port(requested_port):
                (
                    self._serial_conn,
                    port,
                    actual_baud,
                    parity_text,
                    stopbits_value,
                    bytesize,
                ) = self._auto_open_serial_connection(
                    profile_data=profile_data,
                    parity_text=parity_text,
                    bytesize=bytesize,
                    stopbits_value=stopbits_value,
                    fallback_baud=int(baud),
                )
            else:
                try:
                    self._serial_conn = self._open_serial_connection(
                        port=port,
                        baud=int(baud),
                        parity=parity,
                        bytesize=bytesize,
                        stopbits=stopbits,
                    )
                except SerialException:
                    if bool(profile_data.get("auto_fallback", False)):
                        self._log(f"[BILL] manual open failed on {requested_port}, fallback to AUTO probe")
                        (
                            self._serial_conn,
                            port,
                            actual_baud,
                            parity_text,
                            stopbits_value,
                            bytesize,
                        ) = self._auto_open_serial_connection(
                            profile_data=profile_data,
                            parity_text=parity_text,
                            bytesize=bytesize,
                            stopbits_value=stopbits_value,
                            fallback_baud=int(baud),
                        )
                    else:
                        raise
            self._log(
                f"[BILL] open port={port} {int(actual_baud)}{parity_text}{int(bytesize)}{stopbits_value} "
                f"profile={profile_key} strict_init={1 if strict_init else 0}"
            )

            if supports_reset:
                try:
                    self.cmd_reset()
                except Exception as exc:
                    if strict_init:
                        raise
                    self._log(f"[BILL] reset skipped: {exc}")

            if supports_config_bits:
                try:
                    cfg = self._resolve_config_byte()
                    self.cmd_set_config(cfg)
                    self._log(f"[BILL] set_config=0x{cfg:02X} ok")
                except Exception as exc:
                    if strict_init:
                        raise
                    self._log(f"[BILL] set_config skipped: {exc}")

            if supports_insert_control:
                try:
                    self.cmd_insert_enable()
                    self._insert_enabled = True
                    self._log("[BILL] insert_enable ok")
                except Exception as exc:
                    if strict_init:
                        raise
                    self._insert_enabled = False
                    self._log(f"[BILL] insert_enable skipped: {exc}")

            while self._running and not self.isInterruptionRequested():
                try:
                    status = self.cmd_get_status()
                    if self._last_status != status:
                        self._last_status = status
                    if status in self._accept_status_codes:
                        billdata = self.cmd_get_billdata()
                        amount = self._bill_to_amount_map.get(int(billdata))
                        if amount is not None:
                            self.bill_accepted.emit(int(amount), int(status), int(billdata))
                            self._log(
                                f"[BILL] status=0x{status:02X} -> billdata={int(billdata)} amount={int(amount)}"
                            )
                        else:
                            self._log(
                                f"[BILL] status=0x{status:02X} -> billdata={int(billdata)} amount=UNKNOWN"
                            )
                        if supports_insert_control:
                            try:
                                self.cmd_insert_enable()
                                self._insert_enabled = True
                                self._log("[BILL] insert_enable ok")
                            except Exception as exc:
                                if strict_init:
                                    raise
                                self._insert_enabled = False
                                self._log(f"[BILL] insert_enable retry failed: {exc}")
                    elif status >= 0x80:
                        error_code = self.cmd_get_error()
                        self._log(f"[BILL] status=0x{status:02X} error=0x{error_code:02X}")
                except Exception as poll_exc:
                    self._log(f"[BILL] poll error: {poll_exc}")
                    time.sleep(0.2)
                time.sleep(0.08)
        except SerialException as exc:
            self.failed.emit(f"serial failed: {exc}")
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            if self._serial_conn is not None:
                if self._insert_enabled:
                    try:
                        self.cmd_insert_disable()
                        self._log("[BILL] insert_disable ok")
                    except Exception as disable_exc:
                        self._log(f"[BILL] insert_disable failed: {disable_exc}")
                try:
                    self._serial_conn.close()
                except Exception:
                    pass
                self._serial_conn = None
            self._insert_enabled = False


class AdminScreen(QWidget):
    def __init__(self, main_window: "KioskMainWindow") -> None:
        super().__init__()
        self.main_window = main_window
        self.screen_name = "admin"
        self.hotspots: list[Hotspot] = []
        self._loading_bill_controls = False
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._clear_status)

        self.setStyleSheet(
            "QWidget { background: #eef2f7; color: #0f172a; font-size: 15px; } "
            "QLabel#title { font-size: 32px; font-weight: 800; color: #0b1324; } "
            "QLabel#section { font-size: 17px; font-weight: 800; color: #1e3a8a; "
            "padding: 8px 12px; border-radius: 8px; background: #e9f0ff; border: 1px solid #cfe0ff; } "
            "QLabel#status { color: #0a7a55; font-size: 16px; font-weight: 700; padding: 4px 6px; } "
            "QScrollArea { border: none; background: transparent; } "
            "QWidget#adminCard { background: #ffffff; border: 1px solid #dbe3ef; border-radius: 14px; } "
            "QLineEdit, QComboBox, QSpinBox, QTextEdit { background: #ffffff; color: #0f172a; "
            "border: 1px solid #c4cfdd; border-radius: 8px; padding: 6px 8px; min-height: 34px; } "
            "QComboBox::drop-down { border: none; width: 24px; } "
            "QCheckBox { spacing: 8px; } "
            "QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #97a6ba; "
            "border-radius: 4px; background: #fff; } "
            "QCheckBox::indicator:checked { background: #2563eb; border-color: #1d4ed8; } "
            "QPushButton { min-height: 42px; padding: 8px 14px; border-radius: 10px; "
            "font-weight: 700; background: #1d4ed8; color: #ffffff; border: none; } "
            "QPushButton:hover { background: #1e40af; } "
            "QPushButton:pressed { background: #1e3a8a; } "
            "QPushButton#secondaryBtn { background: #334155; } "
            "QPushButton#secondaryBtn:hover { background: #1f2937; } "
            "QPushButton#dangerBtn { background: #b91c1c; } "
            "QPushButton#dangerBtn:hover { background: #991b1b; } "
            "QScrollBar:vertical { width: 16px; background: #e6edf7; border-radius: 7px; } "
            "QScrollBar::handle:vertical { background: #8fa2bc; min-height: 36px; border-radius: 7px; } "
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 24, 36, 24)
        root_layout.setSpacing(12)

        title = QLabel("Admin Settings", self)
        title.setObjectName("title")
        title.setAlignment(ALIGN_CENTER)
        root_layout.addWidget(title)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        if hasattr(Qt, "ScrollBarPolicy"):
            self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_content = QWidget(self._scroll_area)
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_content.setObjectName("adminCard")
        self._scroll_layout.setContentsMargins(18, 18, 18, 18)
        self._scroll_layout.setSpacing(16)
        self._scroll_area.setWidget(self._scroll_content)
        root_layout.addWidget(self._scroll_area, 1)

        form = QFormLayout()
        if hasattr(Qt, "AlignmentFlag"):
            label_align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        else:
            label_align = Qt.AlignLeft | Qt.AlignVCenter
        form.setLabelAlignment(label_align)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(10)

        self.test_mode_cb = QCheckBox(self)
        self.allow_dummy_cb = QCheckBox(self)
        self.debug_fullscreen_shutter_cb = QCheckBox(self)
        self.print_dry_run_cb = QCheckBox(self)
        self.upload_dry_run_cb = QCheckBox(self)
        self.qr_enabled_cb = QCheckBox(self)
        self.printing_enabled_cb = QCheckBox(self)
        self.printing_dry_run_cb = QCheckBox(self)
        self.payment_cash_cb = QCheckBox(self)
        self.payment_card_cb = QCheckBox(self)
        self.payment_coupon_cb = QCheckBox(self)
        self.mode_celebrity_cb = QCheckBox(self)
        self.mode_ai_cb = QCheckBox(self)
        self.ai_style_ids: list[str] = list(DEFAULT_AI_STYLE_PRESETS.keys())[:4]
        self.ai_style_enabled_inputs: dict[str, QCheckBox] = {}
        self.ai_style_order_inputs: dict[str, QSpinBox] = {}
        self.ai_style_name_ko_inputs: dict[str, QLineEdit] = {}
        self.ai_style_name_en_inputs: dict[str, QLineEdit] = {}
        self.ai_style_prompt_inputs: dict[str, QTextEdit] = {}
        self.ai_style_widget = QWidget(self)
        self.ai_style_grid = QGridLayout(self.ai_style_widget)
        self.ai_style_grid.setContentsMargins(0, 0, 0, 0)
        self.ai_style_grid.setHorizontalSpacing(10)
        self.ai_style_grid.setVerticalSpacing(8)
        self.ai_style_grid.addWidget(QLabel("Style ID", self.ai_style_widget), 0, 0)
        self.ai_style_grid.addWidget(QLabel("활성", self.ai_style_widget), 0, 1)
        self.ai_style_grid.addWidget(QLabel("순서", self.ai_style_widget), 0, 2)
        self.ai_style_grid.addWidget(QLabel("표시명(한글)", self.ai_style_widget), 0, 3)
        self.ai_style_grid.addWidget(QLabel("Display (EN)", self.ai_style_widget), 0, 4)
        self.ai_style_grid.addWidget(QLabel("Prompt", self.ai_style_widget), 0, 5)
        display_names = ["first", "second", "third", "fourth"]
        for row, style_id in enumerate(self.ai_style_ids, start=1):
            display_id = display_names[row - 1] if row - 1 < len(display_names) else f"style-{row}"
            id_label = QLabel(display_id, self.ai_style_widget)
            enabled_input = QCheckBox(self.ai_style_widget)
            enabled_input.setChecked(True)
            order_input = QSpinBox(self.ai_style_widget)
            order_input.setRange(1, 99)
            order_input.setValue(row)
            ko_input = QLineEdit(self.ai_style_widget)
            en_input = QLineEdit(self.ai_style_widget)
            prompt_input = QTextEdit(self.ai_style_widget)
            prompt_input.setAcceptRichText(False)
            prompt_input.setMinimumHeight(72)
            prompt_input.setMaximumHeight(110)
            self.ai_style_enabled_inputs[style_id] = enabled_input
            self.ai_style_order_inputs[style_id] = order_input
            self.ai_style_name_ko_inputs[style_id] = ko_input
            self.ai_style_name_en_inputs[style_id] = en_input
            self.ai_style_prompt_inputs[style_id] = prompt_input
            self.ai_style_grid.addWidget(id_label, row, 0)
            self.ai_style_grid.addWidget(enabled_input, row, 1)
            self.ai_style_grid.addWidget(order_input, row, 2)
            self.ai_style_grid.addWidget(ko_input, row, 3)
            self.ai_style_grid.addWidget(en_input, row, 4)
            self.ai_style_grid.addWidget(prompt_input, row, 5)
        self.bill_enabled_cb = QCheckBox(self)
        self.bill_profile_combo = QComboBox(self)
        self.bill_port_combo = QComboBox(self)
        self.pricing_prefix_input = QLineEdit(self)
        self.pricing_prefix_input.setPlaceholderText("KRW / ₩")
        self.pricing_prefix_input.setMaxLength(16)
        self.pricing_default_price = int(DEFAULT_PRICING_SETTINGS["default_price"])
        self.pricing_layout_ids: list[str] = []
        self.pricing_layout_inputs: dict[str, QLineEdit] = {}
        self.pricing_layout_widget = QWidget(self)
        self.pricing_layout_grid = QGridLayout(self.pricing_layout_widget)
        self.pricing_layout_grid.setContentsMargins(0, 0, 0, 0)
        self.pricing_layout_grid.setHorizontalSpacing(10)
        self.pricing_layout_grid.setVerticalSpacing(6)
        self.print_printer_ds620_combo = QComboBox(self)
        self.print_printer_rx1hs_combo = QComboBox(self)
        self.print_printer_ds620_combo.setEditable(True)
        self.print_printer_rx1hs_combo.setEditable(True)
        self.print_form_ds620_4x6_combo = QComboBox(self)
        self.print_form_ds620_2x6_combo = QComboBox(self)
        self.print_form_rx1hs_4x6_combo = QComboBox(self)
        self.print_form_rx1hs_2x6_combo = QComboBox(self)
        self.print_resolved_ds620_input = QLineEdit(self)
        self.print_resolved_ds620_input.setReadOnly(True)
        self.print_resolved_rx1hs_input = QLineEdit(self)
        self.print_resolved_rx1hs_input.setReadOnly(True)
        self.print_printer_refresh_btn = QPushButton("프린터 목록 새로고침", self)
        self.print_test_ds620_btn = QPushButton("Test Print (DS620)", self)
        self.print_test_rx1hs_btn = QPushButton("Test Print (RX1HS)", self)
        self.print_health_ds620_btn = QPushButton("프린터 상태 (DS620)", self)
        self.print_health_rx1hs_btn = QPushButton("프린터 상태 (RX1HS)", self)
        self.log_path_input = QLineEdit(self)
        self.log_path_input.setReadOnly(True)
        self.log_refresh_btn = QPushButton("로그 경로 새로고침", self)
        self.log_open_btn = QPushButton("로그 폴더 열기", self)
        self.print_printer_ds620_combo.currentTextChanged.connect(
            lambda _text: self._refresh_print_form_controls()
        )
        self.print_printer_rx1hs_combo.currentTextChanged.connect(
            lambda _text: self._refresh_print_form_controls()
        )
        self.print_printer_refresh_btn.clicked.connect(self._on_refresh_printers_clicked)
        self.print_test_ds620_btn.clicked.connect(lambda: self._on_test_print_clicked("DS620"))
        self.print_test_rx1hs_btn.clicked.connect(lambda: self._on_test_print_clicked("RX1HS"))
        self.print_health_ds620_btn.clicked.connect(
            lambda: self._on_check_printer_health_clicked("DS620")
        )
        self.print_health_rx1hs_btn.clicked.connect(
            lambda: self._on_check_printer_health_clicked("RX1HS")
        )
        self.log_refresh_btn.clicked.connect(self._on_refresh_log_path_clicked)
        self.log_open_btn.clicked.connect(self._on_open_log_folder_clicked)
        self.bill_denom_cbs: dict[str, QCheckBox] = {}
        for denom in ("1000", "5000", "10000", "50000"):
            self.bill_denom_cbs[denom] = QCheckBox(denom, self)

        for profile_key, profile in BILL_PROFILES.items():
            label = str(profile.get("label", profile_key))
            self.bill_profile_combo.addItem(label, profile_key)
        self.bill_profile_combo.currentIndexChanged.connect(self._on_bill_profile_changed)
        self.bill_port_combo.setEditable(False)

        self.camera_backend_combo = QComboBox(self)
        self.camera_backend_combo.addItems(["auto", "edsdk", "dummy"])

        self.capture_slots_override_combo = QComboBox(self)
        self.capture_slots_override_combo.addItems(["auto", "4", "6", "8", "9", "10"])

        self.countdown_spin = QSpinBox(self)
        self.countdown_spin.setRange(0, 10)

        form.addRow(self._make_section_label("기본 설정 / Runtime"))
        form.addRow("test_mode", self.test_mode_cb)
        form.addRow("camera_backend", self.camera_backend_combo)
        form.addRow("allow_dummy_when_camera_fail", self.allow_dummy_cb)
        form.addRow("countdown_seconds", self.countdown_spin)
        form.addRow("capture_slots_override", self.capture_slots_override_combo)
        form.addRow("debug_fullscreen_shutter", self.debug_fullscreen_shutter_cb)
        form.addRow("print_dry_run", self.print_dry_run_cb)
        form.addRow("upload_dry_run", self.upload_dry_run_cb)
        form.addRow("qr_enabled", self.qr_enabled_cb)
        form.addRow(self._make_section_label("프린팅 / Printing"))
        form.addRow("printing_enabled", self.printing_enabled_cb)
        form.addRow("printing_dry_run", self.printing_dry_run_cb)
        form.addRow("printer_DS620", self.print_printer_ds620_combo)
        form.addRow("DS620 form_4x6", self.print_form_ds620_4x6_combo)
        form.addRow("DS620 form_2x6", self.print_form_ds620_2x6_combo)
        form.addRow("DS620 resolved", self.print_resolved_ds620_input)
        form.addRow("printer_RX1HS", self.print_printer_rx1hs_combo)
        form.addRow("RX1HS form_4x6", self.print_form_rx1hs_4x6_combo)
        form.addRow("RX1HS form_2x6", self.print_form_rx1hs_2x6_combo)
        form.addRow("RX1HS resolved", self.print_resolved_rx1hs_input)
        form.addRow(self._make_section_label("결제/모드 / Payment & Mode"))
        form.addRow("pay_cash", self.payment_cash_cb)
        form.addRow("pay_card", self.payment_card_cb)
        form.addRow("pay_coupon", self.payment_coupon_cb)
        form.addRow("mode_celebrity_enabled", self.mode_celebrity_cb)
        form.addRow("mode_ai_enabled", self.mode_ai_cb)
        form.addRow(self._make_section_label("AI 스타일 / AI Styles"))
        form.addRow("ai_styles", self.ai_style_widget)
        form.addRow(self._make_section_label("지폐 인식기 / Bill Acceptor"))
        form.addRow("bill_enabled", self.bill_enabled_cb)
        form.addRow("bill_profile", self.bill_profile_combo)
        form.addRow("bill_port", self.bill_port_combo)
        denoms_row = QWidget(self)
        denoms_layout = QHBoxLayout(denoms_row)
        denoms_layout.setContentsMargins(0, 0, 0, 0)
        denoms_layout.setSpacing(10)
        for denom in ("1000", "5000", "10000", "50000"):
            denoms_layout.addWidget(self.bill_denom_cbs[denom])
        denoms_layout.addStretch(1)
        form.addRow("bill_denoms", denoms_row)
        form.addRow(self._make_section_label("가격 / Pricing"))
        form.addRow("pricing_prefix", self.pricing_prefix_input)
        form.addRow("pricing_layouts", self.pricing_layout_widget)
        print_button_row = QWidget(self)
        print_button_layout = QHBoxLayout(print_button_row)
        print_button_layout.setContentsMargins(0, 0, 0, 0)
        print_button_layout.setSpacing(8)
        print_button_layout.addWidget(self.print_printer_refresh_btn)
        print_button_layout.addWidget(self.print_test_ds620_btn)
        print_button_layout.addWidget(self.print_test_rx1hs_btn)
        print_button_layout.addWidget(self.print_health_ds620_btn)
        print_button_layout.addWidget(self.print_health_rx1hs_btn)
        form.addRow("printing_tools", print_button_row)

        form.addRow(self._make_section_label("로그 / Logs"))
        form.addRow("runtime_log_file", self.log_path_input)
        log_button_row = QWidget(self)
        log_button_layout = QHBoxLayout(log_button_row)
        log_button_layout.setContentsMargins(0, 0, 0, 0)
        log_button_layout.setSpacing(8)
        log_button_layout.addWidget(self.log_refresh_btn)
        log_button_layout.addWidget(self.log_open_btn)
        form.addRow("log_tools", log_button_row)
        self._scroll_layout.addLayout(form)

        bill_test_row = QHBoxLayout()
        bill_test_row.setSpacing(10)
        self.bill_test_start_btn = QPushButton("Bill 테스트 시작", self)
        self.bill_test_stop_btn = QPushButton("Bill 테스트 정지", self)
        self.bill_test_start_btn.clicked.connect(self._on_bill_test_start)
        self.bill_test_stop_btn.clicked.connect(self._on_bill_test_stop)
        bill_test_row.addWidget(self.bill_test_start_btn)
        bill_test_row.addWidget(self.bill_test_stop_btn)
        self._scroll_layout.addLayout(bill_test_row)

        self.status_label = QLabel("", self)
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(ALIGN_CENTER)
        self._scroll_layout.addWidget(self.status_label)

        jump_row = QHBoxLayout()
        jump_row.setSpacing(10)
        self.jump_screen_combo = QComboBox(self)
        self.jump_screen_combo.addItems(
            [
                "start",
                "frame_select",
                "how_many_prints",
                "payment_method",
                "coupon_input",
                "payment_complete_success",
                "camera",
                "after_camera_loading",
                "select_photo",
                "select_design",
                "preview",
                "loading",
                "qr_generating",
                "qr_code",
                "thank_you",
            ]
        )
        self.jump_button = QPushButton("이동", self)
        self.jump_button.clicked.connect(self._on_jump_clicked)
        jump_row.addWidget(QLabel("화면 점프", self))
        jump_row.addWidget(self.jump_screen_combo, 1)
        jump_row.addWidget(self.jump_button)
        self._scroll_layout.addLayout(jump_row)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        self.save_button = QPushButton("저장", self)
        self.cancel_button = QPushButton("취소/뒤로", self)
        self.reset_button = QPushButton("상태리셋", self)
        self.exit_app_button = QPushButton("나가기(프로그램 종료)", self)
        self.save_button.clicked.connect(self._on_save_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.exit_app_button.clicked.connect(self._on_exit_app_clicked)
        self.cancel_button.setObjectName("secondaryBtn")
        self.reset_button.setObjectName("secondaryBtn")
        self.exit_app_button.setObjectName("dangerBtn")
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.exit_app_button)
        self._scroll_layout.addLayout(buttons)
        self._scroll_layout.addStretch(1)

    def _make_section_label(self, text: str) -> QLabel:
        label = QLabel(str(text), self)
        label.setObjectName("section")
        label.setAlignment(ALIGN_CENTER)
        return label

    def set_hotspots(self, hotspots: list[Hotspot]) -> None:
        self.hotspots = hotspots

    def set_overlay_visible(self, visible: bool) -> None:
        _ = visible

    def load_settings(
        self,
        settings: dict,
        payment_methods: Optional[dict] = None,
        modes: Optional[dict] = None,
        ai_styles: Optional[dict] = None,
        bill_acceptor: Optional[dict] = None,
        pricing: Optional[dict] = None,
        layout_ids: Optional[list[str]] = None,
        printing: Optional[dict] = None,
        printer_names: Optional[list[str]] = None,
    ) -> None:
        self.test_mode_cb.setChecked(bool(settings.get("test_mode", False)))
        self.allow_dummy_cb.setChecked(
            bool(
                settings.get(
                    "allow_dummy_when_camera_fail",
                    bool(DEFAULT_ADMIN_SETTINGS["allow_dummy_when_camera_fail"]),
                )
            )
        )
        self.debug_fullscreen_shutter_cb.setChecked(
            bool(settings.get("debug_fullscreen_shutter", False))
        )
        self.print_dry_run_cb.setChecked(bool(settings.get("print_dry_run", True)))
        self.upload_dry_run_cb.setChecked(bool(settings.get("upload_dry_run", True)))
        self.qr_enabled_cb.setChecked(bool(settings.get("qr_enabled", True)))

        backend = str(settings.get("camera_backend", "auto"))
        backend_index = self.camera_backend_combo.findText(backend)
        self.camera_backend_combo.setCurrentIndex(max(0, backend_index))

        capture_override = settings.get("capture_slots_override", "auto")
        capture_text = str(capture_override)
        capture_index = self.capture_slots_override_combo.findText(capture_text)
        self.capture_slots_override_combo.setCurrentIndex(max(0, capture_index))

        self.countdown_spin.setValue(max(0, min(10, int(settings.get("countdown_seconds", 3)))))
        methods = dict(DEFAULT_PAYMENT_METHODS)
        if isinstance(payment_methods, dict):
            methods["cash"] = bool(payment_methods.get("cash", methods["cash"]))
            methods["card"] = bool(payment_methods.get("card", methods["card"]))
            methods["coupon"] = bool(payment_methods.get("coupon", methods["coupon"]))
        self.payment_cash_cb.setChecked(methods["cash"])
        self.payment_card_cb.setChecked(methods["card"])
        self.payment_coupon_cb.setChecked(methods["coupon"])
        mode_settings = dict(DEFAULT_MODE_SETTINGS)
        if isinstance(modes, dict):
            mode_settings["celebrity_enabled"] = bool(
                modes.get("celebrity_enabled", mode_settings["celebrity_enabled"])
            )
            mode_settings["ai_enabled"] = bool(modes.get("ai_enabled", mode_settings["ai_enabled"]))
        self.mode_celebrity_cb.setChecked(bool(mode_settings["celebrity_enabled"]))
        self.mode_ai_cb.setChecked(bool(mode_settings["ai_enabled"]))
        self._load_ai_style_controls(ai_styles)
        self._load_printing_controls(printing, printer_names)
        self._load_pricing_controls(pricing, layout_ids)
        self._load_bill_acceptor_controls(bill_acceptor)
        self._refresh_bill_test_buttons()
        self._clear_status()

    def _collect_settings(self) -> dict:
        capture_override_text = self.capture_slots_override_combo.currentText().strip().lower()
        if capture_override_text == "auto":
            capture_override: object = "auto"
        else:
            capture_override = int(capture_override_text)
        return {
            "test_mode": self.test_mode_cb.isChecked(),
            "camera_backend": self.camera_backend_combo.currentText().strip().lower(),
            "allow_dummy_when_camera_fail": self.allow_dummy_cb.isChecked(),
            "countdown_seconds": int(self.countdown_spin.value()),
            "capture_slots_override": capture_override,
            "debug_fullscreen_shutter": self.debug_fullscreen_shutter_cb.isChecked(),
            "print_dry_run": self.print_dry_run_cb.isChecked(),
            "upload_dry_run": self.upload_dry_run_cb.isChecked(),
            "qr_enabled": self.qr_enabled_cb.isChecked(),
        }

    def _collect_payment_methods(self) -> dict:
        return {
            "cash": self.payment_cash_cb.isChecked(),
            "card": self.payment_card_cb.isChecked(),
            "coupon": self.payment_coupon_cb.isChecked(),
        }

    def _collect_modes_settings(self) -> dict:
        return {
            "celebrity_enabled": self.mode_celebrity_cb.isChecked(),
            "ai_enabled": self.mode_ai_cb.isChecked(),
        }

    def _load_ai_style_controls(self, ai_styles: Optional[dict]) -> None:
        defaults = DEFAULT_AI_STYLE_PRESETS
        incoming = ai_styles if isinstance(ai_styles, dict) else {}
        for row, style_id in enumerate(self.ai_style_ids, start=1):
            style_defaults = defaults.get(style_id, {})
            style_current = incoming.get(style_id) if isinstance(incoming, dict) else {}
            style_current = style_current if isinstance(style_current, dict) else {}
            ko = str(style_current.get("label_ko", style_defaults.get("label_ko", style_id))).strip()
            en = str(style_current.get("label_en", style_defaults.get("label_en", ko or style_id))).strip()
            prompt = str(style_current.get("prompt", style_defaults.get("prompt", ""))).strip()
            enabled = bool(style_current.get("enabled", True))
            try:
                order = int(style_current.get("order", row))
            except Exception:
                order = row

            enabled_input = self.ai_style_enabled_inputs.get(style_id)
            order_input = self.ai_style_order_inputs.get(style_id)
            ko_input = self.ai_style_name_ko_inputs.get(style_id)
            en_input = self.ai_style_name_en_inputs.get(style_id)
            prompt_input = self.ai_style_prompt_inputs.get(style_id)
            if isinstance(enabled_input, QCheckBox):
                enabled_input.setChecked(enabled)
            if isinstance(order_input, QSpinBox):
                order_input.setValue(max(1, min(99, order)))
            if isinstance(ko_input, QLineEdit):
                ko_input.setText(ko or style_id)
            if isinstance(en_input, QLineEdit):
                en_input.setText(en or ko or style_id)
            if isinstance(prompt_input, QTextEdit):
                prompt_input.setPlainText(prompt)

    def _collect_ai_style_settings(self) -> dict:
        result: dict[str, dict[str, Any]] = {}
        for style_id in self.ai_style_ids:
            defaults = DEFAULT_AI_STYLE_PRESETS.get(style_id, {})
            enabled_input = self.ai_style_enabled_inputs.get(style_id)
            order_input = self.ai_style_order_inputs.get(style_id)
            ko_input = self.ai_style_name_ko_inputs.get(style_id)
            en_input = self.ai_style_name_en_inputs.get(style_id)
            prompt_input = self.ai_style_prompt_inputs.get(style_id)

            enabled = enabled_input.isChecked() if isinstance(enabled_input, QCheckBox) else True
            order = int(order_input.value()) if isinstance(order_input, QSpinBox) else 1
            ko = (
                ko_input.text().strip()
                if isinstance(ko_input, QLineEdit)
                else str(defaults.get("label_ko", style_id))
            )
            en = (
                en_input.text().strip()
                if isinstance(en_input, QLineEdit)
                else str(defaults.get("label_en", ko or style_id))
            )
            prompt = (
                prompt_input.toPlainText().strip()
                if isinstance(prompt_input, QTextEdit)
                else str(defaults.get("prompt", ""))
            )
            result[style_id] = {
                "label_ko": ko or str(defaults.get("label_ko", style_id)) or style_id,
                "label_en": en or str(defaults.get("label_en", ko or style_id)) or ko or style_id,
                "prompt": prompt or str(defaults.get("prompt", "Stylized portrait")) or "Stylized portrait",
                "enabled": bool(enabled),
                "order": max(1, int(order)),
            }
        return result

    @staticmethod
    def _set_combo_items(combo: QComboBox, names: list[str], selected: str = "") -> None:
        current_text = str(selected or "").strip()
        values = [str(v).strip() for v in names if str(v).strip()]
        if current_text and current_text not in values:
            values.append(current_text)
        values = sorted(set(values))
        combo.blockSignals(True)
        combo.clear()
        for name in values:
            combo.addItem(name)
        if current_text:
            idx = combo.findText(current_text)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _list_forms_for_printer(self, printer_name: str) -> list[str]:
        name = str(printer_name or "").strip()
        if not name:
            return []
        if hasattr(self.main_window, "list_printer_forms"):
            return list(self.main_window.list_printer_forms(name))
        return []

    def _refresh_print_form_controls(
        self,
        ds620_form_4x6: str = "",
        ds620_form_2x6: str = "",
        rx1hs_form_4x6: str = "",
        rx1hs_form_2x6: str = "",
    ) -> None:
        ds620_printer = self.print_printer_ds620_combo.currentText().strip()
        rx1hs_printer = self.print_printer_rx1hs_combo.currentText().strip()

        ds620_forms = self._list_forms_for_printer(ds620_printer)
        rx1hs_forms = self._list_forms_for_printer(rx1hs_printer)

        selected_ds620_4x6 = (
            str(ds620_form_4x6).strip()
            or self.print_form_ds620_4x6_combo.currentText().strip()
            or "4x6"
        )
        selected_ds620_2x6 = (
            str(ds620_form_2x6).strip()
            or self.print_form_ds620_2x6_combo.currentText().strip()
            or "2x6"
        )
        selected_rx1hs_4x6 = (
            str(rx1hs_form_4x6).strip()
            or self.print_form_rx1hs_4x6_combo.currentText().strip()
            or "4x6"
        )
        selected_rx1hs_2x6 = (
            str(rx1hs_form_2x6).strip()
            or self.print_form_rx1hs_2x6_combo.currentText().strip()
            or "2x6"
        )

        self._set_combo_items(self.print_form_ds620_4x6_combo, ds620_forms, selected_ds620_4x6)
        self._set_combo_items(self.print_form_ds620_2x6_combo, ds620_forms, selected_ds620_2x6)
        self._set_combo_items(self.print_form_rx1hs_4x6_combo, rx1hs_forms, selected_rx1hs_4x6)
        self._set_combo_items(self.print_form_rx1hs_2x6_combo, rx1hs_forms, selected_rx1hs_2x6)
        self._refresh_resolved_printer_labels()

    def _refresh_resolved_printer_labels(self) -> None:
        ds620_resolved = ""
        rx1hs_resolved = ""
        if hasattr(self.main_window, "resolve_admin_printer_name"):
            try:
                current = self._collect_printing_settings()
                ds620_resolved = str(
                    self.main_window.resolve_admin_printer_name("DS620", current)
                ).strip()
                rx1hs_resolved = str(
                    self.main_window.resolve_admin_printer_name("RX1HS", current)
                ).strip()
            except Exception:
                ds620_resolved = ""
                rx1hs_resolved = ""
        self.print_resolved_ds620_input.setText(ds620_resolved)
        self.print_resolved_rx1hs_input.setText(rx1hs_resolved)

    def _refresh_log_path(self) -> None:
        path = ""
        if hasattr(self.main_window, "get_runtime_log_file_path"):
            try:
                path = str(self.main_window.get_runtime_log_file_path() or "").strip()
            except Exception:
                path = ""
        self.log_path_input.setText(path)

    def _load_printing_controls(self, printing: Optional[dict], printer_names: Optional[list[str]]) -> None:
        settings = printing if isinstance(printing, dict) else {}
        self.printing_enabled_cb.setChecked(bool(settings.get("enabled", True)))
        self.printing_dry_run_cb.setChecked(bool(settings.get("dry_run", False)))
        printers = settings.get("printers") if isinstance(settings.get("printers"), dict) else {}
        ds620_name = ""
        rx1hs_name = ""
        ds620_form_4x6 = "4x6"
        ds620_form_2x6 = "2x6"
        rx1hs_form_4x6 = "4x6"
        rx1hs_form_2x6 = "2x6"
        if isinstance(printers, dict):
            ds620 = printers.get("DS620")
            rx1hs = printers.get("RX1HS")
            if isinstance(ds620, dict):
                ds620_name = str(ds620.get("win_name", "")).strip()
                ds620_form_4x6 = str(ds620.get("form_4x6", ds620_form_4x6)).strip() or "4x6"
                ds620_form_2x6 = str(ds620.get("form_2x6", ds620_form_2x6)).strip() or "2x6"
            if isinstance(rx1hs, dict):
                rx1hs_name = str(rx1hs.get("win_name", "")).strip()
                rx1hs_form_4x6 = str(rx1hs.get("form_4x6", rx1hs_form_4x6)).strip() or "4x6"
                rx1hs_form_2x6 = str(rx1hs.get("form_2x6", rx1hs_form_2x6)).strip() or "2x6"
        self._set_combo_items(self.print_printer_ds620_combo, list(printer_names or []), ds620_name)
        self._set_combo_items(self.print_printer_rx1hs_combo, list(printer_names or []), rx1hs_name)
        self._refresh_print_form_controls(
            ds620_form_4x6=ds620_form_4x6,
            ds620_form_2x6=ds620_form_2x6,
            rx1hs_form_4x6=rx1hs_form_4x6,
            rx1hs_form_2x6=rx1hs_form_2x6,
        )
        self._refresh_log_path()

    def _collect_printing_settings(self) -> dict:
        current = (
            self.main_window.get_printing_settings()
            if hasattr(self.main_window, "get_printing_settings")
            else dict(DEFAULT_PRINTING_SETTINGS)
        )
        current_printers = current.get("printers", {}) if isinstance(current, dict) else {}
        current_ds620 = current_printers.get("DS620", {}) if isinstance(current_printers, dict) else {}
        current_rx1hs = current_printers.get("RX1HS", {}) if isinstance(current_printers, dict) else {}
        ds620_form_4x6 = self.print_form_ds620_4x6_combo.currentText().strip() or "4x6"
        ds620_form_2x6 = self.print_form_ds620_2x6_combo.currentText().strip() or "2x6"
        rx1hs_form_4x6 = self.print_form_rx1hs_4x6_combo.currentText().strip() or "4x6"
        rx1hs_form_2x6 = self.print_form_rx1hs_2x6_combo.currentText().strip() or "2x6"
        default_model = str(current.get("default_model", "DS620")).strip().upper()
        if default_model not in {"DS620", "RX1HS"}:
            default_model = "DS620"
        ds620_name = self.print_printer_ds620_combo.currentText().strip()
        rx1hs_name = self.print_printer_rx1hs_combo.currentText().strip()
        if default_model == "DS620" and (not ds620_name) and rx1hs_name:
            default_model = "RX1HS"
        return {
            "enabled": self.printing_enabled_cb.isChecked(),
            "dry_run": self.printing_dry_run_cb.isChecked(),
            "printers": {
                "DS620": {
                    "win_name": ds620_name,
                    "form_4x6": ds620_form_4x6 or str(current_ds620.get("form_4x6", "4x6")),
                    "form_2x6": ds620_form_2x6 or str(current_ds620.get("form_2x6", "2x6")),
                },
                "RX1HS": {
                    "win_name": rx1hs_name,
                    "form_4x6": rx1hs_form_4x6 or str(current_rx1hs.get("form_4x6", "4x6")),
                    "form_2x6": rx1hs_form_2x6 or str(current_rx1hs.get("form_2x6", "2x6")),
                },
            },
            "default_model": default_model,
        }

    def _load_pricing_controls(self, pricing: Optional[dict], layout_ids: Optional[list[str]]) -> None:
        settings = pricing if isinstance(pricing, dict) else {}
        prefix = str(settings.get("currency_prefix", DEFAULT_PRICING_SETTINGS["currency_prefix"]))
        self.pricing_prefix_input.setText(prefix)

        try:
            default_price = int(settings.get("default_price", DEFAULT_PRICING_SETTINGS["default_price"]))
        except Exception:
            default_price = int(DEFAULT_PRICING_SETTINGS["default_price"])
        self.pricing_default_price = max(0, default_price)

        layout_prices = settings.get("layouts") if isinstance(settings.get("layouts"), dict) else {}
        detected = [str(v).strip() for v in (layout_ids or []) if str(v).strip()]
        for default_layout in DEFAULT_FRAME_LAYOUT_IDS:
            layout_key = str(default_layout or "").strip()
            if layout_key and layout_key not in detected:
                detected.append(layout_key)
        if not detected and isinstance(layout_prices, dict):
            detected = sorted(str(k).strip() for k in layout_prices.keys() if str(k).strip())
        if isinstance(layout_prices, dict):
            for key in layout_prices.keys():
                layout_key = str(key).strip()
                if layout_key and layout_key not in detected:
                    detected.append(layout_key)
        celeb_layout = str(DEFAULT_CELEBRITY_SETTINGS.get("layout_id", "2461")).strip() or "2461"
        if celeb_layout not in detected:
            detected.append(celeb_layout)
        ai_layout = str(AI_LAYOUT_ID).strip()
        if ai_layout and ai_layout not in detected:
            detected.append(ai_layout)
        self.pricing_layout_ids = sorted(set(detected))

        while self.pricing_layout_grid.count():
            item = self.pricing_layout_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.pricing_layout_inputs = {}

        row = 0
        for layout_id in self.pricing_layout_ids:
            name_label = QLabel(self._pricing_layout_label(layout_id), self.pricing_layout_widget)
            price_input = QLineEdit(self.pricing_layout_widget)
            price_input.setValidator(QIntValidator(0, 999999, price_input))
            value = self.pricing_default_price
            if isinstance(layout_prices, dict):
                try:
                    value = int(layout_prices.get(layout_id, value))
                except Exception:
                    value = self.pricing_default_price
            price_input.setText(str(max(0, value)))
            self.pricing_layout_inputs[layout_id] = price_input
            self.pricing_layout_grid.addWidget(name_label, row, 0)
            self.pricing_layout_grid.addWidget(price_input, row, 1)
            row += 1

    def _pricing_layout_label(self, layout_id: str) -> str:
        layout_key = str(layout_id or "").strip()
        if not layout_key:
            return ""
        tags: list[str] = []
        celeb_layout = str(DEFAULT_CELEBRITY_SETTINGS.get("layout_id", "2461")).strip() or "2461"
        if hasattr(self.main_window, "get_celebrity_settings"):
            try:
                celeb_cfg = self.main_window.get_celebrity_settings()
                if isinstance(celeb_cfg, dict):
                    celeb_layout = str(
                        celeb_cfg.get("layout_id", DEFAULT_CELEBRITY_SETTINGS.get("layout_id", "2461"))
                    ).strip() or celeb_layout
            except Exception:
                pass
        if layout_key == celeb_layout:
            tags.append("유명인모드")
        if layout_key == AI_LAYOUT_ID:
            tags.append("AI모드")
        if not tags:
            return layout_key
        return f"{layout_key} ({' / '.join(tags)})"

    def _collect_pricing_settings(self) -> dict:
        prefix = self.pricing_prefix_input.text().strip()
        layouts: dict[str, int] = {}
        for layout_id in self.pricing_layout_ids:
            editor = self.pricing_layout_inputs.get(layout_id)
            raw = editor.text().strip() if isinstance(editor, QLineEdit) else ""
            try:
                amount = int(raw) if raw else int(self.pricing_default_price)
            except Exception:
                amount = int(self.pricing_default_price)
            layouts[layout_id] = max(0, amount)
        return {
            "currency_prefix": prefix,
            "default_price": int(self.pricing_default_price),
            "layouts": layouts,
        }

    def _current_bill_profile_key(self) -> str:
        idx = self.bill_profile_combo.currentIndex()
        data = self.bill_profile_combo.itemData(idx)
        key = str(data).strip() if data is not None else ""
        if key in BILL_PROFILES:
            return key
        text = self.bill_profile_combo.currentText().strip()
        if text in BILL_PROFILES:
            return text
        return str(DEFAULT_BILL_ACCEPTOR_SETTINGS["profile"])

    def _refresh_bill_ports(self, selected_port: Optional[str] = None) -> None:
        ports = []
        if hasattr(self.main_window, "list_serial_ports"):
            ports = list(self.main_window.list_serial_ports())
        selected = str(selected_port or "").strip()
        if _is_auto_serial_port(selected):
            selected = "AUTO"
        if "AUTO" not in ports:
            ports.insert(0, "AUTO")
        if selected and selected not in ports:
            ports.append(selected)
        if not ports:
            fallback = str(DEFAULT_BILL_ACCEPTOR_SETTINGS["port"])
            if fallback:
                ports = [fallback]
        self.bill_port_combo.blockSignals(True)
        self.bill_port_combo.clear()
        for port in ports:
            self.bill_port_combo.addItem(str(port))
        if selected:
            index = self.bill_port_combo.findText(selected)
            if index >= 0:
                self.bill_port_combo.setCurrentIndex(index)
        self.bill_port_combo.blockSignals(False)

    def _apply_bill_profile_defaults(self, profile_key: str) -> None:
        profile = BILL_PROFILES.get(profile_key, {})
        default_denoms = profile.get("default_denoms")
        if not isinstance(default_denoms, dict):
            default_denoms = DEFAULT_BILL_ACCEPTOR_SETTINGS["denoms"]
        for denom, cb in self.bill_denom_cbs.items():
            cb.setChecked(bool(default_denoms.get(denom, False)))
        default_port = str(profile.get("default_port", DEFAULT_BILL_ACCEPTOR_SETTINGS["port"])).strip()
        if default_port:
            normalized = "AUTO" if _is_auto_serial_port(default_port) else default_port
            index = self.bill_port_combo.findText(normalized)
            if index < 0:
                self.bill_port_combo.addItem(normalized)
                index = self.bill_port_combo.findText(normalized)
            if index >= 0:
                self.bill_port_combo.setCurrentIndex(index)

    def _on_bill_profile_changed(self, _index: int) -> None:
        if self._loading_bill_controls:
            return
        profile_key = self._current_bill_profile_key()
        self._apply_bill_profile_defaults(profile_key)

    def _load_bill_acceptor_controls(self, bill_acceptor: Optional[dict]) -> None:
        defaults = dict(DEFAULT_BILL_ACCEPTOR_SETTINGS)
        denoms_default = dict(DEFAULT_BILL_ACCEPTOR_SETTINGS["denoms"])
        incoming = bill_acceptor if isinstance(bill_acceptor, dict) else defaults
        enabled = bool(incoming.get("enabled", defaults["enabled"]))
        profile = str(incoming.get("profile", defaults["profile"])).strip()
        if profile not in BILL_PROFILES:
            profile = str(DEFAULT_BILL_ACCEPTOR_SETTINGS["profile"])
        port = str(incoming.get("port", defaults["port"])).strip()
        if _is_auto_serial_port(port):
            port = "AUTO"
        denoms = incoming.get("denoms")
        denoms_map = dict(denoms_default)
        if isinstance(denoms, dict):
            for key in denoms_map.keys():
                denoms_map[key] = bool(denoms.get(key, denoms_map[key]))

        self._loading_bill_controls = True
        self.bill_enabled_cb.setChecked(enabled)
        profile_index = -1
        for idx in range(self.bill_profile_combo.count()):
            if str(self.bill_profile_combo.itemData(idx)) == profile:
                profile_index = idx
                break
        if profile_index < 0:
            profile_index = 0
        self.bill_profile_combo.setCurrentIndex(profile_index)
        self._refresh_bill_ports(selected_port=port)
        for denom, cb in self.bill_denom_cbs.items():
            cb.setChecked(bool(denoms_map.get(denom, False)))
        self._loading_bill_controls = False

    def _collect_bill_acceptor_settings(self) -> dict:
        profile = self._current_bill_profile_key()
        profile_data = BILL_PROFILES.get(profile, {})
        baud = int(profile_data.get("baud", DEFAULT_BILL_ACCEPTOR_SETTINGS["baud"]))
        denoms = {
            denom: cb.isChecked() for denom, cb in self.bill_denom_cbs.items()
        }
        bill_to_amount: dict[int, int] = {}
        try:
            current = self.main_window.get_bill_acceptor_settings()
            raw_map = current.get("bill_to_amount") if isinstance(current, dict) else None
            if isinstance(raw_map, dict):
                for raw_key, raw_amount in raw_map.items():
                    try:
                        code = int(raw_key) & 0xFF
                        amount = int(raw_amount)
                    except Exception:
                        continue
                    if amount > 0:
                        bill_to_amount[code] = amount
        except Exception:
            pass
        return {
            "enabled": self.bill_enabled_cb.isChecked(),
            "profile": profile,
            "port": (
                "AUTO"
                if _is_auto_serial_port(self.bill_port_combo.currentText().strip())
                else self.bill_port_combo.currentText().strip() or str(DEFAULT_BILL_ACCEPTOR_SETTINGS["port"])
            ),
            "baud": baud,
            "denoms": denoms,
            "bill_to_amount": bill_to_amount,
        }

    def _on_save_clicked(self) -> None:
        forced_cash = self.main_window.save_admin_settings(
            self._collect_settings(),
            payment_methods=self._collect_payment_methods(),
            modes=self._collect_modes_settings(),
            ai_styles=self._collect_ai_style_settings(),
            bill_acceptor=self._collect_bill_acceptor_settings(),
            pricing=self._collect_pricing_settings(),
            printing=self._collect_printing_settings(),
        )
        self.load_settings(
            self.main_window.admin_settings,
            self.main_window.get_payment_methods(),
            self.main_window.get_modes_settings(),
            self.main_window.get_ai_style_settings(),
            self.main_window.get_bill_acceptor_settings(),
            self.main_window.get_payment_pricing_settings(),
            self.main_window.get_pricing_layout_ids(),
            self.main_window.get_printing_settings(),
            self.main_window.list_windows_printers(),
        )
        self._refresh_bill_test_buttons()
        if forced_cash:
            self._show_status("Cash는 최소 1개 필요해 자동 활성화되었습니다", duration_ms=1000)
        else:
            self._show_status("저장되었습니다")

    def _on_cancel_clicked(self) -> None:
        self.main_window.close_admin()

    def _on_reset_clicked(self) -> None:
        print("[ADMIN] reset_state")
        self.main_window.reset_state()
        self._show_status("상태가 초기화되었습니다")

    def _on_exit_app_clicked(self) -> None:
        message = (
            "키오스크 프로그램을 종료할까요?\n"
            "Are you sure you want to exit the kiosk app?"
        )
        if hasattr(QMessageBox, "StandardButton"):
            yes_btn = QMessageBox.StandardButton.Yes
            no_btn = QMessageBox.StandardButton.No
        else:
            yes_btn = QMessageBox.Yes
            no_btn = QMessageBox.No
        reply = QMessageBox.question(
            self,
            "프로그램 종료 / Exit",
            message,
            yes_btn | no_btn,
            no_btn,
        )
        if reply != yes_btn:
            return
        print("[ADMIN] exit app requested")
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _refresh_bill_test_buttons(self) -> None:
        running = bool(getattr(self.main_window, "is_bill_acceptor_running", lambda: False)())
        self.bill_test_start_btn.setEnabled(not running)
        self.bill_test_stop_btn.setEnabled(running)

    def _on_bill_test_start(self) -> None:
        settings = self._collect_bill_acceptor_settings()
        started = bool(
            getattr(self.main_window, "start_bill_acceptor_test", lambda *_args, **_kwargs: False)(
                settings
            )
        )
        self._refresh_bill_test_buttons()
        if started:
            self._show_status("Bill 테스트 시작")
        else:
            self._show_status("Bill 테스트 시작 실패", duration_ms=1200)

    def _on_bill_test_stop(self) -> None:
        getattr(self.main_window, "stop_bill_acceptor_test", lambda *_args, **_kwargs: None)()
        self._refresh_bill_test_buttons()
        self._show_status("Bill 테스트 정지", duration_ms=1000)

    def _on_refresh_printers_clicked(self) -> None:
        names = []
        if hasattr(self.main_window, "list_windows_printers"):
            names = list(self.main_window.list_windows_printers())
        ds620 = self.print_printer_ds620_combo.currentText().strip()
        rx1hs = self.print_printer_rx1hs_combo.currentText().strip()
        ds620_form_4x6 = self.print_form_ds620_4x6_combo.currentText().strip()
        ds620_form_2x6 = self.print_form_ds620_2x6_combo.currentText().strip()
        rx1hs_form_4x6 = self.print_form_rx1hs_4x6_combo.currentText().strip()
        rx1hs_form_2x6 = self.print_form_rx1hs_2x6_combo.currentText().strip()
        self._set_combo_items(self.print_printer_ds620_combo, names, ds620)
        self._set_combo_items(self.print_printer_rx1hs_combo, names, rx1hs)
        self._refresh_print_form_controls(
            ds620_form_4x6=ds620_form_4x6,
            ds620_form_2x6=ds620_form_2x6,
            rx1hs_form_4x6=rx1hs_form_4x6,
            rx1hs_form_2x6=rx1hs_form_2x6,
        )
        self._show_status("프린터 목록 갱신", duration_ms=900)

    def _on_refresh_log_path_clicked(self) -> None:
        self._refresh_log_path()
        self._show_status("로그 경로 갱신", duration_ms=900)

    def _on_open_log_folder_clicked(self) -> None:
        ok = False
        if hasattr(self.main_window, "open_runtime_log_folder"):
            try:
                ok = bool(self.main_window.open_runtime_log_folder())
            except Exception:
                ok = False
        self._refresh_log_path()
        if ok:
            self._show_status("로그 폴더 열기 완료", duration_ms=1200)
        else:
            self._show_status("로그 폴더 열기 실패", duration_ms=1600)

    def _on_test_print_clicked(self, model: str) -> None:
        ok = False
        resolved = ""
        if hasattr(self.main_window, "resolve_admin_printer_name"):
            try:
                resolved = str(
                    self.main_window.resolve_admin_printer_name(model, self._collect_printing_settings())
                ).strip()
            except Exception:
                resolved = ""
        if hasattr(self.main_window, "run_admin_print_test"):
            ok = bool(self.main_window.run_admin_print_test(model, self._collect_printing_settings()))
        self._refresh_resolved_printer_labels()
        status = "Test Print OK" if ok else "Test Print FAIL"
        if resolved:
            status = f"{status} ({resolved})"
        self._show_status(status, duration_ms=1200)

    def _on_check_printer_health_clicked(self, model: str) -> None:
        ok = False
        msg = "점검 실패"
        resolved = ""
        if hasattr(self.main_window, "resolve_admin_printer_name"):
            try:
                resolved = str(
                    self.main_window.resolve_admin_printer_name(model, self._collect_printing_settings())
                ).strip()
            except Exception:
                resolved = ""
        if hasattr(self.main_window, "run_admin_printer_health_check"):
            ok, msg = self.main_window.run_admin_printer_health_check(
                model,
                self._collect_printing_settings(),
            )
        self._refresh_resolved_printer_labels()
        prefix = f"{model} ({resolved})" if resolved else model
        if ok:
            self._show_status(f"{prefix} OK: {msg}", duration_ms=1600)
        else:
            self._show_status(f"{prefix} FAIL: {msg}", duration_ms=2200)

    def _on_jump_clicked(self) -> None:
        target = self.jump_screen_combo.currentText().strip()
        if not target:
            return
        print(f"[ADMIN] jump requested screen={target}")
        self.main_window.admin_jump_to_screen(target)
        self._show_status(f"이동: {target}")

    def _show_status(self, text: str, duration_ms: int = 1500) -> None:
        self.status_label.setText(text)
        self._status_timer.start(max(200, int(duration_ms)))

    def _clear_status(self) -> None:
        self.status_label.setText("")

EDS_ERR_OK = 0x00000000
EDS_ERR_INTERNAL_ERROR = 0x00000002
EDS_ERR_DEVICE_BUSY = 0x00000081
EDS_ERR_OBJECT_NOTREADY = 0x0000A102
EDS_ERR_TAKE_PICTURE_AF_NG = 0x00008D01

K_EDS_PROP_ID_SAVE_TO = 0x0000000B
K_EDS_SAVE_TO_HOST = 2
K_EDS_SAVE_TO_BOTH = 3
K_EDS_PROP_ID_EVF_OUTPUT_DEVICE = 0x00000500
K_EDS_EVF_OUTPUT_DEVICE_PC = 0x00000002
K_EDS_OBJECT_EVENT_ALL = 0x00000200
K_EDS_OBJECT_EVENT_DIR_ITEM_REQUEST_TRANSFER = 0x00000208
K_EDS_CAMERA_COMMAND_TAKE_PICTURE = 0x00000000
K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON = 0x00000004
K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_OFF = 0x00000000
K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_HALFWAY = 0x00000001
K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_COMPLETELY = 0x00000003
K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_COMPLETELY_NONAF = 0x00010003
K_EDS_FILE_CREATE_DISPOSITION_CREATE_ALWAYS = 1
K_EDS_ACCESS_READ_WRITE = 2
PM_REMOVE = 0x0001

# Compatibility aliases requested by task spec.
kEdsCameraCommand_TakePicture = K_EDS_CAMERA_COMMAND_TAKE_PICTURE
kEdsCameraCommand_PressShutterButton = K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON
kEdsCameraCommand_ShutterButton_OFF = K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_OFF
kEdsCameraCommand_ShutterButton_Halfway = K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_HALFWAY
kEdsCameraCommand_ShutterButton_Completely = K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_COMPLETELY
kEdsCameraCommand_ShutterButton_Completely_NonAF = (
    K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_COMPLETELY_NONAF
)

_EDS_DLL_HANDLE = None
_EDS_DLL_PATH: Optional[Path] = None
_EDS_DLL_DIR_HANDLE = None
_EDS_SDK_INITIALIZED = False
_EDS_SDK_LOCK = threading.Lock()


def _hex_err(code: int) -> str:
    return f"0x{code:08X}"


def _describe_eds_error(code: int) -> str:
    if code == EDS_ERR_OK:
        return "EDS_ERR_OK"
    if code == EDS_ERR_INTERNAL_ERROR:
        return "EDS_ERR_INTERNAL_ERROR"
    if code == EDS_ERR_OBJECT_NOTREADY:
        return "EDS_ERR_OBJECT_NOTREADY"
    if code == EDS_ERR_DEVICE_BUSY:
        return "EDS_ERR_DEVICE_BUSY"
    if code == EDS_ERR_TAKE_PICTURE_AF_NG:
        return "EDS_ERR_TAKE_PICTURE_AF_NG"
    return "UNKNOWN_ERROR"


def _bind_edsdk_init_api(sdk) -> None:
    sdk.EdsInitializeSDK.restype = ctypes.c_uint32
    sdk.EdsInitializeSDK.argtypes = []
    sdk.EdsTerminateSDK.restype = ctypes.c_uint32
    sdk.EdsTerminateSDK.argtypes = []


def ensure_edsdk_initialized(dll_path: str | Path):
    global _EDS_DLL_HANDLE
    global _EDS_DLL_PATH
    global _EDS_DLL_DIR_HANDLE
    global _EDS_SDK_INITIALIZED

    resolved_path = Path(dll_path)
    if not resolved_path.is_file():
        raise FileNotFoundError(f"EDSDK DLL not found: {resolved_path}")

    with _EDS_SDK_LOCK:
        if _EDS_DLL_HANDLE is None:
            if hasattr(os, "add_dll_directory"):
                _EDS_DLL_DIR_HANDLE = os.add_dll_directory(str(resolved_path.parent))
            try:
                _EDS_DLL_HANDLE = ctypes.WinDLL(str(resolved_path))
            except OSError as exc:
                if getattr(exc, "winerror", None) == 193:
                    raise RuntimeError(
                        "EDSDK DLL bitness mismatch (WinError 193). "
                        "Use matching Python and EDSDK bitness."
                    ) from exc
                raise
            _EDS_DLL_PATH = resolved_path
        elif _EDS_DLL_PATH is not None and resolved_path != _EDS_DLL_PATH:
            print(
                f"[CAMERA] EDSDK path override ignored: requested={resolved_path} "
                f"active={_EDS_DLL_PATH}"
            )

        _bind_edsdk_init_api(_EDS_DLL_HANDLE)
        if not _EDS_SDK_INITIALIZED:
            err = _EDS_DLL_HANDLE.EdsInitializeSDK()
            print(f"[CAMERA] EdsInitializeSDK result: {err:#010x}")
            if err != EDS_ERR_OK:
                raise RuntimeError(
                    f"EdsInitializeSDK failed: {_hex_err(err)} {_describe_eds_error(err)}"
                )
            _EDS_SDK_INITIALIZED = True

        return _EDS_DLL_HANDLE


def terminate_edsdk_once() -> None:
    global _EDS_DLL_HANDLE
    global _EDS_DLL_PATH
    global _EDS_DLL_DIR_HANDLE
    global _EDS_SDK_INITIALIZED

    with _EDS_SDK_LOCK:
        if _EDS_DLL_HANDLE is None:
            return

        _bind_edsdk_init_api(_EDS_DLL_HANDLE)
        if _EDS_SDK_INITIALIZED:
            err = _EDS_DLL_HANDLE.EdsTerminateSDK()
            print(f"[CAMERA] EdsTerminateSDK result: {err:#010x}")
            _EDS_SDK_INITIALIZED = False

        _EDS_DLL_HANDLE = None
        _EDS_DLL_PATH = None
        if _EDS_DLL_DIR_HANDLE is not None:
            try:
                _EDS_DLL_DIR_HANDLE.close()
            except Exception:
                pass
            _EDS_DLL_DIR_HANDLE = None


class LiveViewWorker(QObject):
    frame = Signal(bytes)
    fps = Signal(float)
    capture_success = Signal(str)
    capture_failure = Signal(str)
    error = Signal(str)
    stopped = Signal()

    def __init__(self, dll_path: str, retries: int = 200, capture_timeout_ms: int = 5000) -> None:
        super().__init__()
        self.dll_path = dll_path
        self.retries = max(1, int(retries))
        self.capture_timeout_ms = max(3000, int(capture_timeout_ms))
        self._running = True
        self._capture_requests = queue.Queue()
        self._capture_pending_path: Optional[Path] = None
        self._capture_deadline = 0.0
        self._capture_takepicture_fallback_sent = False
        self._capture_takepicture_fallback_deadline = 0.0
        self._diritem_queue = queue.Queue()
        self._obj_cb: Optional[OBJECT_EVENT_HANDLER] = None
        self._user32 = None

    def stop(self) -> None:
        self._running = False

    def request_capture(self, out_path: Path | str) -> None:
        try:
            target = Path(out_path)
        except Exception as exc:
            self.capture_failure.emit(f"capture target invalid: {exc}")
            return
        self._capture_requests.put(target)
        print(f"[CAMERA] capture queued: {target}")

    def _bind_liveview_api(self, sdk) -> None:
        c_void_pp = ctypes.POINTER(ctypes.c_void_p)
        c_uint32_p = ctypes.POINTER(ctypes.c_uint32)

        sdk.EdsGetCameraList.restype = ctypes.c_uint32
        sdk.EdsGetCameraList.argtypes = [c_void_pp]
        sdk.EdsGetChildCount.restype = ctypes.c_uint32
        sdk.EdsGetChildCount.argtypes = [ctypes.c_void_p, c_uint32_p]
        sdk.EdsGetChildAtIndex.restype = ctypes.c_uint32
        sdk.EdsGetChildAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_int32, c_void_pp]
        sdk.EdsOpenSession.restype = ctypes.c_uint32
        sdk.EdsOpenSession.argtypes = [ctypes.c_void_p]
        sdk.EdsCloseSession.restype = ctypes.c_uint32
        sdk.EdsCloseSession.argtypes = [ctypes.c_void_p]
        sdk.EdsGetPropertyData.restype = ctypes.c_uint32
        sdk.EdsGetPropertyData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        sdk.EdsSetPropertyData.restype = ctypes.c_uint32
        sdk.EdsSetPropertyData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        sdk.EdsCreateMemoryStream.restype = ctypes.c_uint32
        sdk.EdsCreateMemoryStream.argtypes = [ctypes.c_uint32, c_void_pp]
        sdk.EdsCreateEvfImageRef.restype = ctypes.c_uint32
        sdk.EdsCreateEvfImageRef.argtypes = [ctypes.c_void_p, c_void_pp]
        sdk.EdsDownloadEvfImage.restype = ctypes.c_uint32
        sdk.EdsDownloadEvfImage.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        sdk.EdsGetLength.restype = ctypes.c_uint32
        sdk.EdsGetLength.argtypes = [ctypes.c_void_p, c_uint32_p]
        sdk.EdsGetPointer.restype = ctypes.c_uint32
        sdk.EdsGetPointer.argtypes = [ctypes.c_void_p, c_void_pp]
        sdk.EdsSetCapacity.restype = ctypes.c_uint32
        sdk.EdsSetCapacity.argtypes = [ctypes.c_void_p, EdsCapacity]
        sdk.EdsSetObjectEventHandler.restype = ctypes.c_uint32
        sdk.EdsSetObjectEventHandler.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            OBJECT_EVENT_HANDLER,
            ctypes.c_void_p,
        ]
        sdk.EdsSendCommand.restype = ctypes.c_uint32
        sdk.EdsSendCommand.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32]
        sdk.EdsGetEvent.restype = ctypes.c_uint32
        sdk.EdsGetEvent.argtypes = []
        sdk.EdsRetain.restype = ctypes.c_uint32
        sdk.EdsRetain.argtypes = [ctypes.c_void_p]
        sdk.EdsGetDirectoryItemInfo.restype = ctypes.c_uint32
        sdk.EdsGetDirectoryItemInfo.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(EdsDirectoryItemInfo),
        ]
        sdk.EdsCreateFileStreamEx.restype = ctypes.c_uint32
        sdk.EdsCreateFileStreamEx.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            c_void_pp,
        ]
        sdk.EdsDownload.restype = ctypes.c_uint32
        sdk.EdsDownload.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
        sdk.EdsDownloadComplete.restype = ctypes.c_uint32
        sdk.EdsDownloadComplete.argtypes = [ctypes.c_void_p]
        sdk.EdsDownloadCancel.restype = ctypes.c_uint32
        sdk.EdsDownloadCancel.argtypes = [ctypes.c_void_p]
        sdk.EdsRelease.restype = ctypes.c_uint32
        sdk.EdsRelease.argtypes = [ctypes.c_void_p]

    def _ensure_user32(self):
        if self._user32 is not None:
            return self._user32
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.PeekMessageW.restype = wintypes.BOOL
        user32.PeekMessageW.argtypes = [
            ctypes.POINTER(WinMSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.TranslateMessage.restype = wintypes.BOOL
        user32.TranslateMessage.argtypes = [ctypes.POINTER(WinMSG)]
        user32.DispatchMessageW.restype = wintypes.LPARAM
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(WinMSG)]
        self._user32 = user32
        return self._user32

    def _pump_win_messages(self, max_messages: int = 50) -> None:
        user32 = self._ensure_user32()
        msg = WinMSG()
        processed = 0
        while processed < max_messages:
            has_message = user32.PeekMessageW(
                ctypes.byref(msg), None, 0, 0, PM_REMOVE
            )
            if not has_message:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
            processed += 1

    def _ensure_ok(self, err: int, stage: str) -> None:
        if err == EDS_ERR_OK:
            return
        detail = f"{stage} failed: {_hex_err(err)} {_describe_eds_error(err)}"
        if err == EDS_ERR_DEVICE_BUSY:
            detail += " (close EOS Utility and other camera apps)"
        raise RuntimeError(detail)

    @staticmethod
    def _release_ref(sdk, ref: ctypes.c_void_p) -> None:
        if ref and ref.value:
            sdk.EdsRelease(ref)

    def _set_liveview_output_to_pc(self, sdk, camera: ctypes.c_void_p) -> None:
        current_output = ctypes.c_uint32(0)
        err_get = sdk.EdsGetPropertyData(
            camera,
            K_EDS_PROP_ID_EVF_OUTPUT_DEVICE,
            0,
            ctypes.sizeof(current_output),
            ctypes.byref(current_output),
        )
        if err_get == EDS_ERR_OK:
            target_output = ctypes.c_uint32(current_output.value | K_EDS_EVF_OUTPUT_DEVICE_PC)
        else:
            target_output = ctypes.c_uint32(K_EDS_EVF_OUTPUT_DEVICE_PC)
        self._ensure_ok(
            sdk.EdsSetPropertyData(
                camera,
                K_EDS_PROP_ID_EVF_OUTPUT_DEVICE,
                0,
                ctypes.sizeof(target_output),
                ctypes.byref(target_output),
            ),
            "EdsSetPropertyData(Evf_OutputDevice=PC)",
        )

    def _configure_save_to_host(self, sdk, camera: ctypes.c_void_p) -> None:
        save_to = ctypes.c_uint32(K_EDS_SAVE_TO_HOST)
        err_host = sdk.EdsSetPropertyData(
            camera,
            K_EDS_PROP_ID_SAVE_TO,
            0,
            ctypes.sizeof(save_to),
            ctypes.byref(save_to),
        )
        print(f"[CAMERA] SaveTo Host: 0x{int(err_host):08X}")
        if err_host != EDS_ERR_OK:
            save_to = ctypes.c_uint32(K_EDS_SAVE_TO_BOTH)
            self._ensure_ok(
                sdk.EdsSetPropertyData(
                    camera,
                    K_EDS_PROP_ID_SAVE_TO,
                    0,
                    ctypes.sizeof(save_to),
                    ctypes.byref(save_to),
                ),
                "EdsSetPropertyData(SaveTo=Both)",
            )
            print("[CAMERA] SaveTo fallback: Both")

        save_to_current = ctypes.c_uint32(0)
        err_current = sdk.EdsGetPropertyData(
            camera,
            K_EDS_PROP_ID_SAVE_TO,
            0,
            ctypes.sizeof(save_to_current),
            ctypes.byref(save_to_current),
        )
        if err_current == EDS_ERR_OK:
            print(
                f"[CAMERA] SaveTo current={save_to_current.value} "
                "(2=Host,3=Both)"
            )
        else:
            print(f"[CAMERA] SaveTo current read failed: {_hex_err(int(err_current))}")

        cap = EdsCapacity(
            numberOfFreeClusters=0x7FFFFFFF,
            bytesPerSector=4096,
            reset=1,
        )
        err_capacity = sdk.EdsSetCapacity(camera, cap)
        print(f"[CAMERA] SetCapacity result: {_hex_err(int(err_capacity))}")
        self._ensure_ok(err_capacity, "EdsSetCapacity")

    def _handle_object_event(self, sdk, event: int, in_ref) -> int:
        if not self._running:
            return EDS_ERR_OK
        try:
            ref_value = int(in_ref) if in_ref else 0
        except Exception:
            ref_value = 0

        print(f"[CAMERA] object event: 0x{int(event):08X} inRef={ref_value}")
        if ref_value == 0:
            return EDS_ERR_OK

        dir_item = ctypes.c_void_p(ref_value)
        info = EdsDirectoryItemInfo()
        err_info = sdk.EdsGetDirectoryItemInfo(dir_item, ctypes.byref(info))
        if err_info != EDS_ERR_OK:
            return EDS_ERR_OK

        err_retain = sdk.EdsRetain(dir_item)
        retained = err_retain == EDS_ERR_OK
        if not retained:
            print(f"[CAMERA] retain dir item failed: {_hex_err(int(err_retain))}")
            # Do not keep unretained refs for later; they can become invalid and crash on shutdown.
            target_path = self._capture_pending_path
            if target_path is not None:
                try:
                    self._download_dir_item(sdk, dir_item, target_path)
                except Exception as exc:
                    self._capture_pending_path = None
                    self._capture_deadline = 0.0
                    self.capture_failure.emit(str(exc))
                else:
                    self._capture_pending_path = None
                    self._capture_deadline = 0.0
                    self.capture_success.emit(str(target_path))
            return EDS_ERR_OK
        self._diritem_queue.put((dir_item, True))
        return EDS_ERR_OK

    def _drain_capture_requests(self) -> None:
        while True:
            try:
                self._capture_requests.get_nowait()
            except queue.Empty:
                break

    def _drain_dir_items(self, sdk) -> None:
        while True:
            try:
                dir_item, retained = self._diritem_queue.get_nowait()
            except queue.Empty:
                break
            if not retained:
                continue
            try:
                err_cancel = sdk.EdsDownloadCancel(dir_item)
                print(
                    f"[CAMERA] stale transfer request -> DownloadCancel "
                    f"{_hex_err(int(err_cancel))}"
                )
            except Exception:
                pass
            finally:
                if retained:
                    self._release_ref(sdk, dir_item)

    def _download_dir_item(self, sdk, dir_item: ctypes.c_void_p, out_path: Path) -> None:
        info = EdsDirectoryItemInfo()
        self._ensure_ok(
            sdk.EdsGetDirectoryItemInfo(dir_item, ctypes.byref(info)),
            "EdsGetDirectoryItemInfo",
        )
        size = int(info.size)
        if size <= 0:
            raise RuntimeError("captured file size is 0")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            out_path.unlink(missing_ok=True)
        except OSError:
            pass

        stream = ctypes.c_void_p()
        try:
            self._ensure_ok(
                sdk.EdsCreateFileStreamEx(
                    str(out_path),
                    K_EDS_FILE_CREATE_DISPOSITION_CREATE_ALWAYS,
                    K_EDS_ACCESS_READ_WRITE,
                    ctypes.byref(stream),
                ),
                "EdsCreateFileStreamEx",
            )
            download_size = min(size, 0xFFFFFFFF)
            err_download = sdk.EdsDownload(dir_item, ctypes.c_uint32(download_size), stream)
            print(f"[CAMERA] Download result: {_hex_err(int(err_download))}")
            self._ensure_ok(err_download, "EdsDownload")
            err_complete = sdk.EdsDownloadComplete(dir_item)
            print(f"[CAMERA] DownloadComplete result: {_hex_err(int(err_complete))}")
            self._ensure_ok(err_complete, "EdsDownloadComplete")
        finally:
            self._release_ref(sdk, stream)

    def _process_diritem_queue(self, sdk) -> None:
        while True:
            try:
                dir_item, retained = self._diritem_queue.get_nowait()
            except queue.Empty:
                return

            try:
                target_path = self._capture_pending_path
                if target_path is None:
                    if retained:
                        err_cancel = sdk.EdsDownloadCancel(dir_item)
                        print(
                            "[CAMERA] stale transfer request -> DownloadCancel "
                            f"{_hex_err(int(err_cancel))}"
                        )
                    continue

                try:
                    self._download_dir_item(sdk, dir_item, target_path)
                except Exception as exc:
                    try:
                        if retained:
                            err_cancel = sdk.EdsDownloadCancel(dir_item)
                            print(
                                "[CAMERA] Download failed -> DownloadCancel "
                                f"{_hex_err(int(err_cancel))}"
                            )
                    except Exception:
                        pass
                    self._capture_pending_path = None
                    self._capture_deadline = 0.0
                    self._capture_takepicture_fallback_sent = False
                    self._capture_takepicture_fallback_deadline = 0.0
                    self.capture_failure.emit(str(exc))
                else:
                    self._capture_pending_path = None
                    self._capture_deadline = 0.0
                    self._capture_takepicture_fallback_sent = False
                    self._capture_takepicture_fallback_deadline = 0.0
                    self.capture_success.emit(str(target_path))
            finally:
                if retained:
                    self._release_ref(sdk, dir_item)

    def _trigger_capture_command(self, sdk, camera: ctypes.c_void_p) -> int:
        # Primary path: PressShutter sequence (works better on some bodies in liveview).
        result = EDS_ERR_OK
        try:
            halfway = sdk.EdsSendCommand(
                camera,
                K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON,
                K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_HALFWAY,
            )
            print(f"[CAMERA] PressShutter Halfway result: {_hex_err(int(halfway))}")
            time.sleep(0.25)

            result = int(
                sdk.EdsSendCommand(
                    camera,
                    K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON,
                    K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_COMPLETELY,
                )
            )
            print(f"[CAMERA] PressShutter Completely result: {_hex_err(int(result))}")
            if result == EDS_ERR_TAKE_PICTURE_AF_NG:
                result = int(
                    sdk.EdsSendCommand(
                        camera,
                        K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON,
                        K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_COMPLETELY_NONAF,
                    )
                )
                print(
                    "[CAMERA] PressShutter Completely_NonAF result: "
                    f"{_hex_err(int(result))}"
                )
            if int(result) == EDS_ERR_OK:
                return int(result)
        finally:
            off = sdk.EdsSendCommand(
                camera,
                K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON,
                K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_OFF,
            )
            print(f"[CAMERA] PressShutter OFF result: {_hex_err(int(off))}")

        # Fallback path: TakePicture.
        take_picture_result = sdk.EdsSendCommand(
            camera,
            K_EDS_CAMERA_COMMAND_TAKE_PICTURE,
            0,
        )
        print(
            "[CAMERA] PressShutter fallback -> TakePicture "
            f"result={_hex_err(int(take_picture_result))}"
        )
        return int(take_picture_result)

    def _start_next_capture_if_any(self, sdk, camera: ctypes.c_void_p) -> None:
        if self._capture_pending_path is not None:
            return
        try:
            out_path = self._capture_requests.get_nowait()
        except queue.Empty:
            return

        try:
            # Re-apply host transfer configuration before each shot.
            self._configure_save_to_host(sdk, camera)
        except Exception as exc:
            self.capture_failure.emit(f"capture setup failed: {exc}")
            return

        trigger_result = self._trigger_capture_command(sdk, camera)
        print(f"[CAMERA] capture trigger result: {_hex_err(int(trigger_result))}")
        if trigger_result not in (EDS_ERR_OK, EDS_ERR_TAKE_PICTURE_AF_NG):
            self.capture_failure.emit(
                "CaptureTrigger failed: "
                f"{_hex_err(int(trigger_result))} {_describe_eds_error(int(trigger_result))}"
            )
            return

        if trigger_result == EDS_ERR_TAKE_PICTURE_AF_NG:
            print("[CAMERA] AF_NG trigger -> waiting dir item transfer event")
        self._capture_pending_path = Path(out_path)
        now = time.perf_counter()
        self._capture_deadline = now + (self.capture_timeout_ms / 1000.0)
        # Some bodies occasionally don't emit transfer after PressShutter despite OK result.
        # If no dir-item comes quickly, send one TakePicture fallback once.
        self._capture_takepicture_fallback_sent = False
        self._capture_takepicture_fallback_deadline = now + 2.2

    def _check_capture_timeout(self, sdk, camera: ctypes.c_void_p) -> None:
        if self._capture_pending_path is None:
            return
        now = time.perf_counter()
        if (
            not self._capture_takepicture_fallback_sent
            and now >= self._capture_takepicture_fallback_deadline
        ):
            self._capture_takepicture_fallback_sent = True
            fallback_result = int(
                sdk.EdsSendCommand(
                    camera,
                    K_EDS_CAMERA_COMMAND_TAKE_PICTURE,
                    0,
                )
            )
            print(
                "[CAMERA] capture transfer fallback -> TakePicture "
                f"result: {_hex_err(fallback_result)}"
            )
            if fallback_result in (EDS_ERR_OK, EDS_ERR_TAKE_PICTURE_AF_NG):
                self._capture_deadline = now + max(2.5, self.capture_timeout_ms / 2000.0)
            return
        if now < self._capture_deadline:
            return
        pending = self._capture_pending_path
        self._capture_pending_path = None
        self._capture_deadline = 0.0
        self._capture_takepicture_fallback_sent = False
        self._capture_takepicture_fallback_deadline = 0.0
        self.capture_failure.emit(
            f"capture timeout waiting for dir item -> retry ({pending})"
        )

    def _open_session_with_retry(self, sdk, camera: ctypes.c_void_p) -> None:
        last_err = EDS_ERR_OK
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            err = sdk.EdsOpenSession(camera)
            last_err = err
            if err == EDS_ERR_OK:
                return
            print(
                f"[CAMERA] EdsOpenSession attempt {attempt}/{max_attempts} "
                f"failed: {_hex_err(err)} {_describe_eds_error(err)}"
            )
            if attempt < max_attempts:
                time.sleep(0.25)
        self._ensure_ok(last_err, "EdsOpenSession")

    def _get_frame_jpeg_bytes(
        self,
        sdk,
        camera: ctypes.c_void_p,
        evf: ctypes.c_void_p,
        stream: ctypes.c_void_p,
    ) -> bytes:
        last_err = EDS_ERR_OK
        for _ in range(self.retries):
            err = sdk.EdsDownloadEvfImage(camera, evf)
            last_err = err
            if err == EDS_ERR_OK:
                break
            if err == EDS_ERR_OBJECT_NOTREADY:
                time.sleep(0.015)
                continue
            raise RuntimeError(
                "EdsDownloadEvfImage failed: "
                f"{_hex_err(err)} {_describe_eds_error(err)}"
            )
        else:
            raise RuntimeError(
                "EdsDownloadEvfImage retries exhausted: "
                f"{_hex_err(last_err)} {_describe_eds_error(last_err)}"
            )

        length = ctypes.c_uint32(0)
        self._ensure_ok(sdk.EdsGetLength(stream, ctypes.byref(length)), "EdsGetLength")
        if length.value <= 0:
            raise RuntimeError("EVF data length is 0.")

        ptr = ctypes.c_void_p()
        self._ensure_ok(sdk.EdsGetPointer(stream, ctypes.byref(ptr)), "EdsGetPointer")
        if not ptr.value:
            raise RuntimeError("EVF pointer is null.")
        return ctypes.string_at(ptr.value, length.value)

    def run(self) -> None:
        sdk = None
        camera_list = ctypes.c_void_p()
        camera = ctypes.c_void_p()
        stream = ctypes.c_void_p()
        evf = ctypes.c_void_p()
        session_opened = False
        frames = 0
        last_ts = time.perf_counter()
        try:
            sdk = ensure_edsdk_initialized(self.dll_path)
            self._bind_liveview_api(sdk)

            self._ensure_ok(sdk.EdsGetCameraList(ctypes.byref(camera_list)), "EdsGetCameraList")
            count = ctypes.c_uint32(0)
            self._ensure_ok(sdk.EdsGetChildCount(camera_list, ctypes.byref(count)), "EdsGetChildCount")
            if count.value < 1:
                raise RuntimeError("No camera detected.")
            self._ensure_ok(
                sdk.EdsGetChildAtIndex(camera_list, 0, ctypes.byref(camera)),
                "EdsGetChildAtIndex(0)",
            )
            self._open_session_with_retry(sdk, camera)
            session_opened = True

            self._configure_save_to_host(sdk, camera)
            self._obj_cb = OBJECT_EVENT_HANDLER(
                lambda event, in_ref, in_ctx: self._handle_object_event(sdk, event, in_ref)
            )
            err_obj_handler = sdk.EdsSetObjectEventHandler(
                camera,
                K_EDS_OBJECT_EVENT_ALL,
                self._obj_cb,
                None,
            )
            print(f"[CAMERA] SetObjectEventHandler result: {_hex_err(int(err_obj_handler))}")
            self._ensure_ok(err_obj_handler, "EdsSetObjectEventHandler")

            self._set_liveview_output_to_pc(sdk, camera)
            self._ensure_ok(
                sdk.EdsCreateMemoryStream(8 * 1024 * 1024, ctypes.byref(stream)),
                "EdsCreateMemoryStream",
            )
            self._ensure_ok(sdk.EdsCreateEvfImageRef(stream, ctypes.byref(evf)), "EdsCreateEvfImageRef")

            while self._running:
                sdk.EdsGetEvent()
                self._pump_win_messages()
                self._process_diritem_queue(sdk)
                self._start_next_capture_if_any(sdk, camera)
                self._check_capture_timeout(sdk, camera)

                if self._capture_pending_path is not None:
                    time.sleep(0.01)
                    continue

                data = self._get_frame_jpeg_bytes(sdk, camera, evf, stream)
                if not self._running:
                    break
                self.frame.emit(data)
                frames += 1
                now = time.perf_counter()
                elapsed = now - last_ts
                if elapsed >= 1.0:
                    self.fps.emit(frames / elapsed)
                    frames = 0
                    last_ts = now
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            if sdk is not None:
                self._drain_capture_requests()
                self._drain_dir_items(sdk)
                self._release_ref(sdk, evf)
                self._release_ref(sdk, stream)
                if session_opened and camera and camera.value:
                    sdk.EdsCloseSession(camera)
                self._release_ref(sdk, camera)
                self._release_ref(sdk, camera_list)
            self._obj_cb = None
            self._capture_pending_path = None
            self._capture_deadline = 0.0
            self._capture_takepicture_fallback_sent = False
            self._capture_takepicture_fallback_deadline = 0.0
            self.stopped.emit()


class DummyLiveViewWorker(QObject):
    frame = Signal(bytes)
    fps = Signal(float)
    capture_success = Signal(str)
    capture_failure = Signal(str)
    error = Signal(str)
    stopped = Signal()

    def __init__(self, fps_target: int = 24) -> None:
        super().__init__()
        self.fps_target = max(8, min(30, int(fps_target)))
        self._running = True
        self._capture_requests: "queue.Queue[Path]" = queue.Queue()

    def stop(self) -> None:
        self._running = False

    def request_capture(self, out_path: Path | str) -> None:
        try:
            target = Path(out_path)
        except Exception as exc:
            self.capture_failure.emit(f"dummy capture target invalid: {exc}")
            return
        self._capture_requests.put(target)

    @staticmethod
    def _parse_shot_index(path: Path) -> int:
        match = re.search(r"(\d+)", path.stem)
        if match:
            try:
                return int(match.group(1))
            except Exception:
                return 0
        return 0

    def _create_live_frame(self) -> bytes:
        width, height = 960, 640
        now = time.strftime("%H:%M:%S")
        image = Image.new("RGB", (width, height), (28, 34, 56))
        draw = ImageDraw.Draw(image)
        draw.rectangle((20, 20, width - 20, height - 20), outline=(150, 200, 255), width=3)
        draw.text((36, 42), "DUMMY LIVE", fill=(255, 255, 255))
        draw.text((36, 86), f"time={now}", fill=(220, 240, 255))
        draw.text((36, 130), "backend=dummy", fill=(220, 240, 255))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()

    def _save_dummy_capture(self, target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        shot_index = self._parse_shot_index(target)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        image = Image.new("RGB", (1920, 1080), (245, 245, 245))
        draw = ImageDraw.Draw(image)
        draw.text((140, 180), f"DUMMY SHOT {shot_index:02d}", fill=(25, 25, 25))
        draw.text((140, 280), timestamp, fill=(60, 60, 60))
        draw.text((140, 360), "camera_backend=dummy", fill=(60, 60, 60))
        image.save(target, format="JPEG", quality=95)
        return target

    def run(self) -> None:
        frame_counter = 0
        last_fps_ts = time.perf_counter()
        frame_interval = 1.0 / float(self.fps_target)
        try:
            while self._running:
                loop_start = time.perf_counter()
                while True:
                    try:
                        target = self._capture_requests.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        saved = self._save_dummy_capture(target)
                        print(f"[CAMERA] dummy capture saved={saved}")
                        self.capture_success.emit(str(saved))
                    except Exception as exc:
                        self.capture_failure.emit(f"dummy capture failed: {exc}")

                self.frame.emit(self._create_live_frame())
                frame_counter += 1
                now = time.perf_counter()
                elapsed = now - last_fps_ts
                if elapsed >= 1.0:
                    self.fps.emit(frame_counter / elapsed)
                    frame_counter = 0
                    last_fps_ts = now

                sleep_time = frame_interval - (time.perf_counter() - loop_start)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.stopped.emit()


OBJECT_EVENT_HANDLER = ctypes.WINFUNCTYPE(
    ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p
)


class EdsCapacity(ctypes.Structure):
    _fields_ = [
        ("numberOfFreeClusters", ctypes.c_int32),
        ("bytesPerSector", ctypes.c_int32),
        ("reset", ctypes.c_int32),
    ]


class EdsDirectoryItemInfo(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_uint64),
        ("isFolder", ctypes.c_int32),
        ("groupID", ctypes.c_uint32),
        ("option", ctypes.c_uint32),
        ("szFileName", ctypes.c_char * 256),
        ("format", ctypes.c_uint32),
        ("dateTime", ctypes.c_uint32),
    ]


class WinMSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class CaptureWorker(QObject):
    success = Signal(str)
    failure = Signal(str)
    finished = Signal()

    def __init__(self, dll_path: str, out_path: Path, timeout_ms: int = 5000) -> None:
        super().__init__()
        self.dll_path = Path(dll_path)
        self.out_path = Path(out_path)
        self.timeout_ms = max(1000, int(timeout_ms))
        self._running = True

        self._queue: queue.Queue[tuple[ctypes.c_void_p, bool]] = queue.Queue()
        self._obj_cb: Optional[OBJECT_EVENT_HANDLER] = None
        self._dir_item_event_received = False
        self._user32 = None

    def stop(self) -> None:
        self._running = False

    def _bind_capture_api(self, sdk) -> None:
        c_void_pp = ctypes.POINTER(ctypes.c_void_p)

        sdk.EdsGetCameraList.restype = ctypes.c_uint32
        sdk.EdsGetCameraList.argtypes = [c_void_pp]
        sdk.EdsGetChildCount.restype = ctypes.c_uint32
        sdk.EdsGetChildCount.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        sdk.EdsGetChildAtIndex.restype = ctypes.c_uint32
        sdk.EdsGetChildAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_int32, c_void_pp]
        sdk.EdsOpenSession.restype = ctypes.c_uint32
        sdk.EdsOpenSession.argtypes = [ctypes.c_void_p]
        sdk.EdsCloseSession.restype = ctypes.c_uint32
        sdk.EdsCloseSession.argtypes = [ctypes.c_void_p]
        sdk.EdsSetPropertyData.restype = ctypes.c_uint32
        sdk.EdsSetPropertyData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        sdk.EdsGetPropertyData.restype = ctypes.c_uint32
        sdk.EdsGetPropertyData.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int32,
            ctypes.c_uint32,
            ctypes.c_void_p,
        ]
        sdk.EdsSetCapacity.restype = ctypes.c_uint32
        sdk.EdsSetCapacity.argtypes = [ctypes.c_void_p, EdsCapacity]
        sdk.EdsSetObjectEventHandler.restype = ctypes.c_uint32
        sdk.EdsSetObjectEventHandler.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            OBJECT_EVENT_HANDLER,
            ctypes.c_void_p,
        ]
        sdk.EdsSendCommand.restype = ctypes.c_uint32
        sdk.EdsSendCommand.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32]
        sdk.EdsGetEvent.restype = ctypes.c_uint32
        sdk.EdsGetEvent.argtypes = []
        sdk.EdsRetain.restype = ctypes.c_uint32
        sdk.EdsRetain.argtypes = [ctypes.c_void_p]
        sdk.EdsRelease.restype = ctypes.c_uint32
        sdk.EdsRelease.argtypes = [ctypes.c_void_p]
        sdk.EdsGetDirectoryItemInfo.restype = ctypes.c_uint32
        sdk.EdsGetDirectoryItemInfo.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(EdsDirectoryItemInfo),
        ]
        sdk.EdsCreateFileStreamEx.restype = ctypes.c_uint32
        sdk.EdsCreateFileStreamEx.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            c_void_pp,
        ]
        sdk.EdsDownload.restype = ctypes.c_uint32
        sdk.EdsDownload.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
        sdk.EdsDownloadComplete.restype = ctypes.c_uint32
        sdk.EdsDownloadComplete.argtypes = [ctypes.c_void_p]

    def _ensure_user32(self):
        if self._user32 is not None:
            return self._user32
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.PeekMessageW.restype = wintypes.BOOL
        user32.PeekMessageW.argtypes = [
            ctypes.POINTER(WinMSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.TranslateMessage.restype = wintypes.BOOL
        user32.TranslateMessage.argtypes = [ctypes.POINTER(WinMSG)]
        user32.DispatchMessageW.restype = wintypes.LPARAM
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(WinMSG)]
        self._user32 = user32
        return self._user32

    def _pump_win_messages(self, max_messages: int = 50) -> None:
        user32 = self._ensure_user32()
        msg = WinMSG()
        processed = 0
        while processed < max_messages:
            has_message = user32.PeekMessageW(
                ctypes.byref(msg), None, 0, 0, PM_REMOVE
            )
            if not has_message:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
            processed += 1

    def _ensure_ok(self, err: int, stage: str) -> None:
        if err != EDS_ERR_OK:
            raise RuntimeError(f"{stage} failed: 0x{err:08X}")

    def _release_ref(self, sdk, ref: ctypes.c_void_p) -> None:
        if ref and ref.value:
            sdk.EdsRelease(ref)

    def _handle_object_event(self, sdk, event: int, in_ref) -> int:
        try:
            ref_value = int(in_ref) if in_ref else 0
        except Exception:
            ref_value = 0

        print(f"[CAMERA] object event: 0x{int(event):08X} inRef={ref_value}")
        if ref_value == 0:
            return EDS_ERR_OK

        dir_item = ctypes.c_void_p(ref_value)
        info = EdsDirectoryItemInfo()
        err_info = sdk.EdsGetDirectoryItemInfo(dir_item, ctypes.byref(info))
        if err_info != EDS_ERR_OK:
            return EDS_ERR_OK

        err_retain = sdk.EdsRetain(dir_item)
        retained = err_retain == EDS_ERR_OK
        if not retained:
            print(f"[CAMERA] capture retain fallback: 0x{err_retain:08X}")
        self._queue.put((dir_item, retained))
        self._dir_item_event_received = True
        return EDS_ERR_OK

    def _download(self, sdk, dir_item: ctypes.c_void_p) -> None:
        info = EdsDirectoryItemInfo()
        self._ensure_ok(sdk.EdsGetDirectoryItemInfo(dir_item, ctypes.byref(info)), "EdsGetDirectoryItemInfo")
        size = int(info.size)
        if size <= 0:
            raise RuntimeError("captured file size is 0")

        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        stream = ctypes.c_void_p()
        try:
            self._ensure_ok(
                sdk.EdsCreateFileStreamEx(
                    str(self.out_path),
                    K_EDS_FILE_CREATE_DISPOSITION_CREATE_ALWAYS,
                    K_EDS_ACCESS_READ_WRITE,
                    ctypes.byref(stream),
                ),
                "EdsCreateFileStreamEx",
            )
            download_size = min(size, 0xFFFFFFFF)
            err_download = sdk.EdsDownload(dir_item, ctypes.c_uint32(download_size), stream)
            print(f"[CAMERA] Download result: 0x{err_download:08X}")
            self._ensure_ok(err_download, "EdsDownload")
            err_complete = sdk.EdsDownloadComplete(dir_item)
            print(f"[CAMERA] DownloadComplete result: 0x{err_complete:08X}")
            self._ensure_ok(err_complete, "EdsDownloadComplete")
        finally:
            self._release_ref(sdk, stream)

    def _trigger_capture_command(self, sdk, camera: ctypes.c_void_p) -> int:
        result = EDS_ERR_OK
        try:
            halfway = sdk.EdsSendCommand(
                camera,
                K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON,
                K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_HALFWAY,
            )
            print(f"[CAMERA] PressShutter Halfway result: 0x{int(halfway):08X}")
            time.sleep(0.25)

            result = sdk.EdsSendCommand(
                camera,
                K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON,
                K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_COMPLETELY,
            )
            print(f"[CAMERA] PressShutter Completely result: 0x{int(result):08X}")
            if int(result) == EDS_ERR_TAKE_PICTURE_AF_NG:
                result = sdk.EdsSendCommand(
                    camera,
                    K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON,
                    K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_COMPLETELY_NONAF,
                )
                print(
                    f"[CAMERA] PressShutter Completely_NonAF result: 0x{int(result):08X}"
                )
            return int(result)
        finally:
            off = sdk.EdsSendCommand(
                camera,
                K_EDS_CAMERA_COMMAND_PRESS_SHUTTER_BUTTON,
                K_EDS_CAMERA_COMMAND_SHUTTER_BUTTON_OFF,
            )
            print(f"[CAMERA] PressShutter OFF result: 0x{int(off):08X}")

    def run(self) -> None:
        sdk = None
        camera_list = ctypes.c_void_p()
        camera = ctypes.c_void_p()
        session_opened = False
        self._dir_item_event_received = False
        success_path: Optional[str] = None
        failure_message: Optional[str] = None
        try:
            sdk = ensure_edsdk_initialized(self.dll_path)
            self._bind_capture_api(sdk)

            self._ensure_ok(sdk.EdsGetCameraList(ctypes.byref(camera_list)), "EdsGetCameraList")
            count = ctypes.c_uint32(0)
            self._ensure_ok(sdk.EdsGetChildCount(camera_list, ctypes.byref(count)), "EdsGetChildCount")
            if count.value < 1:
                raise RuntimeError("No camera detected.")

            self._ensure_ok(
                sdk.EdsGetChildAtIndex(camera_list, 0, ctypes.byref(camera)),
                "EdsGetChildAtIndex(0)",
            )
            self._ensure_ok(sdk.EdsOpenSession(camera), "EdsOpenSession")
            session_opened = True

            save_to = ctypes.c_uint32(K_EDS_SAVE_TO_HOST)
            err = sdk.EdsSetPropertyData(
                camera,
                K_EDS_PROP_ID_SAVE_TO,
                0,
                ctypes.sizeof(save_to),
                ctypes.byref(save_to),
            )
            print(f"[CAMERA] SaveTo Host: 0x{err:08X}")
            if err != EDS_ERR_OK:
                save_to = ctypes.c_uint32(K_EDS_SAVE_TO_BOTH)
                self._ensure_ok(
                    sdk.EdsSetPropertyData(
                        camera,
                        K_EDS_PROP_ID_SAVE_TO,
                        0,
                        ctypes.sizeof(save_to),
                        ctypes.byref(save_to),
                    ),
                    "EdsSetPropertyData(SaveTo=Both)",
                )
                print("[CAMERA] SaveTo fallback: Both")

            save_to_current = ctypes.c_uint32(0)
            err_save_to_current = sdk.EdsGetPropertyData(
                camera,
                K_EDS_PROP_ID_SAVE_TO,
                0,
                ctypes.sizeof(save_to_current),
                ctypes.byref(save_to_current),
            )
            if err_save_to_current == EDS_ERR_OK:
                print(
                    f"[CAMERA] SaveTo current={save_to_current.value} "
                    "(2=Host,3=Both)"
                )
            else:
                print(
                    f"[CAMERA] SaveTo current read failed: 0x{int(err_save_to_current):08X}"
                )

            cap = EdsCapacity(
                numberOfFreeClusters=0x7FFFFFFF,
                bytesPerSector=4096,
                reset=1,
            )
            err_capacity = sdk.EdsSetCapacity(camera, cap)
            print(f"[CAMERA] SetCapacity result: 0x{int(err_capacity):08X}")
            self._ensure_ok(err_capacity, "EdsSetCapacity")

            self._obj_cb = OBJECT_EVENT_HANDLER(
                lambda event, in_ref, in_ctx: self._handle_object_event(sdk, event, in_ref)
            )
            err_obj_handler = sdk.EdsSetObjectEventHandler(
                camera,
                K_EDS_OBJECT_EVENT_ALL,
                self._obj_cb,
                None,
            )
            print(f"[CAMERA] SetObjectEventHandler result: 0x{int(err_obj_handler):08X}")
            self._ensure_ok(err_obj_handler, "EdsSetObjectEventHandler")

            try:
                self.out_path.unlink(missing_ok=True)
            except OSError:
                pass

            trigger_result = self._trigger_capture_command(sdk, camera)
            print(f"[CAMERA] capture trigger result: 0x{trigger_result:08X}")
            self._ensure_ok(trigger_result, "CaptureTrigger")

            deadline = time.perf_counter() + (self.timeout_ms / 1000.0)
            while self._running and time.perf_counter() < deadline:
                sdk.EdsGetEvent()
                self._pump_win_messages()
                got_item = False
                try:
                    dir_item, retained = self._queue.get_nowait()
                except queue.Empty:
                    got_item = False
                else:
                    got_item = True

                if got_item:
                    try:
                        self._download(sdk, dir_item)
                    finally:
                        if retained:
                            self._release_ref(sdk, dir_item)

                if (
                    self._dir_item_event_received
                    and self.out_path.is_file()
                    and self.out_path.stat().st_size > 0
                ):
                    success_path = str(self.out_path)
                    break
                time.sleep(0.015)

            if success_path is None and not self._running:
                failure_message = "capture canceled"
            elif success_path is None:
                print("[CAMERA] capture timeout waiting for dir item -> retry")
                failure_message = "capture timeout waiting for dir item -> retry"
        except Exception as exc:
            failure_message = str(exc)
        finally:
            if sdk is not None:
                while True:
                    try:
                        ref, retained = self._queue.get_nowait()
                    except queue.Empty:
                        break
                    if retained:
                        self._release_ref(sdk, ref)

                if session_opened and camera and camera.value:
                    sdk.EdsCloseSession(camera)
                self._release_ref(sdk, camera)
                self._release_ref(sdk, camera_list)

            self._obj_cb = None
        if success_path is not None:
            self.success.emit(success_path)
        else:
            self.failure.emit(failure_message or "capture failed")
        self.finished.emit()


class CameraScreen(ImageScreen):
    LIVEVIEW_RECT_BY_LAYOUT: Dict[str, tuple[int, int, int, int]] = {
        "2641": (480, 140, 960, 800),
        "6241": (700, 190, 500, 700),
        "4641": (540, 140, 840, 780),
        "4661": (300, 140, 620, 760),
        "4681": (430, 140, 1060, 800),
    }

    def __init__(
        self,
        main_window: "KioskMainWindow",
        liveview_dll_path: Optional[str] = None,
        camera_backend: str = "edsdk",
    ) -> None:
        self.camera_dir = ROOT_DIR / "assets" / "ui" / "7_Camera_shooting_liveview"
        super().__init__(main_window, "camera", self._find_overlay_path("2641"))
        print("[CAMERA] screen created")
        self.layout_id: Optional[str] = None
        self.design_index: Optional[int] = None
        self.design_path: Optional[str] = None
        self.liveview_dll_path = (liveview_dll_path or "").strip()
        self.camera_backend = (camera_backend or "auto").strip().lower()
        self._backend_active = "idle"
        self._backend_reason = ""
        self._liveview_frame_received = False
        self._camera_connection_blocked = False
        self.print_slots = 0
        self.capture_slots = 0
        self.slot_rects: list[tuple[int, int, int, int]] = []
        self.shot_paths: list[Path] = []
        self.session: Optional[Session] = None
        self._liveview_pixmap: Optional[QPixmap] = None
        self._liveview_thread: Optional[QThread] = None
        self._liveview_worker: Optional[QObject] = None
        self._liveview_running = False
        self._capture_thread: Optional[QThread] = None
        self._capture_worker: Optional[CaptureWorker] = None
        self._capture_pending_after_liveview_stop = False
        self._capture_target_index: Optional[int] = None
        self._capture_target_path: Optional[Path] = None
        self._pending_dummy_fallback_reason: Optional[str] = None
        self._pending_restart_after_liveview_stop = False
        self._capture_timeout_streak = 0
        self._shutter_locked = False
        self._auto_next_pending = False
        self.auto_mode = True
        self.auto_wait_frame = True
        self.countdown_running = False
        self.capture_inflight = False
        self._last_liveview_jpeg: Optional[bytes] = None
        self._gif_frames_by_shot: dict[int, list[bytes]] = {}
        self._gif_burst_timers: list[QTimer] = []
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._on_countdown_tick)
        self._countdown_value = 0
        self._countdown_active = False
        self._retry_overlay_active = False
        self._retry_overlay_timer = QTimer(self)
        self._retry_overlay_timer.setSingleShot(True)
        self._retry_overlay_timer.timeout.connect(self._hide_retry_overlay)
        self._countdown_label = QLabel("", self)
        self._countdown_label.setAlignment(ALIGN_CENTER)
        self._countdown_label.setStyleSheet(
            "color: white; background: transparent; font-size: 220px; font-weight: 700;"
        )
        self._countdown_label.setGeometry(self.rect())
        self._countdown_label.setAttribute(WA_TRANSPARENT, True)
        self._countdown_label.hide()
        self._retry_overlay_label = QLabel("", self)
        self._retry_overlay_label.setAlignment(ALIGN_CENTER)
        self._retry_overlay_label.setStyleSheet(
            "color: white; background-color: rgba(0, 0, 0, 160); font-size: 64px; font-weight: 700;"
        )
        self._retry_overlay_label.setGeometry(self.rect())
        self._retry_overlay_label.setAttribute(WA_TRANSPARENT, True)
        self._retry_overlay_label.hide()
        self._camera_error_label = QLabel("", self)
        self._camera_error_label.setAlignment(ALIGN_CENTER)
        self._camera_error_label.setStyleSheet(
            "color: white; background-color: rgba(120, 0, 0, 180); font-size: 56px; font-weight: 700;"
        )
        self._camera_error_label.setGeometry(self.rect())
        self._camera_error_label.setAttribute(WA_TRANSPARENT, True)
        self._camera_error_label.hide()
        self._deferred_stop_timer = QTimer(self)
        self._deferred_stop_timer.setSingleShot(True)
        self._deferred_stop_timer.timeout.connect(self._on_deferred_stop_timeout)
        self._overlay.setAttribute(WA_TRANSPARENT, True)
        self.setFocusPolicy(STRONG_FOCUS)
        self._liveview_design_rect: tuple[int, int, int, int] = self.LIVEVIEW_RECT_BY_LAYOUT.get(
            "2641", (460, 140, 1000, 800)
        )
        self._last_liveview_image: Optional[QImage] = None
        self._shots_raw_dir: Optional[Path] = None
        self._overlay_sequence_cache: dict[str, list[Path]] = {}
        self._overlay_pixmap_cache: dict[tuple[str, int, int, int], QPixmap] = {}
        runtime_sessions = getattr(main_window, "_runtime_sessions_dir", None)
        try:
            if runtime_sessions:
                self._runtime_sessions_dir = Path(runtime_sessions)
            else:
                self._runtime_sessions_dir = _resolve_runtime_sessions_dir()
        except Exception:
            self._runtime_sessions_dir = _default_runtime_data_dir() / "sessions"

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self._deferred_stop_timer.stop()
        self.auto_mode = True
        self.auto_wait_frame = True
        self.countdown_running = False
        self.capture_inflight = False
        print("[CAMERA] auto_mode enabled")
        self._start_liveview_worker()
        self.setFocus()

    def hideEvent(self, event):  # noqa: N802
        immediate_stop = bool(self.capture_inflight)
        self.auto_mode = False
        self.auto_wait_frame = False
        self.countdown_running = False
        self.capture_inflight = False
        self.cancel_countdown()
        self._clear_gif_burst_timers()
        self._retry_overlay_timer.stop()
        self._hide_retry_overlay()
        self._pending_dummy_fallback_reason = None
        self._auto_next_pending = False
        self._capture_pending_after_liveview_stop = False
        self._stop_capture_worker(wait=False)
        self._last_liveview_image = None
        if immediate_stop:
            self._deferred_stop_timer.stop()
            self._stop_liveview_worker(wait=False)
        else:
            # Avoid immediate SDK teardown right after capture completion.
            self._deferred_stop_timer.start(900)
        super().hideEvent(event)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._countdown_label.setGeometry(self.rect())
        self._retry_overlay_label.setGeometry(self.rect())
        self._camera_error_label.setGeometry(self.rect())

    def mousePressEvent(self, event: QMouseEvent):  # noqa: N802
        if event.button() == LEFT_BUTTON:
            pos = _event_pos(event)
            x, y = self.widget_to_design(pos.x(), pos.y())
            print(f"[CAMERA_CLICK] x={x} y={y}")
        super().mousePressEvent(event)

    def cancel_countdown(self) -> None:
        self._countdown_timer.stop()
        self._countdown_value = 0
        self._countdown_active = False
        self.countdown_running = False
        self._countdown_label.hide()

    def _auto_shoot_step(self) -> None:
        if not self.auto_mode:
            return
        if not self.isVisible():
            return
        if self.auto_wait_frame:
            return
        if self.countdown_running or self.capture_inflight:
            return
        if self.capture_slots > 0 and len(self.shot_paths) >= self.capture_slots:
            return
        shot_index = len(self.shot_paths) + 1
        print(f"[CAMERA] auto trigger shot_index={shot_index}")
        self.request_shutter()

    def _schedule_auto_continue(self, delay_ms: int = 600) -> None:
        if not self.auto_mode:
            return
        if self.capture_slots > 0 and len(self.shot_paths) >= self.capture_slots:
            return
        print(f"[CAMERA] auto continue next in {delay_ms}ms")
        QTimer.singleShot(max(100, int(delay_ms)), self._auto_shoot_step)

    def _clear_gif_burst_timers(self) -> None:
        for timer in self._gif_burst_timers:
            try:
                timer.stop()
            except Exception:
                pass
            timer.deleteLater()
        self._gif_burst_timers = []

    def reset_gif_capture_state(self) -> None:
        self._clear_gif_burst_timers()
        self._gif_frames_by_shot = {}

    def get_gif_frames_snapshot(self) -> dict[int, list[bytes]]:
        snapshot: dict[int, list[bytes]] = {}
        for shot_index, frames in self._gif_frames_by_shot.items():
            snapshot[int(shot_index)] = [bytes(frame) for frame in frames]
        return snapshot

    def _start_gif_burst_capture(self, shot_index: int) -> None:
        if shot_index <= 0:
            return
        gif_settings = {}
        if hasattr(self.main_window, "get_gif_settings"):
            gif_settings = self.main_window.get_gif_settings()
        if not bool(gif_settings.get("enabled", True)):
            return
        frames_per_shot = max(1, int(gif_settings.get("frames_per_shot", 3)))
        interval_ms = max(50, int(gif_settings.get("interval_ms", 200)))
        for frame_idx in range(frames_per_shot):
            timer = QTimer(self)
            timer.setSingleShot(True)
            delay_ms = frame_idx * interval_ms

            def _on_timeout(
                shot=shot_index,
                grab=frame_idx + 1,
                active_timer=timer,
            ) -> None:
                if active_timer in self._gif_burst_timers:
                    self._gif_burst_timers.remove(active_timer)
                self._grab_one_gif_frame(shot, grab)
                active_timer.deleteLater()

            timer.timeout.connect(_on_timeout)
            self._gif_burst_timers.append(timer)
            timer.start(delay_ms)

    def _grab_one_gif_frame(self, shot_index: int, grab_index: int) -> None:
        data = self._make_gif_grab_bytes()
        if not data:
            print(f"[GIF] shot={shot_index:02d} grab={grab_index} skipped(no frame)")
            return
        bucket = self._gif_frames_by_shot.setdefault(int(shot_index), [])
        bucket.append(data)
        print(f"[GIF] shot={shot_index:02d} grab={grab_index} ok size={len(data)}")

    def _make_gif_grab_bytes(self) -> Optional[bytes]:
        gif_settings = {}
        if hasattr(self.main_window, "get_gif_settings"):
            gif_settings = self.main_window.get_gif_settings()
        max_width = max(160, int(gif_settings.get("max_width", 480)))

        source = self._last_liveview_image
        if source is None or source.isNull():
            raw = self._last_liveview_jpeg
            if raw:
                parsed = QImage.fromData(raw, "JPG")
                if not parsed.isNull():
                    source = parsed
        if source is None or source.isNull():
            return None

        frame = source
        if frame.width() > max_width:
            frame = frame.scaledToWidth(max_width, SMOOTH_TRANSFORM)

        payload = QByteArray()
        buffer = QBuffer(payload)
        if not buffer.open(QIODevice.WriteOnly):
            return None
        try:
            ok = frame.save(buffer, "JPG", 82)
        finally:
            buffer.close()
        if not ok:
            return None
        data = bytes(payload)
        return data or None

    def _clear_celebrity_overlay_cache(self) -> None:
        self._overlay_sequence_cache = {}
        self._overlay_pixmap_cache = {}

    def _is_celebrity_mode(self) -> bool:
        mode = ""
        if self.session is not None:
            mode = str(getattr(self.session, "compose_mode", "")).strip().lower()
        if not mode:
            mode = str(getattr(self.main_window, "compose_mode", "")).strip().lower()
        return mode == "celebrity"

    def _resolve_celebrity_template_dir(self) -> Optional[Path]:
        raw = None
        if self.session is not None:
            raw = getattr(self.session, "celebrity_template_dir", None)
        if not raw:
            raw = getattr(self.main_window, "celebrity_template_dir", None)
        if raw is None:
            return None
        try:
            candidate = Path(str(raw))
        except Exception:
            return None
        if candidate.is_dir():
            return candidate
        return None

    @staticmethod
    def _overlay_name_sort_key(path: Path) -> tuple[int, int, str]:
        stem = path.stem.strip()
        if stem.isdigit():
            return (0, int(stem), path.name.lower())
        match = re.search(r"\d+", stem)
        if match:
            return (1, int(match.group(0)), path.name.lower())
        return (2, 0, path.name.lower())

    def _get_celebrity_overlay_sequence(self, template_dir: Path) -> list[Path]:
        key = str(template_dir)
        cached = self._overlay_sequence_cache.get(key)
        if cached is not None:
            return cached
        overlay_dir = template_dir / "overlays"
        items: list[Path] = []
        if overlay_dir.is_dir():
            items = sorted(
                [p for p in overlay_dir.glob("*.png") if p.is_file()],
                key=self._overlay_name_sort_key,
            )
        self._overlay_sequence_cache[key] = items
        return items

    def get_overlay_path(self, template_dir: Path, shot_index: int) -> Optional[Path]:
        if shot_index < 1:
            return None
        overlay_dir = template_dir / "overlays"
        direct = overlay_dir / f"{shot_index:02d}.png"
        if direct.is_file():
            return direct
        sequence = self._get_celebrity_overlay_sequence(template_dir)
        if not sequence:
            return None
        if shot_index <= len(sequence):
            return sequence[shot_index - 1]
        # Missing future index: reuse the last overlay as fallback.
        return sequence[-1]

    def _current_overlay_path_for_liveview(self, shot_index: int) -> Optional[Path]:
        if not self._is_celebrity_mode():
            return None
        template_dir = self._resolve_celebrity_template_dir()
        if template_dir is None:
            return None
        return self.get_overlay_path(template_dir, shot_index)

    def _overlay_pixmap_for_liveview(
        self,
        shot_index: int,
        width: int,
        height: int,
    ) -> Optional[QPixmap]:
        if width <= 0 or height <= 0:
            return None
        overlay_path = self._current_overlay_path_for_liveview(shot_index)
        if overlay_path is None:
            return None
        key = (str(overlay_path), int(shot_index), int(width), int(height))
        cached = self._overlay_pixmap_cache.get(key)
        if cached is not None and not cached.isNull():
            return cached
        raw = QPixmap(str(overlay_path))
        if raw.isNull():
            return None
        scaled = raw.scaled(width, height, IGNORE_ASPECT, SMOOTH_TRANSFORM)
        self._overlay_pixmap_cache[key] = scaled
        return scaled

    def _apply_liveview_overlay(self, pixmap: QPixmap, shot_index: int) -> QPixmap:
        if pixmap.isNull() or shot_index <= 0:
            return pixmap
        overlay = self._overlay_pixmap_for_liveview(shot_index, pixmap.width(), pixmap.height())
        if overlay is None or overlay.isNull():
            return pixmap
        composed = QPixmap(pixmap)
        painter = QPainter(composed)
        painter.drawPixmap(0, 0, overlay)
        painter.end()
        return composed

    def _ensure_shots_raw_dir(self) -> Optional[Path]:
        if self.session is None:
            return None
        if self._shots_raw_dir is None:
            self._shots_raw_dir = self.session.session_dir / "shots_raw"
        try:
            self._shots_raw_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            print(f"[CELEB] shots_raw mkdir failed: {exc}")
            return None
        return self._shots_raw_dir

    def _save_celebrity_composited_shot(self, source_path: Path, index: int) -> Path:
        if self.session is None:
            return source_path

        template_dir = self._resolve_celebrity_template_dir()
        overlay_path = self.get_overlay_path(template_dir, index) if template_dir is not None else None
        raw_target: Optional[Path] = None
        raw_dir = self._ensure_shots_raw_dir()
        if raw_dir is not None:
            raw_target = raw_dir / f"shot_{index:02d}.jpg"

        with Image.open(source_path) as source_img:
            base_rgb = source_img.convert("RGB")
            if raw_target is not None:
                base_rgb.save(raw_target, format="JPEG", quality=95)

            if overlay_path is not None and overlay_path.is_file():
                with Image.open(overlay_path) as overlay_img:
                    overlay_rgba = overlay_img.convert("RGBA")
                    if overlay_rgba.size != base_rgb.size:
                        if hasattr(Image, "Resampling"):
                            overlay_rgba = overlay_rgba.resize(base_rgb.size, Image.Resampling.LANCZOS)
                        else:
                            overlay_rgba = overlay_rgba.resize(base_rgb.size, Image.LANCZOS)
                composed = Image.alpha_composite(base_rgb.convert("RGBA"), overlay_rgba).convert("RGB")
                saved = self.session.save_shot(composed, index)
                print(f"[CELEB] shot={index} overlay={overlay_path} applied=1")
                return saved

            saved = self.session.save_shot(base_rgb, index)
            print(f"[CELEB] shot={index} overlay missing -> applied=0")
            return saved

    def _save_capture_result(self, source_path: Path, index: int) -> Path:
        if self.session is None:
            return source_path
        if self._is_celebrity_mode():
            try:
                return self._save_celebrity_composited_shot(source_path, index)
            except Exception as exc:
                print(f"[CELEB] shot={index} overlay apply failed: {exc}")
        return self.session.save_shot(source_path, index)

    def _hide_retry_overlay(self) -> None:
        self._retry_overlay_active = False
        self._retry_overlay_label.hide()

    def _show_retry_overlay(self, message: str, duration_ms: int = 1500) -> None:
        self._retry_overlay_active = True
        self._retry_overlay_label.setText(message)
        self._retry_overlay_label.show()
        self._retry_overlay_label.raise_()
        self._retry_overlay_timer.start(max(500, int(duration_ms)))

    def _show_camera_connection_error(self, message: str) -> None:
        self._camera_connection_blocked = True
        self._camera_error_label.setText(message)
        self._camera_error_label.show()
        self._camera_error_label.raise_()

    def _clear_camera_connection_error(self) -> None:
        self._camera_connection_blocked = False
        self._camera_error_label.hide()

    def _halt_capture_for_operator(self, error_message: str, notice: str) -> None:
        # In operation mode, do not auto-continue after camera transfer/capture failures.
        self._finish_capture_cycle()
        self.cancel_countdown()
        self.auto_mode = False
        self.auto_wait_frame = False
        self._show_camera_connection_error(notice)
        print(f"[CAMERA] capture halted operator_intervention=1 reason={error_message}")

    def _is_dummy_fallback_allowed(self) -> bool:
        if hasattr(self.main_window, "allow_dummy_when_camera_fail"):
            return bool(self.main_window.allow_dummy_when_camera_fail())
        # Legacy fallback: if runtime method is unavailable, allow only in test mode.
        if hasattr(self.main_window, "is_test_mode"):
            return bool(self.main_window.is_test_mode())
        return False

    def _log_backend(self, backend: str, reason: str) -> None:
        self._backend_active = backend
        self._backend_reason = reason
        print(f"[CAMERA] backend={backend} reason={reason}")

    def request_shutter(self) -> None:
        if self._camera_connection_blocked:
            print("[CAMERA] shutter blocked: camera connection error")
            return
        if self._retry_overlay_active:
            print("[CAMERA] shutter blocked: retry overlay active")
            return
        if self._countdown_active:
            print("[CAMERA] shutter blocked: countdown in progress")
            return
        if self._shutter_locked:
            print("[CAMERA] shutter blocked: capture in progress")
            return
        if not self.layout_id:
            print("[CAMERA] shutter blocked: layout_id missing")
            return
        if self.capture_slots <= 0 and self.layout_id:
            self.capture_slots = CAPTURE_SLOT_OVERRIDE_BY_LAYOUT.get(
                self.layout_id,
                EXPECTED_SLOT_COUNT_BY_LAYOUT.get(self.layout_id, 4),
            )
        if len(self.shot_paths) >= self.capture_slots:
            print(
                f"[CAMERA] shutter blocked: full ({len(self.shot_paths)}/{self.capture_slots})"
            )
            return

        next_shot_index = len(self.shot_paths) + 1
        self._start_gif_burst_capture(next_shot_index)

        countdown_seconds = 3
        if hasattr(self.main_window, "get_countdown_seconds"):
            countdown_seconds = int(self.main_window.get_countdown_seconds())
        countdown_seconds = max(0, min(10, countdown_seconds))
        print(f"[CAMERA] countdown_seconds={countdown_seconds}")
        if countdown_seconds <= 0:
            print("[CAMERA] countdown skipped: 0")
            self.countdown_running = False
            self.capture_inflight = True
            self.trigger_shutter()
            return

        self._countdown_active = True
        self.countdown_running = True
        self._countdown_value = countdown_seconds
        self._countdown_label.setText(str(self._countdown_value))
        self._countdown_label.show()
        self._countdown_label.raise_()
        print(f"[CAMERA] countdown start: {countdown_seconds}")
        self._countdown_timer.start()

    def _on_countdown_tick(self) -> None:
        if not self._countdown_active:
            self._countdown_timer.stop()
            self.countdown_running = False
            return

        self._countdown_value -= 1
        if self._countdown_value > 0:
            self._countdown_label.setText(str(self._countdown_value))
            print(f"[CAMERA] countdown: {self._countdown_value}")
            return

        self._countdown_timer.stop()
        self._countdown_label.setText("0")
        print("[CAMERA] countdown: 0")
        self._countdown_active = False
        self.countdown_running = False
        self._countdown_label.hide()
        self.capture_inflight = True
        self.trigger_shutter()

    def _start_liveview_worker_instance(self, worker: QObject, backend: str, reason: str) -> None:
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.frame.connect(self._on_liveview_frame)
        worker.fps.connect(self._on_liveview_fps)
        worker.capture_success.connect(self._on_capture_success)
        worker.capture_failure.connect(self._on_capture_failure)
        worker.error.connect(self._on_liveview_error)
        worker.stopped.connect(thread.quit)
        worker.stopped.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_liveview_thread_finished)

        self._liveview_worker = worker
        self._liveview_thread = thread
        self._liveview_running = True
        self._pending_restart_after_liveview_stop = False
        self._liveview_frame_received = False
        self._clear_camera_connection_error()
        self._log_backend(backend, reason)
        print(f"[CAMERA] liveview worker start backend={backend}")
        thread.start()

    def _start_liveview_worker(self) -> None:
        if self._liveview_thread is not None and self._liveview_thread.isRunning():
            return
        requested = (self.camera_backend or "auto").strip().lower()
        if requested not in {"auto", "edsdk", "dummy"}:
            requested = "auto"
        self._pending_dummy_fallback_reason = None

        if requested == "dummy":
            self._start_liveview_worker_instance(
                DummyLiveViewWorker(fps_target=24),
                "dummy",
                "config_dummy",
            )
            return

        if not self.liveview_dll_path:
            reason = "dll_path_missing"
            if self._is_dummy_fallback_allowed():
                self._start_liveview_worker_instance(
                    DummyLiveViewWorker(fps_target=24),
                    "fallback_dummy",
                    reason,
                )
                return
            self._log_backend("edsdk", reason)
            self._show_camera_connection_error("카메라 연결 실패")
            return

        self._start_liveview_worker_instance(
            LiveViewWorker(self.liveview_dll_path, retries=200, capture_timeout_ms=5000),
            "edsdk",
            f"requested_{requested}",
        )

    def _stop_liveview_worker(self, wait: bool = False) -> None:
        worker = self._liveview_worker
        thread = self._liveview_thread
        if worker is None and thread is None:
            return

        print("[CAMERA] liveview worker stop requested")
        if worker is not None:
            worker.stop()
        if wait and thread is not None and thread.isRunning():
            if not thread.wait(5000):
                print("[CAMERA] liveview worker stop timeout")

    def _on_liveview_frame(self, jpeg_bytes: bytes) -> None:
        image = QImage.fromData(jpeg_bytes, "JPG")
        if image.isNull():
            return
        if len(jpeg_bytes) <= (2 * 1024 * 1024):
            self._last_liveview_jpeg = bytes(jpeg_bytes)
        else:
            # Some SDK streams report oversized buffers (~8MB). Keep a compact copy only.
            self._last_liveview_jpeg = None
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return
        shot_index = self._capture_target_index or (len(self.shot_paths) + 1)
        if self.capture_slots > 0:
            shot_index = max(1, min(int(shot_index), int(self.capture_slots)))
        pixmap = self._apply_liveview_overlay(pixmap, int(shot_index))
        self._last_liveview_image = pixmap.toImage()
        self._liveview_frame_received = True
        self._clear_camera_connection_error()
        self._liveview_pixmap = pixmap
        self.update()
        if self.auto_mode and self.auto_wait_frame:
            self.auto_wait_frame = False
            print("[CAMERA] auto first-frame received -> start loop")
            QTimer.singleShot(300, self._auto_shoot_step)

    def _on_liveview_fps(self, fps: float) -> None:
        if self._liveview_running:
            print(f"[CAMERA] liveview fps={fps:.1f}")

    def _on_liveview_error(self, error_message: str) -> None:
        print(f"[CAMERA] liveview error: {error_message}")
        if self._backend_active == "edsdk" and self._is_dummy_fallback_allowed():
            self._pending_dummy_fallback_reason = f"edsdk_error:{error_message}"
            print(
                "[CAMERA] backend=fallback_dummy "
                f"reason={self._pending_dummy_fallback_reason}"
            )
            worker = self._liveview_worker
            if worker is not None:
                worker.stop()
            return

        if self._backend_active in {"edsdk", "idle"}:
            self._log_backend("edsdk", f"error:{error_message}")
        self._show_camera_connection_error("카메라 연결 실패")
        worker = self._liveview_worker
        if worker is not None:
            worker.stop()

    def _on_liveview_thread_finished(self) -> None:
        sender_thread = self.sender()
        if (
            sender_thread is not None
            and self._liveview_thread is not None
            and sender_thread is not self._liveview_thread
        ):
            print("[CAMERA] liveview worker finished from stale thread -> ignored")
            return
        self._liveview_worker = None
        self._liveview_thread = None
        self._liveview_running = False
        print("[CAMERA] liveview worker stopped")
        self._capture_pending_after_liveview_stop = False
        if self._pending_restart_after_liveview_stop:
            if self.isVisible():
                print("[CAMERA] timeout recovery resume -> restart liveview/edsdk")
                self._resume_edsdk_timeout_recovery()
            else:
                self._pending_restart_after_liveview_stop = False
            return
        if self._pending_dummy_fallback_reason and self.isVisible():
            reason = self._pending_dummy_fallback_reason
            self._pending_dummy_fallback_reason = None
            self._start_liveview_worker_instance(
                DummyLiveViewWorker(fps_target=24),
                "fallback_dummy",
                reason,
            )

    def _on_deferred_stop_timeout(self) -> None:
        if self.isVisible():
            return
        self._stop_liveview_worker(wait=False)

    def _stop_capture_worker(self, wait: bool = False) -> None:
        _ = wait
        self._capture_thread = None
        self._capture_worker = None
        self._capture_pending_after_liveview_stop = False
        self._capture_target_index = None
        self._capture_target_path = None
        self._shutter_locked = False
        self.capture_inflight = False

    def _start_capture_worker(self) -> None:
        index = self._capture_target_index
        out_path = self._capture_target_path
        if index is None or out_path is None:
            self._finish_capture_cycle()
            return

        if self._camera_connection_blocked:
            self._on_capture_failure("camera connection unavailable")
            return

        worker = self._liveview_worker
        thread = self._liveview_thread
        if worker is None or thread is None or not thread.isRunning():
            if self._pending_restart_after_liveview_stop and self._backend_active == "edsdk":
                print("[CAMERA] capture deferred: timeout recovery still in progress")
                self._finish_capture_cycle()
                self._show_retry_overlay(
                    "Transfer recovery in progress\nPlease retry",
                    duration_ms=1200,
                )
                self._schedule_auto_continue(1300)
                return
            if self._is_dummy_fallback_allowed():
                try:
                    saved = self.capture_still(index)
                    print(
                        "[CAMERA] capture fallback: worker missing -> "
                        f"dummy path={saved}"
                    )
                    self._finalize_saved_shot(saved, index)
                except Exception as exc:
                    self._on_capture_failure(f"dummy capture failed: {exc}")
                return
            self._on_capture_failure("camera worker not running")
            return

        print(
            f"[CAMERA] starting capture request... out={out_path} "
            f"backend={self._backend_active}"
        )
        worker.request_capture(out_path)

    def _finalize_saved_shot(self, saved: Path, index: int) -> None:
        if len(self.shot_paths) >= index:
            self.shot_paths[index - 1] = saved
        elif len(self.shot_paths) == index - 1:
            self.shot_paths.append(saved)
        if self.session is not None:
            next_index = len(self.shot_paths) + 1
            if self.capture_slots > 0:
                next_index = min(next_index, self.capture_slots)
            setattr(self.session, "current_shot_index", int(max(1, next_index)))
        self.update()
        print(f"[CAMERA] capture saved: {saved}")
        self._finish_capture_cycle()
        self._schedule_auto_next_if_complete()
        self._schedule_auto_continue(600)

    def _on_capture_success(self, out_path: str) -> None:
        index = self._capture_target_index
        if index is None:
            self._finish_capture_cycle()
            return
        self._capture_timeout_streak = 0

        source = Path(out_path)
        saved = source
        try:
            if self.session is not None:
                saved = self._save_capture_result(source, index)
        except Exception as exc:
            print(f"[CAMERA] capture save normalize failed: {exc}")
        self._finalize_saved_shot(saved, index)

    def _on_capture_failure(self, error_message: str) -> None:
        index = self._capture_target_index
        normalized = (error_message or "").upper()
        print(f"[CAMERA] capture failed: {error_message}")
        if "0X00008D01" in normalized or "AF_NG" in normalized:
            self._finish_capture_cycle()
            print("[CAMERA] AF_NG -> show retry overlay")
            self._show_retry_overlay(
                "Focus failed\nCheck light/distance and retry",
                duration_ms=1500,
            )
            self._schedule_auto_continue(1700)
            return
        if "TIMEOUT" in normalized or "DIR ITEM" in normalized:
            self._capture_timeout_streak += 1
            if not self._is_dummy_fallback_allowed():
                self._halt_capture_for_operator(
                    error_message,
                    "카메라 전송 실패\n관리자를 호출해주세요",
                )
                return
            self._finish_capture_cycle()
            if self._capture_timeout_streak >= 1:
                self._recover_edsdk_after_capture_timeout()
            self._show_retry_overlay(
                "Transfer failed (USB/settings)\nPlease retry",
                duration_ms=1500,
            )
            self._schedule_auto_continue(1700)
            return

        if self._is_dummy_fallback_allowed() and index is not None:
            try:
                saved = self.capture_still(index)
                print(f"[CAMERA] capture failed -> dummy fallback path={saved}")
                self._finalize_saved_shot(saved, index)
                return
            except Exception as exc:
                print(f"[CAMERA] dummy fallback failed: {exc}")

        self._halt_capture_for_operator(
            error_message,
            "카메라 촬영 실패\n관리자를 호출해주세요",
        )

    def _recover_edsdk_after_capture_timeout(self) -> None:
        if self._backend_active != "edsdk":
            return
        print(
            f"[CAMERA] timeout recovery start streak={self._capture_timeout_streak} "
            "-> restart liveview/edsdk"
        )
        self.cancel_countdown()
        self._stop_capture_worker(wait=False)
        self._pending_restart_after_liveview_stop = True
        self._stop_liveview_worker(wait=True)
        thread = self._liveview_thread
        if thread is not None and thread.isRunning():
            print("[CAMERA] timeout recovery deferred: waiting for liveview worker to stop")
            return
        self._resume_edsdk_timeout_recovery()

    def _resume_edsdk_timeout_recovery(self) -> None:
        self._pending_restart_after_liveview_stop = False
        try:
            terminate_edsdk_once()
        except Exception as exc:
            print(f"[CAMERA] timeout recovery terminate failed: {exc}")
        self.auto_wait_frame = True
        self._liveview_frame_received = False
        self._start_liveview_worker()

    def _on_capture_thread_finished(self) -> None:
        self._capture_worker = None
        self._capture_thread = None
        print("[CAMERA] capture worker stopped")

    def _finish_capture_cycle(self) -> None:
        self._capture_target_index = None
        self._capture_target_path = None
        self._shutter_locked = False
        self.capture_inflight = False

    def _schedule_auto_next_if_complete(self) -> None:
        if self.capture_slots <= 0:
            return
        if len(self.shot_paths) != self.capture_slots:
            return
        if self._auto_next_pending:
            return
        self._auto_next_pending = True
        delay_ms = 300
        gif_settings = {}
        if hasattr(self.main_window, "get_gif_settings"):
            gif_settings = self.main_window.get_gif_settings()
        if bool(gif_settings.get("enabled", True)):
            frames_per_shot = max(1, int(gif_settings.get("frames_per_shot", 3)))
            interval_ms = max(50, int(gif_settings.get("interval_ms", 200)))
            delay_ms = max(delay_ms, (frames_per_shot - 1) * interval_ms + 80)
        print(
            f"[CAMERA] shots complete {self.capture_slots}/{self.capture_slots} "
            "-> goto after_camera_loading"
        )
        print("[NAV] camera -> after_camera_loading")
        QTimer.singleShot(delay_ms, self._run_auto_next)

    def _run_auto_next(self) -> None:
        self._auto_next_pending = False
        if not self.isVisible():
            return
        if self.capture_slots <= 0 or len(self.shot_paths) < self.capture_slots:
            return
        self.main_window.enter_select_photo_from_camera()

    def _find_overlay_path(self, layout_id: str) -> Path:
        fixed_names = {
            "2641": "2641_smallvertical.png",
            "6241": "6241_smallhorizontal.png",
            "4641": "4641_bigvertical.png",
            "4661": "4661_bigvertical.png",
            "4681": "4681__bigvertical.png",
        }
        fixed = self.camera_dir / fixed_names.get(layout_id, "2641_smallvertical.png")
        if fixed.is_file():
            return fixed

        candidates = sorted(
            [p for p in self.camera_dir.glob("*.png") if layout_id in p.stem],
            key=lambda p: p.name.lower(),
        )
        if candidates:
            return candidates[0]
        return fixed

    def _find_overlay_candidates(self, layout_id: str) -> list[Path]:
        fixed = self._find_overlay_path(layout_id)
        candidates = [p for p in self.camera_dir.glob("*.png") if layout_id in p.stem]
        ordered: list[Path] = []
        seen: set[Path] = set()
        for path in [fixed, *sorted(candidates, key=lambda p: p.name.lower())]:
            if path in seen:
                continue
            seen.add(path)
            ordered.append(path)
        return ordered

    def _detect_overlay_slots(self, overlay_path: Path) -> list[tuple[int, int, int, int]]:
        if not overlay_path.is_file():
            return []
        try:
            with Image.open(overlay_path) as source:
                rgba = source.convert("RGBA")
        except Exception as exc:
            print(f"[CAMERA] overlay open failed: {overlay_path} ({exc})")
            return []
        components = _detect_gray_slot_components(rgba)
        rects = [rect for rect, _area in components]
        rects.sort(key=lambda r: (r[1], r[0]))
        return rects

    def _fallback_grid_slots(self, required: int) -> list[tuple[int, int, int, int]]:
        if required <= 0:
            return []
        cols = 1 if required == 1 else 2
        rows = math.ceil(required / cols)
        margin_x = 140
        margin_y = 120
        gap_x = 60
        gap_y = 40
        avail_w = DESIGN_WIDTH - margin_x * 2 - gap_x * (cols - 1)
        avail_h = DESIGN_HEIGHT - margin_y * 2 - gap_y * (rows - 1)
        cell_w = max(1, int(avail_w / cols))
        cell_h = max(1, int(avail_h / rows))

        slots: list[tuple[int, int, int, int]] = []
        for i in range(required):
            row = i // cols
            col = i % cols
            x = margin_x + col * (cell_w + gap_x)
            y = margin_y + row * (cell_h + gap_y)
            slots.append((x, y, cell_w, cell_h))
        return slots

    def _resolve_slots_for_overlay(
        self,
        overlay_path: Path,
        layout_id: str,
        required: int,
    ) -> tuple[list[tuple[int, int, int, int]], str]:
        source = "detected"
        try:
            slots, source = resolve_slots(overlay_path, layout_id)
        except Exception as exc:
            print(f"[CAMERA] slot detect failed: {exc}")
            slots = []
            source = "camera_grid_fallback"

        if len(slots) < required:
            slots = self._fallback_grid_slots(required)
            source = "camera_grid_fallback"
        elif len(slots) > required:
            slots = slots[:required]
        return slots, source

    def _select_overlay_for_layout(
        self, layout_id: str
    ) -> tuple[Path, list[tuple[int, int, int, int]], int, str]:
        best_path: Optional[Path] = None
        best_rects: list[tuple[int, int, int, int]] = []
        for candidate in self._find_overlay_candidates(layout_id):
            rects = self._detect_overlay_slots(candidate)
            if len(rects) > len(best_rects):
                best_path = candidate
                best_rects = rects

        if best_path is None:
            best_path = self._find_overlay_path(layout_id)

        print(f"[CAMERA] overlay selected: {best_path} slots={len(best_rects)}")

        capture_slots = len(best_rects)
        source = "detected"
        if capture_slots <= self.print_slots:
            override_slots = CAPTURE_SLOT_OVERRIDE_BY_LAYOUT.get(layout_id)
            if override_slots is not None and override_slots > capture_slots:
                capture_slots = override_slots
                source = "override"

        if capture_slots <= 0:
            capture_slots = max(self.print_slots, 1)
            source = "fallback"

        if len(best_rects) < capture_slots:
            best_rects = self._fallback_grid_slots(capture_slots)
            if source == "detected":
                source = "camera_grid_fallback"

        return best_path, best_rects, capture_slots, source

    def _compute_liveview_design_rect(self, layout_id: str) -> tuple[int, int, int, int]:
        base_rect = self.LIVEVIEW_RECT_BY_LAYOUT.get(layout_id, (460, 140, 1000, 800))
        x, y, w, h = [int(v) for v in base_rect]
        if layout_id in {"6241", "4641"} and self.slot_rects:
            # Compute the largest horizontal gap between detected placeholder columns,
            # then place liveview in that central safe area.
            centers = sorted(
                ((sx + (sw / 2.0), idx) for idx, (sx, _sy, sw, _sh) in enumerate(self.slot_rects)),
                key=lambda item: item[0],
            )
            if len(centers) >= 2:
                best_gap = -1.0
                split_idx = -1
                for i in range(len(centers) - 1):
                    gap = centers[i + 1][0] - centers[i][0]
                    if gap > best_gap:
                        best_gap = gap
                        split_idx = i
                if split_idx >= 0:
                    left_ids = {idx for _cx, idx in centers[: split_idx + 1]}
                    right_ids = {idx for _cx, idx in centers[split_idx + 1 :]}
                    left_right_edge = max(
                        (sx + sw for i, (sx, _sy, sw, _sh) in enumerate(self.slot_rects) if i in left_ids),
                        default=0,
                    )
                    right_left_edge = min(
                        (sx for i, (sx, _sy, _sw, _sh) in enumerate(self.slot_rects) if i in right_ids),
                        default=DESIGN_WIDTH,
                    )
                    pad = 46
                    safe_left = int(left_right_edge + pad)
                    safe_right = int(right_left_edge - pad)
                    safe_width = safe_right - safe_left
                    if safe_width >= 320:
                        new_w = min(w, safe_width)
                        base_cx = x + (w / 2.0)
                        desired_x = int(round(base_cx - (new_w / 2.0)))
                        min_x = safe_left
                        max_x = max(min_x, safe_right - new_w)
                        new_x = max(min_x, min(desired_x, max_x))
                        return (int(new_x), y, int(new_w), h)
            return (x, y, w, h)
        if not self.slot_rects:
            return (x, y, w, h)

        center_x = DESIGN_WIDTH // 2
        left_group_rights = [sx + sw for sx, _sy, sw, _sh in self.slot_rects if (sx + sw) <= center_x + 40]
        right_group_lefts = [sx for sx, _sy, _sw, _sh in self.slot_rects if sx >= center_x - 40]
        if not left_group_rights or not right_group_lefts:
            return (x, y, w, h)

        safe_left = max(left_group_rights) + 46
        safe_right = min(right_group_lefts) - 46
        safe_width = safe_right - safe_left
        if safe_width < 320:
            return (x, y, w, h)

        new_w = min(w, safe_width)
        new_x = safe_left + max(0, (safe_width - new_w) // 2)
        return (int(new_x), y, int(new_w), h)

    @staticmethod
    def _pick_ai_mode_capture_rects(
        rects: list[tuple[int, int, int, int]],
        required: int = AI_CAPTURE_SLOTS,
    ) -> list[tuple[int, int, int, int]]:
        normalized = [
            tuple(int(v) for v in rect)
            for rect in rects
            if isinstance(rect, (list, tuple)) and len(rect) == 4 and int(rect[2]) > 0 and int(rect[3]) > 0
        ]
        if len(normalized) < required:
            return []

        centers = sorted(
            [((x + (w / 2.0)), idx) for idx, (x, _y, w, _h) in enumerate(normalized)],
            key=lambda item: item[0],
        )
        if len(centers) < 2:
            return []

        best_gap = -1.0
        split_idx = -1
        for i in range(len(centers) - 1):
            gap = centers[i + 1][0] - centers[i][0]
            if gap > best_gap:
                best_gap = gap
                split_idx = i
        if split_idx < 0:
            return []

        left_ids = {idx for _cx, idx in centers[: split_idx + 1]}
        right_ids = {idx for _cx, idx in centers[split_idx + 1 :]}
        if len(left_ids) < 2 or len(right_ids) < 2:
            return []

        left_rects = sorted((normalized[idx] for idx in left_ids), key=lambda r: (r[1], r[0]))
        right_rects = sorted((normalized[idx] for idx in right_ids), key=lambda r: (r[1], r[0]))
        chosen = left_rects[:2] + right_rects[:2]  # left 2 + right 2
        if len(chosen) < required:
            return []
        return [tuple(int(v) for v in rect) for rect in chosen[:required]]

    def set_layout(self, layout_id: str) -> None:
        self.layout_id = layout_id
        self._overlay_pixmap_cache = {}
        self.print_slots = EXPECTED_SLOT_COUNT_BY_LAYOUT.get(layout_id, 4)
        overlay_path, capture_rects, capture_slots, slot_source = self._select_overlay_for_layout(
            layout_id
        )
        try:
            if (
                hasattr(self.main_window, "is_ai_mode_active")
                and bool(self.main_window.is_ai_mode_active())
                and str(layout_id or "").strip() == AI_LAYOUT_ID
                and AI_CAMERA_OVERLAY_PATH.is_file()
            ):
                ai_rects = self._detect_overlay_slots(AI_CAMERA_OVERLAY_PATH)
                if ai_rects:
                    overlay_path = AI_CAMERA_OVERLAY_PATH
                    capture_rects = ai_rects
                    capture_slots = len(ai_rects)
                    slot_source = "ai_overlay"
                    print(f"[AI_MODE] camera overlay applied path={AI_CAMERA_OVERLAY_PATH} slots={capture_slots}")
        except Exception as exc:
            print(f"[AI_MODE] camera overlay apply failed: {exc}")
        self._background = QPixmap(str(overlay_path))
        if self._background.isNull():
            print(f"[WARN] Camera overlay image not found: {overlay_path}")
        self.capture_slots = capture_slots
        self.slot_rects = list(capture_rects)
        if hasattr(self.main_window, "get_capture_slots_override"):
            override_slots = self.main_window.get_capture_slots_override()
            if override_slots is not None and override_slots > 0:
                self.capture_slots = int(override_slots)
                if len(self.slot_rects) < self.capture_slots:
                    self.slot_rects = self._fallback_grid_slots(self.capture_slots)
                elif len(self.slot_rects) > self.capture_slots:
                    self.slot_rects = self.slot_rects[: self.capture_slots]
                slot_source = f"admin_override:{self.capture_slots}"
        try:
            if (
                hasattr(self.main_window, "is_ai_mode_active")
                and bool(self.main_window.is_ai_mode_active())
                and str(layout_id or "").strip() == AI_LAYOUT_ID
            ):
                self.print_slots = AI_SELECT_SLOTS
                self.capture_slots = AI_CAPTURE_SLOTS
                ai_rects = self._pick_ai_mode_capture_rects(self.slot_rects, self.capture_slots)
                if len(ai_rects) >= self.capture_slots:
                    self.slot_rects = ai_rects[: self.capture_slots]
                else:
                    self.slot_rects = self._fallback_grid_slots(self.capture_slots)
                slot_source = f"ai_mode:{self.capture_slots}"
        except Exception:
            pass
        self._liveview_design_rect = self._compute_liveview_design_rect(layout_id)
        self._auto_next_pending = False
        self.shot_paths = []
        self._liveview_pixmap = None
        self.update()
        print(
            f"[CAMERA] layout={layout_id} print_slots={self.print_slots} "
            f"capture_slots={self.capture_slots} source={slot_source}"
        )
        print(f"[CAMERA] liveview_rect={self._liveview_design_rect}")

    def set_design(self, design_index: Optional[int], design_path: Optional[str]) -> None:
        self.design_index = design_index
        self.design_path = design_path
        print(f"[CAMERA] design_index={design_index} design_path={design_path}")

    def start_session(self, layout_id: Optional[str], design_path: Optional[str]) -> None:
        try:
            self.session = create_session(self._runtime_sessions_dir)
        except Exception as exc:
            print(f"[SESSION] create failed base={self._runtime_sessions_dir} err={exc}")
            if hasattr(self.main_window, "_switch_runtime_storage_to_fallback"):
                try:
                    self.main_window._switch_runtime_storage_to_fallback(
                        f"session_create_failed:{exc}"
                    )
                except Exception as fallback_exc:
                    print(f"[SESSION] fallback switch failed: {fallback_exc}")
            fallback_sessions = Path(
                getattr(self.main_window, "_runtime_sessions_dir", _default_runtime_data_dir() / "sessions")
            )
            self.session = create_session(fallback_sessions)
        self.session.set_context(layout_id=layout_id, design_path=design_path)
        self._shots_raw_dir = self.session.session_dir / "shots_raw"
        setattr(self.session, "current_shot_index", 1)
        self._auto_next_pending = False
        self._capture_timeout_streak = 0
        self.auto_wait_frame = True
        self.countdown_running = False
        self.capture_inflight = False
        self.reset_gif_capture_state()
        self._clear_celebrity_overlay_cache()
        self.shot_paths = []
        self._liveview_pixmap = None
        self._last_liveview_image = None
        self._last_liveview_jpeg = None
        self.update()
        print(f"[SESSION] created dir={self.session.session_dir} shots_reset=0")

    def _load_font(self, size: int) -> ImageFont.ImageFont:
        for name in ("arial.ttf", "malgun.ttf", "segoeui.ttf"):
            try:
                return ImageFont.truetype(name, size=size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _create_dummy_shot_image(self, index: int) -> Image.Image:
        image = Image.new("RGB", (1920, 1080), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        text = f"DUMMY SHOT {index:02d}"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        font = self._load_font(150)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=6)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (image.width - text_w) // 2
        y = (image.height - text_h) // 2 - 40
        draw.text(
            (x, y),
            text,
            fill=(20, 20, 20),
            font=font,
            stroke_width=6,
            stroke_fill=(120, 120, 120),
        )
        ts_font = self._load_font(56)
        ts_bbox = draw.textbbox((0, 0), timestamp, font=ts_font)
        ts_x = (image.width - (ts_bbox[2] - ts_bbox[0])) // 2
        draw.text((ts_x, y + text_h + 50), timestamp, fill=(70, 70, 70), font=ts_font)
        return image

    def capture_still(self, index: int) -> Path:
        if self.session is None:
            self.start_session(self.layout_id, self.design_path)
        if self.session is None:
            raise RuntimeError("Failed to create camera session.")
        dummy = self._create_dummy_shot_image(index)
        if self._is_celebrity_mode():
            raw_dir = self._ensure_shots_raw_dir()
            if raw_dir is not None:
                raw_path = raw_dir / f"shot_{index:02d}.jpg"
                dummy.save(raw_path, format="JPEG", quality=95)
                return self._save_capture_result(raw_path, index)
        return self.session.save_shot(dummy, index)

    def trigger_shutter(self) -> None:
        if not self.layout_id:
            self.capture_inflight = False
            print("[CAMERA] shutter blocked: layout_id missing")
            return
        if self.capture_slots <= 0 and self.layout_id:
            self.capture_slots = CAPTURE_SLOT_OVERRIDE_BY_LAYOUT.get(
                self.layout_id,
                EXPECTED_SLOT_COUNT_BY_LAYOUT.get(self.layout_id, 4),
            )
        if len(self.shot_paths) >= self.capture_slots:
            self.capture_inflight = False
            print(
                f"[CAMERA] shutter blocked: full ({len(self.shot_paths)}/{self.capture_slots})"
            )
            return
        if self._shutter_locked:
            self.capture_inflight = False
            print("[CAMERA] shutter blocked: capture in progress")
            return

        shot_index = len(self.shot_paths) + 1
        if self.session is None:
            self.start_session(self.layout_id, self.design_path)
        if self.session is None:
            self.capture_inflight = False
            print("[CAMERA] shutter failed: session missing")
            return

        self._shutter_locked = True
        self.capture_inflight = True
        self._capture_target_index = shot_index
        if self._is_celebrity_mode():
            raw_dir = self._ensure_shots_raw_dir()
            if raw_dir is not None:
                self._capture_target_path = raw_dir / f"shot_{shot_index:02d}.jpg"
            else:
                self._capture_target_path = self.session.shots_dir / f"shot_{shot_index:02d}.jpg"
        else:
            self._capture_target_path = self.session.shots_dir / f"shot_{shot_index:02d}.jpg"
        setattr(self.session, "current_shot_index", int(shot_index))

        print("[CAMERA] capture requested on session owner worker")
        self._start_capture_worker()

    def undo_last_shot(self) -> None:
        if not self.shot_paths:
            print("[CAMERA] undo blocked: no shots")
            return

        removed_index = len(self.shot_paths)

        deleted: Optional[Path] = None
        if self.session is not None:
            deleted = self.session.delete_last_shot()
        if deleted is None:
            deleted = self.shot_paths[-1]
            try:
                deleted.unlink(missing_ok=True)
            except OSError:
                pass

        self.shot_paths.pop()
        self._gif_frames_by_shot.pop(removed_index, None)
        self.update()
        print(f"[CAMERA] shot removed path={deleted}")

    def can_go_next(self) -> bool:
        return self.capture_slots > 0 and len(self.shot_paths) >= self.capture_slots

    @staticmethod
    def _design_sort_key(path: Path) -> tuple[int, int, str]:
        stem = path.stem.strip()
        if stem.isdigit():
            return (0, int(stem), path.name.lower())
        match = re.search(r"\d+", stem)
        if match:
            return (1, int(match.group(0)), path.name.lower())
        return (2, 0, path.name.lower())

    def _auto_select_default_design_path(self) -> Optional[Path]:
        if not self.layout_id:
            return None
        frame_dir = (
            ROOT_DIR
            / "assets"
            / "ui"
            / "10_select_Design"
            / "Frame"
            / "Frame2"
            / self.layout_id
        )
        if not frame_dir.is_dir():
            print(f"[CAMERA] design frame dir missing: {frame_dir}")
            return None

        png_files = [p for p in frame_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"]
        if not png_files:
            print(f"[CAMERA] design frame png missing: {frame_dir}")
            return None
        return sorted(png_files, key=self._design_sort_key)[0]

    @staticmethod
    def _fit_cover_image(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
        if target_w <= 0 or target_h <= 0:
            return image.copy()
        src = image.convert("RGB")
        scale = max(target_w / src.width, target_h / src.height)
        resized_w = max(1, int(round(src.width * scale)))
        resized_h = max(1, int(round(src.height * scale)))
        if hasattr(Image, "Resampling"):
            resized = src.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
        else:
            resized = src.resize((resized_w, resized_h), Image.LANCZOS)
        left = max(0, (resized_w - target_w) // 2)
        top = max(0, (resized_h - target_h) // 2)
        return resized.crop((left, top, left + target_w, top + target_h))

    def _compose_photos_only(self, photos: list[Path]) -> Image.Image:
        canvas = Image.new("RGB", (DESIGN_WIDTH, DESIGN_HEIGHT), (255, 255, 255))
        slots = list(self.slot_rects[: len(photos)])
        if len(slots) < len(photos):
            slots = self._fallback_grid_slots(len(photos))
        for idx, photo_path in enumerate(photos):
            if idx >= len(slots):
                break
            x, y, w, h = slots[idx]
            try:
                with Image.open(photo_path) as source:
                    fitted = self._fit_cover_image(source, w, h)
                canvas.paste(fitted, (x, y))
            except Exception as exc:
                print(f"[CAMERA] photos-only paste failed: {photo_path} ({exc})")
        return canvas

    def handle_next(self) -> Optional[Path]:
        if self._countdown_active:
            print("[CAMERA] next blocked: countdown in progress")
            return None
        if self._shutter_locked:
            print("[CAMERA] next blocked: capture in progress")
            return None

        if self.capture_slots <= 0 and self.layout_id:
            self.capture_slots = CAPTURE_SLOT_OVERRIDE_BY_LAYOUT.get(
                self.layout_id,
                EXPECTED_SLOT_COUNT_BY_LAYOUT.get(self.layout_id, 4),
            )
        current_count = len(self.shot_paths)
        if current_count < self.capture_slots:
            print(f"[CAMERA] next blocked: shots incomplete {current_count}/{self.capture_slots}")
            return None

        if self.layout_id is None:
            print("[CAMERA] next blocked: layout_id missing")
            return None
        if self.session is None:
            print("[CAMERA] next blocked: session missing")
            return None

        photos_for_print = self.print_slots if self.print_slots > 0 else len(self.shot_paths)
        photos = self.shot_paths[:photos_for_print]
        frame_path: Optional[Path] = None
        if self.design_path:
            candidate = Path(self.design_path)
            if candidate.is_file():
                frame_path = candidate
        if frame_path is None:
            auto_frame = self._auto_select_default_design_path()
            if auto_frame is not None:
                frame_path = auto_frame
                self.design_path = str(auto_frame)
                self.main_window.current_design_path = self.design_path
                print(f"[CAMERA] design_path missing -> auto selected: {auto_frame}")

        try:
            if frame_path is not None and frame_path.is_file():
                composed = compose_print(frame_path, photos, self.layout_id)
            else:
                print("[CAMERA] frame unavailable -> compose photos only")
                composed = self._compose_photos_only(photos)
            print_path = self.session.save_print(composed)
        except Exception as exc:
            print(f"[CAMERA] compose failed with frame: {exc} -> fallback photos only")
            try:
                composed = self._compose_photos_only(photos)
                print_path = self.session.save_print(composed)
            except Exception as fallback_exc:
                print(f"[CAMERA] compose fallback failed: {fallback_exc}")
                return None

        print(
            f"[CAMERA] next ok captured={current_count}/{self.capture_slots} "
            f"print_slots={self.print_slots} saved={print_path}"
        )
        return print_path

    def _draw_cover_pixmap(self, painter: QPainter, pixmap: QPixmap, target: QRect) -> None:
        if target.width() <= 0 or target.height() <= 0 or pixmap.isNull():
            return
        scaled = pixmap.scaled(target.size(), KEEP_ASPECT_EXPAND, SMOOTH_TRANSFORM)
        sx = max(0, (scaled.width() - target.width()) // 2)
        sy = max(0, (scaled.height() - target.height()) // 2)
        src = QRect(sx, sy, target.width(), target.height())
        painter.drawPixmap(target, scaled, src)

    def _draw_fit_pixmap(self, painter: QPainter, pixmap: QPixmap) -> None:
        if pixmap.isNull() or self.width() <= 0 or self.height() <= 0:
            return
        scaled = pixmap.scaled(self.size(), KEEP_ASPECT, SMOOTH_TRANSFORM)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

    def _get_liveview_rect(self) -> QRect:
        return self.design_rect_to_widget(self._liveview_design_rect)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        if not self._background.isNull():
            painter.drawPixmap(self.rect(), self._background)

        if self._liveview_pixmap is not None and not self._liveview_pixmap.isNull():
            self._draw_cover_pixmap(painter, self._liveview_pixmap, self._get_liveview_rect())

        if not self.slot_rects:
            return

        for idx, rect in enumerate(self.slot_rects):
            target = self.design_rect_to_widget(rect)

            if idx < len(self.shot_paths):
                shot_pixmap = QPixmap(str(self.shot_paths[idx]))
                if not shot_pixmap.isNull():
                    self._draw_cover_pixmap(painter, shot_pixmap, target)


class UiSoundManager(QObject):
    AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".m4a"}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.enabled = True
        self._sound_paths: dict[str, Path] = {}
        self._effects: dict[str, Any] = {}
        self._fallback_paths: dict[str, Path] = {}
        self._load_sound_library()

    def _sound_dirs(self) -> list[Path]:
        return [
            ROOT_DIR / "assets" / "sounds",
            ROOT_DIR / "assets" / "sound",
            ROOT_DIR / "assets" / "audio",
            ROOT_DIR / "assets" / "ui" / "sounds",
            ROOT_DIR / "assets" / "ui",
            ROOT_DIR / "assets",
        ]

    @classmethod
    def _is_audio_file(cls, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in cls.AUDIO_EXTS

    def _find_by_tokens(self, files: list[Path], tokens: list[str]) -> Optional[Path]:
        for token in tokens:
            token_lower = token.lower()
            for path in files:
                if token_lower in path.stem.lower():
                    return path
        return None

    def _load_sound_library(self) -> None:
        discovered: list[Path] = []
        for directory in self._sound_dirs():
            if not directory.is_dir():
                continue
            for path in directory.rglob("*"):
                if self._is_audio_file(path):
                    discovered.append(path)

        if not discovered:
            print("[SOUND] no audio files found (assets/sounds|sound|audio)")
            return

        discovered = sorted(set(discovered), key=lambda p: p.name.lower())
        click_path = self._find_by_tokens(discovered, ["click", "tap", "button", "touch", "select"])
        nav_path = self._find_by_tokens(discovered, ["page", "screen", "transition", "nav", "next", "move", "loading"])
        if click_path is None:
            click_path = self._find_by_tokens(discovered, ["btn", "select"])
        if nav_path is None:
            nav_path = self._find_by_tokens(discovered, ["loading", "page"])

        fallback = discovered[0]
        self._sound_paths["click"] = click_path or fallback
        self._sound_paths["nav"] = nav_path or fallback
        self._fallback_paths = dict(self._sound_paths)

        print(
            "[SOUND] loaded click="
            f"{self._sound_paths['click'].name} nav={self._sound_paths['nav'].name} "
            f"count={len(discovered)}"
        )

        if QSoundEffect is None:
            print("[SOUND] QtMultimedia unavailable; using winsound fallback if possible")
            return

        for key, path in self._sound_paths.items():
            try:
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setLoopCount(1)
                effect.setVolume(0.85)
                self._effects[key] = effect
            except Exception as exc:
                print(f"[SOUND] effect init failed key={key} path={path} err={exc}")

    def play(self, key: str) -> None:
        if not self.enabled:
            return
        effect = self._effects.get(key)
        if effect is not None:
            try:
                effect.stop()
                effect.play()
                return
            except Exception:
                pass

        # Fallback for environments where QtMultimedia backend is unavailable.
        if winsound is not None:
            path = self._fallback_paths.get(key)
            if path is not None and path.is_file() and path.suffix.lower() == ".wav":
                try:
                    winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                except Exception:
                    pass


class OfflineLockScreen(QWidget):
    screen_name = "offline_locked"

    def __init__(self, main_window: "KioskMainWindow") -> None:
        super().__init__(main_window)
        self.main_window = main_window
        self.setStyleSheet("QWidget { background: #0b1020; color: white; }")

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(160, 120, 160, 120)
        self._root_layout.setSpacing(20)

        self._title = QLabel("서비스 잠금\nService Locked", self)
        self._title.setAlignment(ALIGN_CENTER)
        self._title.setStyleSheet("font-size: 54px; font-weight: 800;")

        self._subtitle = QLabel(
            "인터넷 미연결 허용시간(72시간)을 초과했습니다.\n"
            "Offline grace period (72 hours) has expired.",
            self,
        )
        self._subtitle.setAlignment(ALIGN_CENTER)
        self._subtitle.setStyleSheet("font-size: 28px; color: #d6ddf5;")

        self._detail = QLabel("", self)
        self._detail.setAlignment(ALIGN_CENTER)
        self._detail.setWordWrap(True)
        self._detail.setStyleSheet(
            "font-size: 24px; color: #a6b3db; background: rgba(255,255,255,0.08); "
            "border: 1px solid rgba(255,255,255,0.18); border-radius: 12px; padding: 12px 18px;"
        )

        self._retry_button = QPushButton("재시도 / Retry", self)
        self._retry_button.setMinimumHeight(74)
        self._retry_button.setStyleSheet(
            "QPushButton { background: #1f7ae0; color: white; font-size: 30px; font-weight: 700; "
            "border-radius: 12px; padding: 8px 24px; } "
            "QPushButton:pressed { background: #1565c0; }"
        )
        self._retry_button.clicked.connect(self._on_retry_clicked)

        self._hint = QLabel(
            "인터넷 연결 복구 후 재시도를 누르세요.\n"
            "Restore internet connection, then tap Retry.",
            self,
        )
        self._hint.setAlignment(ALIGN_CENTER)
        self._hint.setStyleSheet("font-size: 22px; color: #c4cde9;")

        self._root_layout.addStretch(1)
        self._root_layout.addWidget(self._title)
        self._root_layout.addWidget(self._subtitle)
        self._root_layout.addWidget(self._detail)
        self._root_layout.addWidget(self._retry_button)
        self._root_layout.addWidget(self._hint)
        self._root_layout.addStretch(1)

    def set_lock_message(self, message: str) -> None:
        self._detail.setText(str(message or "").strip())

    def set_hotspots(self, hotspots: list[Hotspot]) -> None:
        _ = hotspots

    def set_overlay_visible(self, visible: bool) -> None:
        _ = visible

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if hasattr(self.main_window, "_current_runtime_lock_message"):
            try:
                self.set_lock_message(str(self.main_window._current_runtime_lock_message()))
                return
            except Exception:
                pass
        if hasattr(self.main_window, "_offline_lock_message"):
            self.set_lock_message(str(getattr(self.main_window, "_offline_lock_message", "")))

    def _on_retry_clicked(self) -> None:
        if hasattr(self.main_window, "retry_offline_unlock"):
            self.main_window.retry_offline_unlock()


class KioskMainWindow(QMainWindow):
    offline_guard_signal = Signal(str)
    server_lock_signal = Signal(object)
    server_mode_permissions_signal = Signal(object)
    ota_state_signal = Signal(object)
    FRAME_SELECT_MODE_RECTS: dict[str, tuple[int, int, int, int]] = {
        "celebrity": (260, 820, 620, 86),
        "ai": (1040, 820, 620, 86),
    }
    # Price label Y positions for frame cards (design coordinate, 1920x1080).
    # Used as fallback only when frame-bound detection is unavailable.
    FRAME_SELECT_PRICE_Y_BY_LAYOUT: dict[str, int] = {
        "2641": 613,
        "6241": 503,
        "4641": 613,
        "4661": 613,
        "4681": 614,
    }
    FRAME_SELECT_PRICE_X_OFFSET_BY_LAYOUT: dict[str, int] = {
        # Fine-tune after frame-center anchoring.
        "4641": 44,
        "4661": 44,
    }
    FRAME_SELECT_PRICE_Y_OFFSET_BY_LAYOUT: dict[str, int] = {
        "4641": 0,
        "4661": 0,
        "4681": 0,
    }
    FRAME_SELECT_BG_PATH = ROOT_DIR / "assets" / "ui" / "3_select_a_frame" / "please_select_a_frame.png"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Viorafilm Kiosk")
        self.resize(DESIGN_WIDTH, DESIGN_HEIGHT)

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.config_path = _resolve_runtime_config_path()
        self.hotspots_path = ROOT_DIR / "assets" / "hotspots.json"
        self.hotspot_map: Dict[str, list[Hotspot]] = {}
        self.available_layout_ids: list[str] = self._detect_layout_ids_from_hotspots_file()
        self.share_settings = self._resolve_share_settings()
        self._device_registration_required = self._env_bool(os.environ.get("KIOSK_REQUIRE_DEVICE_AUTH", "1"), True)
        if self._device_registration_required:
            self._ensure_device_registration_or_raise()
        self.payment_pricing_settings = self._resolve_payment_pricing_settings()
        self.printing_settings = self._resolve_printing_settings()
        self.coupon_value_settings = self._resolve_coupon_value_settings()
        self.bill_acceptor_settings = self._resolve_bill_acceptor_settings()
        self.bill_worker: Optional[BillAcceptorWorker] = None
        self.current_bill_total_amount: int = 0
        self.coupon_settings = self._resolve_coupon_settings()
        self.gif_settings = self._resolve_gif_settings()
        self.thank_you_settings = self._resolve_thank_you_settings()
        self.payment_methods = self._resolve_payment_methods()
        self.mode_settings = self._resolve_modes_settings()
        self._base_mode_settings = dict(self.mode_settings)
        self.ai_style_settings = self._resolve_ai_styles_settings()
        self._apply_ai_style_settings(self.ai_style_settings, emit_log=False)
        self.celebrity_settings = self._resolve_celebrity_settings()
        self.layout_settings = self._resolve_layout_settings()

        self.show_hotspot_overlay = False
        self.log_click_coords = False
        self.record_mode = False
        self.record_start: Optional[tuple[int, int]] = None
        self.current_layout_id: Optional[str] = None
        self.current_design_index: Optional[int] = None
        self.current_design_path: Optional[str] = None
        self.current_design_is_gray: bool = False
        self.current_design_flip_horizontal: bool = False
        self.current_design_qr_enabled: bool = True
        self.current_print_path: Optional[str] = None
        self.current_print_job_path: Optional[str] = None
        self.current_print_job_copies: int = 2
        self.current_print_job_size: str = "4x6"
        self.current_print_job_mode: str = "full"
        self.current_captured_paths: list[str] = []
        self.current_capture_slots: int = 0
        self.current_print_slots: int = 0
        self.selected_print_paths: list[str] = []
        self.print_slots: int = 0
        self.print_count: int = 2
        self.current_print_count: int = 2
        self.current_payment_method: Optional[str] = None
        self.current_coupon_code: Optional[str] = None
        self.current_coupon_value: int = 0
        self.current_required_amount: int = 0
        self.current_inserted_amount: int = 0
        self.current_remaining_amount: int = 0
        self.compose_mode: str = "normal"
        self.celebrity_template_dir: Optional[str] = None
        self.celebrity_template_name: Optional[str] = None
        self.ai_style_id: Optional[str] = None
        self.ai_selected_source_paths: list[str] = []
        self.pending_coupon_code: Optional[str] = None
        self.print_thread: Optional[QThread] = None
        self.print_worker = None
        self.boot_check_done: bool = False
        self._boot_checked: bool = False
        self.prepared_select_photo: dict = {}
        self._select_photo_preload_worker: Optional[PreloadSelectPhotoWorker] = None
        self._after_loading_started_at: float = 0.0
        self._after_loading_token: int = 0
        self._after_loading_handled_token: int = -1
        self._after_loading_progress_percent: int = -1
        self.design_key_buffer = ""
        self.design_key_timer = QTimer(self)
        self.design_key_timer.setSingleShot(True)
        self.design_key_timer.timeout.connect(self.flush_design_key_buffer)
        self.admin_settings = self._resolve_admin_settings()
        self._admin_return_screen = "start"
        self._start_admin_tap_count = 0
        self._start_admin_tap_timer = QTimer(self)
        self._start_admin_tap_timer.setSingleShot(True)
        self._start_admin_tap_timer.timeout.connect(self._reset_start_admin_taps)
        self.session = None
        self.layout_id = None
        self.captured_paths = []
        self.payment_method = None
        self.design_index = 1
        self.design_path = None
        self.qr_enabled = True
        self.coupon_code = None
        self.coupon_value = 0
        self._frame_select_price_labels: dict[str, QLabel] = {}
        self._frame_select_mode_buttons: dict[str, QPushButton] = {}
        self._frame_select_mode_price_labels: dict[str, QLabel] = {}
        self._last_ai_runtime_ready: Optional[bool] = None
        self.ui_sound = UiSoundManager(self)
        self._suppress_nav_sound_until: float = 0.0
        self._runtime_out_dir = _resolve_runtime_out_dir()
        self._runtime_sessions_dir = _resolve_runtime_sessions_dir()
        self._ensure_runtime_dirs()
        self._apply_startup_runtime_defaults()
        try:
            print(
                "[BOOT] runtime config "
                f"path={self.config_path} "
                f"preferred={1 if self._is_preferred_runtime_config_path(self.config_path) else 0}"
            )
        except Exception:
            pass
        self._license_state_lock = threading.Lock()
        self._license_state_path = self._runtime_out_dir / "license_state.json"
        self._first_seen_ts = 0.0
        self._last_online_ts = 0.0
        self._offline_lock_active = False
        self._offline_lock_message = ""
        self._server_lock_active = False
        self._server_lock_message = ""
        self._ota_force_lock_active = False
        self._ota_force_lock_message = ""
        self._ota_target_version = ""
        self._ota_check_inflight = False
        self._ota_last_state_signature = ""
        self._ota_auto_download_enabled = self._env_bool(os.environ.get("KIOSK_OTA_AUTO_DOWNLOAD", "0"), False)
        self._ota_auto_apply_enabled = self._env_bool(os.environ.get("KIOSK_OTA_AUTO_APPLY", "0"), False)
        self._ota_auto_restart_enabled = self._env_bool(os.environ.get("KIOSK_OTA_AUTO_RESTART", "0"), False)
        self._ota_restart_scheduled = False
        try:
            restart_delay = float(str(os.environ.get("KIOSK_OTA_RESTART_DELAY_SEC", "8")).strip())
        except Exception:
            restart_delay = 8.0
        self._ota_restart_delay_sec = max(2.0, min(60.0, restart_delay))
        self._ota_apply_cmd_template = str(os.environ.get("KIOSK_OTA_APPLY_CMD", "")).strip()
        self._ota_download_dir = self._resolve_ota_download_dir()
        self._ota_state_path = self._resolve_ota_state_path()
        self._kiosk_app_version = self._load_kiosk_app_version()
        self._ota_download_lock = threading.Lock()
        self._ota_download_inflight = False
        self._ota_last_download_signature = ""
        self._ota_last_downloaded_path = ""
        self._ota_last_download_error = ""
        self._offline_guard_enabled = True
        self._offline_grace_seconds = int(DEFAULT_OFFLINE_GRACE_HOURS * 3600)
        self._reported_sale_sessions: set[str] = set()
        self._sale_report_lock = threading.Lock()
        self._heartbeat_lock = threading.Lock()
        self._heartbeat_inflight = False
        self._offline_queue_lock = threading.Lock()
        self._offline_flush_lock = threading.Lock()
        self._offline_flush_inflight = False
        self._offline_queue_path = self._runtime_out_dir / "offline_events_queue.json"
        self._film_state_lock = threading.Lock()
        self._film_state_path = self._runtime_out_dir / "film_remaining_state.json"
        self._film_remaining_by_model: dict[str, int] = {}
        self._active_print_context: dict[str, Any] = {}
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.setInterval(30000)
        self._heartbeat_timer.timeout.connect(self._heartbeat_tick)
        self._server_lock_probe_lock = threading.Lock()
        self._server_lock_probe_inflight = False
        self._server_lock_probe_last_error = ""
        self._server_lock_probe_last_error_ts = 0.0
        self._server_lock_probe_timer = QTimer(self)
        lock_poll_ms = 1000
        try:
            lock_poll_ms = int(float(os.environ.get("KIOSK_SERVER_LOCK_POLL_MS", "1000")))
        except Exception:
            lock_poll_ms = 1000
        self._server_lock_probe_timer.setInterval(max(500, min(10000, lock_poll_ms)))
        self._server_lock_probe_timer.timeout.connect(self._server_lock_probe_tick)
        self._ota_check_timer = QTimer(self)
        ota_poll_ms = 300000
        try:
            ota_poll_ms = int(float(os.environ.get("KIOSK_OTA_CHECK_MS", "300000")))
        except Exception:
            ota_poll_ms = 300000
        self._ota_check_timer.setInterval(max(30000, min(3600000, ota_poll_ms)))
        self._ota_check_timer.timeout.connect(self._ota_check_tick)
        self._payment_complete_watchdog_timer = QTimer(self)
        self._payment_complete_watchdog_timer.setSingleShot(True)
        self._payment_complete_watchdog_timer.timeout.connect(self._payment_complete_watchdog_tick)
        self.offline_guard_signal.connect(self._enforce_offline_runtime_guard)
        self.server_lock_signal.connect(self._on_server_lock_signal)
        self.server_mode_permissions_signal.connect(self._on_server_mode_permissions_signal)
        self.ota_state_signal.connect(self._on_ota_state_signal)

        after_camera_loading_screen = LoadingScreen(self)
        after_camera_loading_screen.screen_name = "after_camera_loading"

        self.screens: Dict[str, QWidget] = {
            "boot_healthcheck": BootHealthCheckScreen(self),
            "start": ImageScreen(
                self,
                "start",
                ROOT_DIR / "assets" / "ui" / "2_Start" / "start_1.png",
            ),
            "frame_select": ImageScreen(
                self,
                "frame_select",
                ROOT_DIR
                / "assets"
                / "ui"
                / "3_select_a_frame"
                / "please_select_a_frame.png",
            ),
            "celebrity_template_select": CelebrityTemplateSelectScreen(self),
            "ai_style_select": AiStyleSelectScreen(self),
            "how_many_prints": AppHowManyPrintsScreen(self),
            "payment_method": AppPaymentMethodScreen(self),
            "pay_cash": PayCashScreen(self),
            "coupon_input": CouponInputScreen(self),
            "coupon_remaining_method": CouponRemainingMethodScreen(self),
            "pay_cash_remaining": PayCashRemainingScreen(self),
            "payment_complete_success": AppPaymentCompleteSuccessScreen(self),
            "payment_complete_failed": PaymentCompleteScreen(
                self, "payment_complete_failed", success=False
            ),
            "camera": CameraScreen(
                self,
                self._resolve_canon_edsdk_dll_path(),
                self._resolve_camera_backend(),
            ),
            "select_photo": SelectPhotoScreen(self),
            "select_design": SelectDesignScreen(self),
            "admin": AdminScreen(self),
            "preview": PreviewScreen(self),
            "after_camera_loading": after_camera_loading_screen,
            "loading": LoadingScreen(self),
            "qr_generating": AppQrGeneratingScreen(self),
            "qr_code": AppQrCodeScreen(self),
            "thank_you": AppThankYouScreen(
                self,
                ROOT_DIR / "assets" / "ui" / "12_Thank_you" / "Lastpage.png",
                gif_rect=self.get_thank_you_gif_rect(),
            ),
            "error": StaticImageScreen(
                self,
                "error",
                ROOT_DIR / "assets" / "ui" / "errorpage" / "error.png",
                missing_text="Error",
            ),
            "offline_locked": OfflineLockScreen(self),
        }

        for screen in self.screens.values():
            self.stack.addWidget(screen)

        self.reload_hotspots()
        self._sync_pricing_layout_defaults(persist=True)
        self._apply_admin_settings(self.admin_settings, emit_log=False)
        self._apply_payment_methods(self.payment_methods, emit_log=False)
        self._apply_mode_settings(self.mode_settings, emit_log=False)
        self._apply_ai_style_settings(self.ai_style_settings, emit_log=False)
        self._init_offline_license_state()
        self._init_film_remaining_state()
        pending_events = self._offline_queue_count()
        if pending_events > 0:
            print(f"[QUEUE] pending events loaded={pending_events}")
        self._heartbeat_timer.start()
        self._server_lock_probe_timer.start()
        self._ota_check_timer.start()
        QTimer.singleShot(2500, self._heartbeat_tick)
        QTimer.singleShot(1000, self._server_lock_probe_tick)
        QTimer.singleShot(4000, self._ota_check_tick)
        if self._is_runtime_locked():
            self.goto_screen("offline_locked")
        else:
            self.goto_screen("boot_healthcheck")

    def _ensure_runtime_dirs(self) -> None:
        for preferred_root in _preferred_runtime_data_dirs():
            preferred_root = Path(preferred_root)
            for path in (
                preferred_root,
                preferred_root / "config",
                preferred_root / "out",
                preferred_root / "sessions",
                preferred_root / "logs",
            ):
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as exc:
                    _safe_boot_write(f"[BOOT] preferred runtime dir prepare failed: {path} ({exc})\n")
            try:
                out_ok = _is_directory_writable(preferred_root / "out")
                sessions_ok = _is_directory_writable(preferred_root / "sessions")
                print(
                    f"[BOOT] runtime preferred root={preferred_root} "
                    f"writable_out={1 if out_ok else 0} writable_sessions={1 if sessions_ok else 0}"
                )
            except Exception:
                pass

        candidates = [
            _default_runtime_data_dir(),
            Path(self._runtime_out_dir),
            Path(self._runtime_sessions_dir),
        ]
        for path in candidates:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                _safe_boot_write(f"[BOOT] runtime dir prepare failed: {path} ({exc})\n")
        out_dir = Path(self._runtime_out_dir)
        sessions_dir = Path(self._runtime_sessions_dir)
        if not _is_directory_writable(out_dir) or not _is_directory_writable(sessions_dir):
            self._switch_runtime_storage_to_fallback("dir_not_writable")
        try:
            print(
                "[BOOT] runtime dirs "
                f"data={_default_runtime_data_dir()} "
                f"out={self._runtime_out_dir} "
                f"sessions={self._runtime_sessions_dir}"
            )
        except Exception:
            pass

    def _switch_runtime_storage_to_fallback(self, reason: str) -> None:
        current_root: Optional[Path] = None
        try:
            current_root = Path(self._runtime_out_dir).parent.resolve(strict=False)
        except Exception:
            current_root = None

        fallback_data = _default_runtime_data_dir()
        for candidate in _iter_runtime_data_dir_candidates():
            try:
                resolved_candidate = candidate.resolve(strict=False)
            except Exception:
                resolved_candidate = candidate
            if (
                current_root is not None
                and str(resolved_candidate).strip().lower() == str(current_root).strip().lower()
            ):
                continue
            candidate_out = candidate / "out"
            candidate_sessions = candidate / "sessions"
            try:
                candidate_out.mkdir(parents=True, exist_ok=True)
                candidate_sessions.mkdir(parents=True, exist_ok=True)
                probe_path = candidate_out / f".vf_runtime_switch_probe_{os.getpid()}.json"
                _write_json_atomic(
                    probe_path,
                    {
                        "reason": str(reason or ""),
                        "ts": time.time(),
                    },
                )
                try:
                    probe_path.unlink(missing_ok=True)
                except Exception:
                    pass
                fallback_data = candidate
                break
            except Exception:
                continue
        fallback_out = fallback_data / "out"
        fallback_sessions = fallback_data / "sessions"
        for path in [fallback_data, fallback_out, fallback_sessions]:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        self._runtime_out_dir = fallback_out
        self._runtime_sessions_dir = fallback_sessions
        self._license_state_path = fallback_out / "license_state.json"
        self._offline_queue_path = fallback_out / "offline_events_queue.json"
        self._film_state_path = fallback_out / "film_remaining_state.json"
        self._ota_download_dir = fallback_out / "updates"
        self._ota_state_path = fallback_out / "ota_state.json"
        camera_screen = self.screens.get("camera")
        if isinstance(camera_screen, CameraScreen):
            camera_screen._runtime_sessions_dir = Path(self._runtime_sessions_dir)
        _safe_boot_write(
            "[BOOT] runtime storage switched to fallback "
            f"reason={reason} data={fallback_data}\n"
        )
        try:
            print(
                f"[BOOT] runtime fallback reason={reason} "
                f"out={self._runtime_out_dir} sessions={self._runtime_sessions_dir}"
            )
        except Exception:
            pass

    def _start_payment_complete_transition_watchdog(self) -> None:
        try:
            if self._payment_complete_watchdog_timer.isActive():
                self._payment_complete_watchdog_timer.stop()
            self._payment_complete_watchdog_timer.start(int(AppPaymentCompleteSuccessScreen.AUTO_MS) + 2200)
        except Exception:
            pass

    def _stop_payment_complete_transition_watchdog(self) -> None:
        try:
            if self._payment_complete_watchdog_timer.isActive():
                self._payment_complete_watchdog_timer.stop()
        except Exception:
            pass

    def _payment_complete_watchdog_tick(self) -> None:
        try:
            current = self.stack.currentWidget()
            if getattr(current, "screen_name", None) != "payment_complete_success":
                return
            print("[PAYMENT_COMPLETE] watchdog fired -> retry camera transition")
            self.handle_payment_complete_success()
        except Exception as exc:
            print(f"[PAYMENT_COMPLETE] watchdog failed: {exc}")

    def goto_screen(self, screen_name: str) -> None:
        if screen_name == "boot_healthcheck" and (
            self.boot_check_done or self._boot_checked
        ):
            screen_name = "start"
        if self._is_runtime_locked() and screen_name not in {"offline_locked", "admin"}:
            screen_name = "offline_locked"
        target = self.screens.get(screen_name)
        if not target:
            print(f"[NAV] Unknown screen: {screen_name}")
            return
        if screen_name != "payment_complete_success":
            self._stop_payment_complete_transition_watchdog()
        current_widget = self.stack.currentWidget()
        current_screen_name = getattr(current_widget, "screen_name", None)
        should_play_nav_sound = bool(
            isinstance(current_screen_name, str)
            and current_screen_name
            and current_screen_name != screen_name
        )
        if time.monotonic() < float(self._suppress_nav_sound_until):
            should_play_nav_sound = False
        if (
            isinstance(current_screen_name, str)
            and current_screen_name in {"pay_cash", "pay_cash_remaining"}
            and current_screen_name != screen_name
        ):
            self.stop_bill_acceptor_test(wait_ms=3000)
        if screen_name == "start":
            self.reset_state()
        elif screen_name == "how_many_prints":
            self.current_print_count = 2
            self.print_count = 2
            how_many_screen = self.screens.get("how_many_prints")
            if isinstance(how_many_screen, AppHowManyPrintsScreen):
                how_many_screen.set_print_count(2)
            print("[PRINT_COUNT] init=2")
        elif screen_name == "payment_method":
            payment_screen = self.screens.get("payment_method")
            if isinstance(payment_screen, AppPaymentMethodScreen):
                enabled = self.get_payment_methods()
                single_method = self._single_enabled_payment_method(enabled)
                payment_screen.apply_payment_methods(enabled)
                self._apply_payment_hotspot_overrides()
                payment_screen.set_default_method()
                self.current_payment_method = payment_screen.payment_method
                self.payment_method = self.current_payment_method
                main_asset = payment_screen.get_main_asset_path()
                print(
                    "[PAYMENT] enabled "
                    f"cash={1 if enabled.get('cash') else 0} "
                    f"card={1 if enabled.get('card') else 0} "
                    f"coupon={1 if enabled.get('coupon') else 0} "
                    f"mode={payment_screen.get_payment_mode()} asset={main_asset}"
                )
                if self.current_required_amount <= 0:
                    self._refresh_required_amount()
                if single_method:
                    print(f"[PAYMENT] single enabled method={single_method} -> skip payment_method")
                    if self._enter_single_payment_flow(single_method):
                        return
            else:
                self.current_payment_method = "cash"
                self.payment_method = self.current_payment_method
                print("[PAYMENT] method=cash (default)")
        elif screen_name == "pay_cash":
            self._enter_pay_cash_screen()
        elif screen_name == "coupon_remaining_method":
            self._enter_coupon_remaining_method_screen()
        elif screen_name == "pay_cash_remaining":
            self._enter_pay_cash_remaining_screen()
        elif screen_name == "select_photo":
            self._prepare_select_photo_screen()
        elif screen_name == "select_design":
            self._prepare_select_design_screen()
            print(
                f"[SELECT_DESIGN] enter layout={self.current_layout_id} "
                f"selected={len(self.selected_print_paths)} "
                f"frame={self.current_design_index or 1} "
                f"gray={1 if self.current_design_is_gray else 0} "
                f"flip={1 if self.current_design_flip_horizontal else 0} "
                f"qr={1 if self.current_design_qr_enabled else 0}"
            )
        elif screen_name == "admin":
            self._prepare_admin_screen()
        self.stack.setCurrentWidget(target)
        if should_play_nav_sound:
            self.ui_sound.play("nav")
        if screen_name == "frame_select":
            self._ensure_frame_select_mode_buttons()
            self._refresh_frame_select_mode_buttons()
            self._refresh_frame_select_price_labels()
        if screen_name == "camera":
            print(
                f"[CAMERA] enter layout_id={self.current_layout_id} "
                f"design_path={self.current_design_path}"
            )
        elif screen_name == "payment_complete_success":
            self._start_payment_complete_transition_watchdog()
        print(f"[NAV] {screen_name}")

    def complete_boot_healthcheck(self, force: bool = False) -> None:
        if self._is_runtime_locked():
            print("[LICENSE] boot start blocked: runtime lock active")
            self.goto_screen("offline_locked")
            return
        if not force:
            print("[HEALTH] boot check passed -> start")
        else:
            print("[HEALTH] boot check forced -> start")
        self.boot_check_done = True
        self._boot_checked = True
        self.goto_screen("start")

    def reset_state(self) -> None:
        self._stop_select_photo_preload_worker(wait=False)
        self._stop_bill_acceptor_for_payment()
        self._reset_start_admin_taps()
        self._start_admin_tap_timer.stop()
        self.current_layout_id = None
        self.current_design_index = None
        self.current_design_path = None
        self.current_design_is_gray = False
        self.current_design_flip_horizontal = False
        self.current_design_qr_enabled = True
        self.current_print_path = None
        self.current_print_job_path = None
        self.current_print_job_copies = 2
        self.current_print_job_size = "4x6"
        self.current_print_job_mode = "full"
        self.prepared_select_photo = {}
        self._after_loading_started_at = 0.0
        self._after_loading_token = 0
        self._after_loading_handled_token = -1
        self.current_captured_paths = []
        self.current_capture_slots = 0
        self.current_print_slots = 0
        self.selected_print_paths = []
        self.print_slots = 0
        self.print_count = 2
        self.current_print_count = 2
        self.current_payment_method = None
        self.current_coupon_code = None
        self.current_coupon_value = 0
        self.current_required_amount = 0
        self.current_inserted_amount = 0
        self.current_remaining_amount = 0
        self.compose_mode = "normal"
        self.celebrity_template_dir = None
        self.celebrity_template_name = None
        self.ai_style_id = None
        self.ai_selected_source_paths = []
        self.pending_coupon_code = None
        self.current_bill_total_amount = 0
        self.design_key_buffer = ""
        self.design_key_timer.stop()

        select_photo_screen = self.screens.get("select_photo")
        if isinstance(select_photo_screen, SelectPhotoScreen):
            select_photo_screen.set_context(None, [], 0)

        preview_screen = self.screens.get("preview")
        if isinstance(preview_screen, PreviewScreen):
            preview_screen.set_confirm_locked(False)
            preview_screen.set_print_image(None)
            preview_screen.set_layout(None)

        thank_you_screen = self.screens.get("thank_you")
        if isinstance(thank_you_screen, ThankYouScreen):
            thank_you_screen.set_qr_path(None)

        camera_screen = self.screens.get("camera")
        if isinstance(camera_screen, CameraScreen):
            camera_screen.cancel_countdown()
            camera_screen.reset_gif_capture_state()
            camera_screen._auto_next_pending = False
            camera_screen._capture_pending_after_liveview_stop = False
            camera_screen._stop_capture_worker(wait=False)
            camera_screen._stop_liveview_worker(wait=False)
            camera_screen._capture_target_index = None
            camera_screen._capture_target_path = None
            camera_screen._shutter_locked = False
            camera_screen.layout_id = None
            camera_screen.design_index = None
            camera_screen.design_path = None
            camera_screen.print_slots = 0
            camera_screen.capture_slots = 0
            camera_screen.slot_rects = []
            camera_screen.shot_paths = []
            camera_screen.session = None
            camera_screen._liveview_pixmap = None
            camera_screen.update()

        if self.print_thread is not None and self.print_thread.isRunning():
            try:
                self.print_thread.quit()
                self.print_thread.wait(300)
            except Exception:
                pass
        self.print_worker = None
        self.print_thread = None

        # Compatibility aliases for simpler state access in flows/tools.
        self.session = None
        self.layout_id = None
        self.captured_paths = []
        self.payment_method = None
        self.design_index = 1
        self.design_path = None
        self.qr_enabled = True
        self.coupon_code = None
        self.coupon_value = 0
        self.compose_mode = "normal"
        self.celebrity_template_dir = None
        self.celebrity_template_name = None
        self.ai_style_id = None
        self.pending_coupon_code = None
        print("[STATE] reset ok")

    def get_active_session(self) -> Optional[Session]:
        camera_screen = self.screens.get("camera")
        if isinstance(camera_screen, CameraScreen):
            return camera_screen.session
        return None

    def _prepare_camera_entry(self, skip_health_check: bool = False) -> bool:
        if not self.current_layout_id:
            print("[CAMERA] enter blocked: layout_id missing")
            return False
        camera_screen = self.screens.get("camera")
        if not isinstance(camera_screen, CameraScreen):
            print("[CAMERA] enter blocked: camera screen missing")
            return False
        if self.is_ai_mode_active() and not self._is_ai_mode_runtime_ready(
            stage="camera_entry",
            probe_once=True,
        ):
            self._block_ai_mode_missing_key(
                stage="camera_entry",
                notice="AI 서버 키가 없어 촬영을 시작할 수 없습니다",
            )
            return False
        requested_backend = self._resolve_requested_camera_backend()
        effective_backend = requested_backend
        if requested_backend == "dummy" and not self.is_test_mode():
            # Do not allow dummy backend in operation mode.
            print("[CAMERA] dummy backend blocked: test_mode required -> auto")
            requested_backend = "auto"
            effective_backend = "auto"
        if not skip_health_check:
            health_ok, health_msg = self.check_runtime_camera_health(requested_backend)
            if not health_ok:
                allow_dummy = bool(self.allow_dummy_when_camera_fail())
                if requested_backend in {"auto", "edsdk"} and allow_dummy:
                    effective_backend = "dummy"
                    print(f"[CAMERA] health failed -> fallback dummy ({health_msg})")
                    self._show_runtime_notice("카메라 연결 실패: 테스트 더미 모드로 진행합니다", duration_ms=1200)
                else:
                    print(f"[CAMERA] enter blocked: {health_msg}")
                    self._show_runtime_notice("카메라 연결 실패", duration_ms=1200)
                    return False
        camera_screen.camera_backend = effective_backend
        camera_screen.set_layout(self.current_layout_id)
        camera_screen.set_design(
            self.current_design_index,
            self.current_design_path,
        )
        camera_screen._runtime_sessions_dir = Path(self._runtime_sessions_dir)
        try:
            camera_screen.start_session(
                self.current_layout_id,
                self.current_design_path,
            )
        except Exception as exc:
            print(f"[CAMERA] start_session failed: {exc}")
            try:
                self._switch_runtime_storage_to_fallback(f"camera_start_session_failed:{exc}")
                camera_screen._runtime_sessions_dir = Path(self._runtime_sessions_dir)
                camera_screen.start_session(
                    self.current_layout_id,
                    self.current_design_path,
                )
            except Exception as fallback_exc:
                print(f"[CAMERA] start_session fallback failed: {fallback_exc}")
                self._show_runtime_notice("카메라 세션 시작 실패", duration_ms=1200)
                return False
        if camera_screen.session is not None:
            camera_screen.session.print_count = int(self.current_print_count or self.print_count or 2)
            setattr(camera_screen.session, "payment_method", self.current_payment_method)
            coupon_code = self.pending_coupon_code or self.current_coupon_code
            if coupon_code:
                setattr(camera_screen.session, "coupon_code", coupon_code)
            setattr(camera_screen.session, "coupon_value", int(self.current_coupon_value))
            setattr(camera_screen.session, "payment_required", int(self.current_required_amount))
            setattr(camera_screen.session, "payment_inserted", int(self.current_inserted_amount))
            setattr(camera_screen.session, "payment_remaining", int(self.current_remaining_amount))
            setattr(camera_screen.session, "compose_mode", str(self.compose_mode or "normal"))
            setattr(camera_screen.session, "celebrity_template_dir", self.celebrity_template_dir)
            setattr(camera_screen.session, "celebrity_template_name", self.celebrity_template_name)
            setattr(camera_screen.session, "ai_style_id", self.ai_style_id)
            print(
                "[SESSION] payment_method="
                f"{self.current_payment_method} coupon_code={coupon_code} "
                f"coupon_value={self.current_coupon_value} "
                f"required={self.current_required_amount} remaining={self.current_remaining_amount}"
            )
        return True

    def _prepare_select_photo_screen(self) -> None:
        screen = self.screens.get("select_photo")
        if isinstance(screen, SelectPhotoScreen):
            captured_for_screen = list(self.current_captured_paths or [])
            if self.is_ai_mode_active():
                ai_candidate_raw = self.prepared_select_photo.get("ai_candidate_paths", [])
                ai_candidates: list[str] = []
                if isinstance(ai_candidate_raw, list):
                    for item in ai_candidate_raw:
                        if isinstance(item, str) and item.strip() and Path(item).is_file():
                            ai_candidates.append(item)
                print(
                    f"[AI_MODE] select_photo source=original count={len(captured_for_screen)} "
                    f"ai_candidates={len(ai_candidates)}"
                )
            screen.set_context(
                self.current_layout_id,
                captured_for_screen,
                self.current_print_slots,
                prepared=self.prepared_select_photo,
            )

    def _prepare_ai_selected_paths_from_captures(
        self,
        preferred_paths: Optional[list[Path]] = None,
        preferred_source_paths: Optional[list[Path]] = None,
    ) -> bool:
        selected_ai: list[Path] = []
        if isinstance(preferred_paths, list):
            for path in preferred_paths:
                if isinstance(path, Path) and path.is_file():
                    selected_ai.append(path)
                if len(selected_ai) >= AI_SELECT_SLOTS:
                    break
        if len(selected_ai) < AI_SELECT_SLOTS:
            raw_paths = list(self.selected_print_paths or [])
            for raw in raw_paths:
                path = Path(raw)
                if path.is_file():
                    selected_ai.append(path)
                if len(selected_ai) >= AI_SELECT_SLOTS:
                    break
        if len(selected_ai) < AI_SELECT_SLOTS:
            print("[AI_MODE] selection blocked: not enough selected ai shots")
            return False

        selected_ai = selected_ai[:AI_SELECT_SLOTS]
        original_sources: list[Path] = []
        if isinstance(preferred_source_paths, list):
            for source_path in preferred_source_paths:
                if isinstance(source_path, Path) and source_path.is_file():
                    original_sources.append(source_path)
                if len(original_sources) >= AI_SELECT_SLOTS:
                    break

        current_captured = [
            Path(raw)
            for raw in list(self.current_captured_paths or [])
            if isinstance(raw, str) and raw.strip() and Path(raw).is_file()
        ]

        if len(original_sources) < AI_SELECT_SLOTS and current_captured:
            for ai_path in selected_ai:
                match = re.search(r"ai_(?:pick|preview|final)_(\d+)_", ai_path.name.lower())
                if not match:
                    continue
                try:
                    idx = int(match.group(1)) - 1
                except Exception:
                    continue
                if 0 <= idx < len(current_captured):
                    source = current_captured[idx]
                    if source not in original_sources:
                        original_sources.append(source)
                if len(original_sources) >= AI_SELECT_SLOTS:
                    break

        if len(original_sources) < AI_SELECT_SLOTS:
            for source in current_captured:
                if source not in original_sources:
                    original_sources.append(source)
                if len(original_sources) >= AI_SELECT_SLOTS:
                    break

        if len(original_sources) < AI_SELECT_SLOTS:
            print("[AI_MODE] selection blocked: not enough source shots")
            return False

        source_a = original_sources[0]
        source_b = original_sources[1]
        self.selected_print_paths = [str(selected_ai[0]), str(selected_ai[1])]
        self.ai_selected_source_paths = [str(source_a), str(source_b)]
        self.current_print_slots = AI_SELECT_SLOTS
        self.print_slots = AI_SELECT_SLOTS
        print(
            "[AI_MODE] selected ai shots "
            f"ai_a={selected_ai[0].name} ai_b={selected_ai[1].name} "
            f"src_a={source_a.name} src_b={source_b.name}"
        )
        return True

    def _stop_select_photo_preload_worker(self, wait: bool = False) -> None:
        worker = self._select_photo_preload_worker
        if worker is None:
            return
        if worker.isRunning():
            worker.requestInterruption()
            if wait:
                if not worker.wait(3000):
                    print("[AFTER_LOADING] preload worker stop timeout")
        if not worker.isRunning():
            self._select_photo_preload_worker = None

    def _start_select_photo_preload(self) -> None:
        self._stop_select_photo_preload_worker(wait=False)
        self.prepared_select_photo = {}
        self.ai_selected_source_paths = []
        self._after_loading_token += 1
        token = self._after_loading_token
        self._after_loading_handled_token = -1
        self._after_loading_progress_percent = -1
        self._after_loading_started_at = time.perf_counter()

        session = self.get_active_session()
        session_dir = session.session_dir if session is not None else None
        camera_screen = self.screens.get("camera")
        gif_frames_snapshot: dict[int, list[bytes]] = {}
        if isinstance(camera_screen, CameraScreen):
            gif_frames_snapshot = camera_screen.get_gif_frames_snapshot()
        gif_settings = self.get_gif_settings()
        ai_mode_for_preload = (
            bool(self.is_ai_mode_active())
            and str(self.current_layout_id or "").strip() == AI_LAYOUT_ID
        )
        ai_style_for_preload = _resolve_preferred_ai_style_id(self.ai_style_id)
        ai_remote_allowed = True
        ai_strict_mode = self.is_ai_strict_mode_enabled()
        worker = PreloadSelectPhotoWorker(
            session_dir=session_dir,
            layout_id=self.current_layout_id,
            captured_paths=self.current_captured_paths,
            print_slots=self.current_print_slots,
            request_token=token,
            gif_enabled=bool(gif_settings.get("enabled", True)),
            gif_interval_ms=int(gif_settings.get("interval_ms", 200)),
            gif_max_width=int(gif_settings.get("max_width", 480)),
            gif_frames_by_shot=gif_frames_snapshot,
            ai_mode_4641=ai_mode_for_preload,
            ai_style_id=ai_style_for_preload,
            ai_remote_allowed=ai_remote_allowed,
            ai_strict_mode=ai_strict_mode,
            parent=self,
        )
        worker.success.connect(self._on_select_photo_preload_success)
        worker.failure.connect(self._on_select_photo_preload_failure)
        worker.progress.connect(self._on_select_photo_preload_progress)
        worker.finished.connect(self._on_select_photo_preload_finished)
        worker.finished.connect(worker.deleteLater)
        self._select_photo_preload_worker = worker

        print(
            f"[AFTER_LOADING] start layout={self.current_layout_id} "
            f"shots={len(self.current_captured_paths)} print_slots={self.current_print_slots} "
            f"ai_preload={1 if ai_mode_for_preload else 0}"
        )
        self.goto_screen("after_camera_loading")
        after_loading_screen = self.screens.get("after_camera_loading")
        if isinstance(after_loading_screen, LoadingScreen):
            if ai_mode_for_preload:
                after_loading_screen.set_status_message(
                    "AI 생성중 0%\nGenerating AI Photos 0%\n잠시만 기다려주세요\nPlease wait",
                    animate=False,
                )
            else:
                after_loading_screen.clear_status_message()
        worker.start()

    def _on_select_photo_preload_progress(self, token: int, percent: int, ko_message: str, en_message: str) -> None:
        if int(token) != self._after_loading_token:
            return
        safe_percent = max(0, min(100, int(percent)))
        if safe_percent == self._after_loading_progress_percent and not ko_message and not en_message:
            return
        self._after_loading_progress_percent = safe_percent
        after_loading_screen = self.screens.get("after_camera_loading")
        if not isinstance(after_loading_screen, LoadingScreen):
            return
        message = (
            f"AI 생성중 {safe_percent}%\n"
            f"Generating AI Photos {safe_percent}%\n"
            f"{str(ko_message or '잠시만 기다려주세요')}\n"
            f"{str(en_message or 'Please wait')}"
        )
        after_loading_screen.set_status_message(message, animate=False)

    def _finalize_after_loading(self, token: int) -> None:
        if token != self._after_loading_token:
            return
        current = self.stack.currentWidget()
        if getattr(current, "screen_name", None) != "after_camera_loading":
            return
        self._prepare_select_photo_screen()
        print("[NAV] after_camera_loading -> select_photo")
        self.goto_screen("select_photo")

    def _complete_after_loading(
        self,
        token: int,
        payload: Optional[dict],
        error_message: Optional[str] = None,
    ) -> None:
        if token != self._after_loading_token:
            return
        if self._after_loading_handled_token == token:
            return
        self._after_loading_handled_token = token
        self._after_loading_progress_percent = -1

        payload_dict = payload if isinstance(payload, dict) else {}
        if payload_dict:
            self.prepared_select_photo = payload_dict

        after_loading_screen = self.screens.get("after_camera_loading")
        if isinstance(after_loading_screen, LoadingScreen):
            after_loading_screen.clear_status_message()

        elapsed_ms = int((time.perf_counter() - self._after_loading_started_at) * 1000)
        left_count = len(payload_dict.get("left_rects") or [])
        right_count = len(payload_dict.get("right_rects") or [])
        video_gif_path = payload_dict.get("video_gif_path")
        if error_message:
            print(f"[AFTER_LOADING] preload failed: {error_message}")
            if self.is_ai_mode_active() and self.is_ai_strict_mode_enabled():
                print("[AI_MODE] preload failed strict -> block select_photo")
                self._show_runtime_notice("AI 생성 실패: 관리자에게 문의해주세요", duration_ms=1300)
                self._clear_ai_mode_runtime_state()
                self.goto_screen("frame_select")
                return
        print(
            f"[AFTER_LOADING] done ms={elapsed_ms} left={left_count} right={right_count} "
            f"gif={'yes' if video_gif_path else 'no'} "
            "-> goto select_photo"
        )

        remain_ms = max(0, 1000 - elapsed_ms)
        if remain_ms > 0:
            QTimer.singleShot(remain_ms, lambda t=token: self._finalize_after_loading(t))
            return
        self._finalize_after_loading(token)

    def _on_select_photo_preload_success(self, token: int, payload: dict) -> None:
        self._complete_after_loading(token, payload, None)

    def _on_select_photo_preload_failure(
        self,
        token: int,
        error_message: str,
        payload: dict,
    ) -> None:
        self._complete_after_loading(token, payload, error_message)

    def _on_select_photo_preload_finished(self) -> None:
        worker = self.sender()
        token = None
        if worker is not None:
            token = int(getattr(worker, "request_token", -1))
        if token is None:
            return
        if token == self._after_loading_token:
            self._select_photo_preload_worker = None
        if self._after_loading_handled_token != token:
            self._complete_after_loading(token, self.prepared_select_photo, "preload finished without payload")

    def _prepare_select_design_screen(self) -> None:
        if self.is_ai_mode_active() and len(self.selected_print_paths) < AI_SELECT_SLOTS:
            self._prepare_ai_selected_paths_from_captures()
        screen = self.screens.get("select_design")
        if isinstance(screen, SelectDesignScreen):
            screen.set_context(
                layout_id=self.current_layout_id,
                selected_paths=self.selected_print_paths,
                frame_index=self.current_design_index or 1,
                is_gray=self.current_design_is_gray,
                flip_horizontal=self.current_design_flip_horizontal,
                qr_enabled=self.current_design_qr_enabled,
            )
            self._sync_design_state_from_screen(screen)

    def _sync_design_state_from_screen(self, screen: SelectDesignScreen) -> None:
        self.current_design_index = int(screen.frame_index)
        self.current_design_is_gray = bool(screen.is_gray)
        self.current_design_flip_horizontal = bool(screen.flip_horizontal)
        self.current_design_qr_enabled = bool(screen.qr_enabled)
        frame_path = screen.get_frame_path()
        if frame_path is not None and frame_path.is_file():
            self.current_design_path = str(frame_path)

    def _prepare_admin_screen(self) -> None:
        screen = self.screens.get("admin")
        if isinstance(screen, AdminScreen):
            printer_names = self.list_windows_printers()
            screen.load_settings(
                self.admin_settings,
                self.get_payment_methods(),
                self.get_modes_settings(),
                self.get_ai_style_settings(),
                self.get_bill_acceptor_settings(),
                self.get_payment_pricing_settings(),
                self.get_pricing_layout_ids(),
                self.get_printing_settings(),
                printer_names,
            )

    @staticmethod
    def _as_bool(value, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return default

    @classmethod
    def _normalize_admin_settings(cls, raw_settings: object) -> dict:
        normalized = dict(DEFAULT_ADMIN_SETTINGS)
        if not isinstance(raw_settings, dict):
            return normalized

        normalized["test_mode"] = cls._as_bool(
            raw_settings.get("test_mode"),
            bool(DEFAULT_ADMIN_SETTINGS["test_mode"]),
        )

        backend = raw_settings.get("camera_backend", DEFAULT_ADMIN_SETTINGS["camera_backend"])
        backend_text = str(backend).strip().lower()
        normalized["camera_backend"] = backend_text if backend_text in {"auto", "edsdk", "dummy"} else "auto"

        normalized["allow_dummy_when_camera_fail"] = cls._as_bool(
            raw_settings.get("allow_dummy_when_camera_fail"),
            bool(DEFAULT_ADMIN_SETTINGS["allow_dummy_when_camera_fail"]),
        )

        try:
            countdown = int(raw_settings.get("countdown_seconds", DEFAULT_ADMIN_SETTINGS["countdown_seconds"]))
        except Exception:
            countdown = int(DEFAULT_ADMIN_SETTINGS["countdown_seconds"])
        normalized["countdown_seconds"] = max(0, min(10, countdown))

        capture_override_raw = raw_settings.get(
            "capture_slots_override",
            DEFAULT_ADMIN_SETTINGS["capture_slots_override"],
        )
        capture_override: object = "auto"
        if isinstance(capture_override_raw, str):
            text = capture_override_raw.strip().lower()
            if text == "auto":
                capture_override = "auto"
            else:
                try:
                    parsed = int(text)
                except Exception:
                    parsed = None
                if parsed in {4, 6, 8, 9, 10}:
                    capture_override = parsed
        elif isinstance(capture_override_raw, (int, float)):
            parsed = int(capture_override_raw)
            if parsed in {4, 6, 8, 9, 10}:
                capture_override = parsed
        normalized["capture_slots_override"] = capture_override

        normalized["debug_fullscreen_shutter"] = cls._as_bool(
            raw_settings.get("debug_fullscreen_shutter"),
            bool(DEFAULT_ADMIN_SETTINGS["debug_fullscreen_shutter"]),
        )
        normalized["print_dry_run"] = cls._as_bool(
            raw_settings.get("print_dry_run"),
            bool(DEFAULT_ADMIN_SETTINGS["print_dry_run"]),
        )
        normalized["upload_dry_run"] = cls._as_bool(
            raw_settings.get("upload_dry_run"),
            bool(DEFAULT_ADMIN_SETTINGS["upload_dry_run"]),
        )
        normalized["qr_enabled"] = cls._as_bool(
            raw_settings.get("qr_enabled"),
            bool(DEFAULT_ADMIN_SETTINGS["qr_enabled"]),
        )
        return normalized

    def _read_config_dict(self) -> dict:
        if not self.config_path.is_file():
            return {}
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            print(f"[CONFIG] read failed: {exc}")
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    def _write_config_dict_atomic(self, data: dict) -> None:
        target_path = Path(self.config_path)
        payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

        def _write(path: Path) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(path.suffix + ".tmp")
            tmp_path.write_text(payload, encoding="utf-8")
            os.replace(tmp_path, path)

        candidate_paths: list[Path] = [target_path]
        for root in _preferred_runtime_data_dirs():
            candidate_paths.append(Path(root) / "config" / "config.json")
        for root in _iter_runtime_data_dir_candidates():
            candidate_paths.append(Path(root) / "config" / "config.json")

        dedup_candidates: list[Path] = []
        seen: set[str] = set()
        for path in candidate_paths:
            key = self._normalize_path_token(path)
            if key in seen:
                continue
            seen.add(key)
            dedup_candidates.append(path)

        for idx, candidate in enumerate(dedup_candidates):
            try:
                _write(candidate)
                self.config_path = candidate
                if idx > 0:
                    _safe_boot_write(
                        f"[CONFIG] write fallback selected: {candidate}\n"
                    )
                return
            except Exception as exc:
                if idx == 0:
                    _safe_boot_write(
                        f"[CONFIG] write denied at {candidate} ({exc})\n"
                    )
                else:
                    _safe_boot_write(
                        f"[CONFIG] write fallback failed at {candidate} ({exc})\n"
                    )

        temp_fallback = Path(os.environ.get("TEMP", os.getcwd())) / "ViorafilmKiosk" / "config" / "config.json"
        _safe_boot_write(
            f"[CONFIG] all write candidates failed -> temp {temp_fallback}\n"
        )
        _write(temp_fallback)
        self.config_path = temp_fallback

    @staticmethod
    def _parse_layout_id_from_action(action: object) -> Optional[str]:
        text = str(action or "").strip()
        if not text.startswith("select_layout:"):
            return None
        layout_id = text.split(":", 1)[1].strip()
        return layout_id or None

    @classmethod
    def _extract_layout_ids_from_hotspots(cls, hotspot_data: object) -> list[str]:
        if not isinstance(hotspot_data, dict):
            return []
        entries = hotspot_data.get("frame_select")
        if not isinstance(entries, list):
            return []
        found: set[str] = set()
        for item in entries:
            action_value: object = None
            if isinstance(item, Hotspot):
                action_value = item.action
            elif isinstance(item, dict):
                action_value = item.get("action")
            layout_id = cls._parse_layout_id_from_action(action_value)
            if layout_id:
                found.add(layout_id)
        return sorted(found)

    def _detect_layout_ids_from_hotspots_file(self) -> list[str]:
        try:
            loaded = load_hotspots(self.hotspots_path)
        except Exception as exc:
            print(f"[PRICING] hotspot layout detect failed: {exc}")
            return []
        layouts = self._extract_layout_ids_from_hotspots(loaded)
        if layouts:
            print(f"[PRICING] layouts detected: {','.join(layouts)}")
        return layouts

    def _detect_layout_ids_from_loaded_hotspots(self) -> list[str]:
        layouts = self._extract_layout_ids_from_hotspots(self.hotspot_map)
        if layouts:
            print(f"[PRICING] layouts detected: {','.join(layouts)}")
        return layouts

    def _pricing_layout_ids_with_modes(
        self,
        base_layout_ids: Optional[list[str]] = None,
        celebrity_layout_id: Optional[str] = None,
    ) -> list[str]:
        merged_ordered: list[str] = []

        def _append_layout(value: object) -> None:
            key = str(value or "").strip()
            if key and key not in merged_ordered:
                merged_ordered.append(key)

        for layout_id in DEFAULT_FRAME_LAYOUT_IDS:
            _append_layout(layout_id)
        for layout_id in list(base_layout_ids or []):
            _append_layout(layout_id)
        celeb_layout = str(celebrity_layout_id or "").strip()
        if not celeb_layout:
            celeb_cfg = getattr(self, "celebrity_settings", {})
            if isinstance(celeb_cfg, dict):
                celeb_layout = str(
                    celeb_cfg.get("layout_id", DEFAULT_CELEBRITY_SETTINGS["layout_id"])
                ).strip()
        celeb_layout = celeb_layout or str(DEFAULT_CELEBRITY_SETTINGS["layout_id"]).strip() or "2461"
        _append_layout(celeb_layout)
        _append_layout(str(AI_LAYOUT_ID).strip())
        return list(merged_ordered)

    def get_pricing_layout_ids(self) -> list[str]:
        return self._pricing_layout_ids_with_modes(self.available_layout_ids)

    def _sync_pricing_layout_defaults(self, persist: bool = False) -> bool:
        detected = self._detect_layout_ids_from_loaded_hotspots()
        if not detected:
            detected = list(self.available_layout_ids)
        if not detected:
            settings = self.get_payment_pricing_settings()
            detected = sorted(settings.get("layouts", {}).keys())
        self.available_layout_ids = list(detected)
        pricing_layout_ids = self._pricing_layout_ids_with_modes(detected)

        settings = self.get_payment_pricing_settings()
        default_price = max(0, int(settings.get("default_price", DEFAULT_PRICING_SETTINGS["default_price"])))
        layouts = dict(settings.get("layouts", {}))
        changed = False
        for layout_id in pricing_layout_ids:
            if layout_id not in layouts:
                layouts[layout_id] = default_price
                changed = True
        if changed:
            self.payment_pricing_settings["layouts"] = layouts
        should_persist = bool(changed)
        if persist:
            config = self._read_config_dict()
            raw_pricing = config.get("pricing") if isinstance(config, dict) else None
            if not isinstance(raw_pricing, dict):
                should_persist = True
            else:
                if "currency_prefix" not in raw_pricing or "default_price" not in raw_pricing:
                    should_persist = True
                raw_layouts = raw_pricing.get("layouts")
                if not isinstance(raw_layouts, dict):
                    should_persist = True
                else:
                    for layout_id in pricing_layout_ids:
                        if layout_id not in raw_layouts:
                            should_persist = True
                            break
        if persist and should_persist:
            config = self._read_config_dict()
            config["pricing"] = {
                "currency_prefix": str(
                    self.payment_pricing_settings.get("currency_prefix", DEFAULT_PRICING_SETTINGS["currency_prefix"])
                ),
                "default_price": int(
                    self.payment_pricing_settings.get("default_price", DEFAULT_PRICING_SETTINGS["default_price"])
                ),
                "layouts": dict(layouts),
            }
            config["payment_pricing"] = {
                "default_price": int(
                    self.payment_pricing_settings.get("default_price", DEFAULT_PRICING_SETTINGS["default_price"])
                ),
                "pricing_by_layout": dict(layouts),
            }
            self._write_config_dict_atomic(config)
        return bool(changed)

    def _resolve_admin_settings(self) -> dict:
        config = self._read_config_dict()
        return self._normalize_admin_settings(config.get("admin"))

    @classmethod
    def _normalize_payment_methods(cls, raw_settings: object) -> tuple[dict[str, bool], bool]:
        normalized = dict(DEFAULT_PAYMENT_METHODS)
        if isinstance(raw_settings, dict):
            for key in ("cash", "card", "coupon"):
                normalized[key] = cls._as_bool(raw_settings.get(key), bool(DEFAULT_PAYMENT_METHODS[key]))
        forced_cash = False
        if not (normalized["cash"] or normalized["card"] or normalized["coupon"]):
            normalized["cash"] = True
            forced_cash = True
        return normalized, forced_cash

    def _resolve_payment_methods(self) -> dict[str, bool]:
        config = self._read_config_dict()
        methods_raw = config.get("payment_methods") if isinstance(config, dict) else None
        normalized, _forced_cash = self._normalize_payment_methods(methods_raw)
        return normalized

    @classmethod
    def _normalize_modes_settings(cls, raw_settings: object) -> dict[str, bool]:
        normalized = dict(DEFAULT_MODE_SETTINGS)
        if isinstance(raw_settings, dict):
            normalized["celebrity_enabled"] = cls._as_bool(
                raw_settings.get("celebrity_enabled"),
                bool(DEFAULT_MODE_SETTINGS["celebrity_enabled"]),
            )
            normalized["ai_enabled"] = cls._as_bool(
                raw_settings.get("ai_enabled"),
                bool(DEFAULT_MODE_SETTINGS["ai_enabled"]),
            )
        return normalized

    def _resolve_modes_settings(self) -> dict[str, bool]:
        config = self._read_config_dict()
        raw = config.get("modes") if isinstance(config, dict) else None
        return self._normalize_modes_settings(raw)

    @classmethod
    def _normalize_ai_styles_settings(cls, raw_settings: object) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        raw_map = raw_settings if isinstance(raw_settings, dict) else {}
        for index, (style_id, defaults) in enumerate(DEFAULT_AI_STYLE_PRESETS.items(), start=1):
            raw_item = raw_map.get(style_id) if isinstance(raw_map, dict) else None
            item = raw_item if isinstance(raw_item, dict) else {}
            label_ko_default = str(defaults.get("label_ko", style_id)).strip() or style_id
            label_en_default = str(defaults.get("label_en", style_id)).strip() or label_ko_default
            prompt_default = str(defaults.get("prompt", "Stylized portrait")).strip() or "Stylized portrait"

            label_ko = str(item.get("label_ko", label_ko_default)).strip() or label_ko_default
            label_en = str(item.get("label_en", label_en_default)).strip() or label_en_default
            prompt = str(item.get("prompt", prompt_default)).strip() or prompt_default
            enabled = cls._as_bool(item.get("enabled"), True)
            try:
                order = int(item.get("order", index))
            except Exception:
                order = index
            normalized[style_id] = {
                "label_ko": label_ko,
                "label_en": label_en,
                "prompt": prompt,
                "enabled": bool(enabled),
                "order": max(1, int(order)),
            }
        return normalized

    def _resolve_ai_styles_settings(self) -> dict[str, dict[str, Any]]:
        config = self._read_config_dict()
        raw = config.get("ai_styles") if isinstance(config, dict) else None
        return self._normalize_ai_styles_settings(raw)

    def _apply_ai_style_settings(self, ai_styles: dict, emit_log: bool = True) -> None:
        normalized = self._normalize_ai_styles_settings(ai_styles)
        enabled_items = [
            (style_id, info)
            for style_id, info in normalized.items()
            if bool(info.get("enabled", True))
        ]
        enabled_items.sort(key=lambda item: (int(item[1].get("order", 9999)), item[0]))
        if not enabled_items:
            first_key = next(iter(DEFAULT_AI_STYLE_PRESETS.keys()))
            normalized[first_key]["enabled"] = True
            normalized[first_key]["order"] = 1
            enabled_items = [(first_key, normalized[first_key])]
        self.ai_style_settings = normalized

        AI_STYLE_PRESETS.clear()
        for style_id, style_info in enabled_items:
            AI_STYLE_PRESETS[style_id] = {
                "label_ko": str(style_info.get("label_ko", style_id)),
                "label_en": str(style_info.get("label_en", style_info.get("label_ko", style_id))),
                "prompt": str(style_info.get("prompt", "Stylized portrait")),
            }

        screen = getattr(self, "screens", {}).get("ai_style_select") if hasattr(self, "screens") else None
        if isinstance(screen, AiStyleSelectScreen):
            screen.reload_style_cards()

        if emit_log:
            style_summary = ", ".join(
                f"{style_id}=\"{style_info.get('label_ko', style_id)}\"(enabled={1 if bool(style_info.get('enabled', True)) else 0},order={int(style_info.get('order', 0) or 0)})"
                for style_id, style_info in normalized.items()
            )
            print(f"[ADMIN] ai_styles {style_summary}")

    @classmethod
    def _normalize_celebrity_settings(cls, raw_settings: object) -> dict[str, str]:
        normalized = dict(DEFAULT_CELEBRITY_SETTINGS)
        if isinstance(raw_settings, dict):
            templates_dir = _remap_legacy_install_path(
                raw_settings.get("templates_dir", normalized["templates_dir"])
            ).strip()
            layout_id = str(raw_settings.get("layout_id", normalized["layout_id"])).strip()
            if templates_dir:
                normalized["templates_dir"] = templates_dir
            if layout_id:
                normalized["layout_id"] = layout_id
        return normalized

    def _resolve_celebrity_settings(self) -> dict[str, str]:
        config = self._read_config_dict()
        raw = config.get("celebrity") if isinstance(config, dict) else None
        return self._normalize_celebrity_settings(raw)

    @classmethod
    def _normalize_layout_settings(cls, raw_settings: object) -> dict:
        normalized = {"strip_2x6": list(DEFAULT_LAYOUT_SETTINGS["strip_2x6"])}
        if not isinstance(raw_settings, dict):
            return normalized
        raw_strip = raw_settings.get("strip_2x6")
        if isinstance(raw_strip, list):
            values = []
            for item in raw_strip:
                text = str(item).strip()
                if text:
                    values.append(text)
            if values:
                normalized["strip_2x6"] = sorted(set(values))
        return normalized

    def _resolve_layout_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("layouts") if isinstance(config, dict) else None
        return self._normalize_layout_settings(raw)

    def get_strip_2x6_layouts(self) -> set[str]:
        settings = self.layout_settings if isinstance(self.layout_settings, dict) else {}
        values = settings.get("strip_2x6")
        if not isinstance(values, list):
            values = list(DEFAULT_LAYOUT_SETTINGS["strip_2x6"])
        result = {str(v).strip() for v in values if str(v).strip()}
        # 2641/6241 are always treated as strip layouts.
        # 2461 is accepted as a legacy alias.
        result.update({"2641", "6241", "2461"})
        return result

    @classmethod
    def _normalize_bill_acceptor_settings(cls, raw_settings: object) -> dict:
        normalized = dict(DEFAULT_BILL_ACCEPTOR_SETTINGS)
        denoms = dict(DEFAULT_BILL_ACCEPTOR_SETTINGS["denoms"])
        bill_to_amount: dict[int, int] = {}
        normalized["denoms"] = denoms
        normalized["bill_to_amount"] = bill_to_amount
        if not isinstance(raw_settings, dict):
            return normalized

        normalized["enabled"] = cls._as_bool(
            raw_settings.get("enabled"),
            bool(DEFAULT_BILL_ACCEPTOR_SETTINGS["enabled"]),
        )

        profile = str(raw_settings.get("profile", DEFAULT_BILL_ACCEPTOR_SETTINGS["profile"])).strip()
        if profile not in BILL_PROFILES:
            profile = str(DEFAULT_BILL_ACCEPTOR_SETTINGS["profile"])
        normalized["profile"] = profile

        profile_info = BILL_PROFILES.get(profile, {})
        default_denoms = profile_info.get("default_denoms")
        if isinstance(default_denoms, dict):
            for key in denoms.keys():
                denoms[key] = cls._as_bool(default_denoms.get(key), denoms[key])
        profile_bill_map = profile_info.get("bill_to_amount")
        if isinstance(profile_bill_map, dict):
            for raw_key, raw_amount in profile_bill_map.items():
                try:
                    code = int(raw_key) & 0xFF
                    amount = int(raw_amount)
                except Exception:
                    continue
                if amount > 0:
                    bill_to_amount[code] = amount

        raw_denoms = raw_settings.get("denoms")
        if isinstance(raw_denoms, dict):
            for key in denoms.keys():
                denoms[key] = cls._as_bool(raw_denoms.get(key), denoms[key])
        raw_bill_map = raw_settings.get("bill_to_amount")
        if isinstance(raw_bill_map, dict):
            for raw_key, raw_amount in raw_bill_map.items():
                try:
                    code = int(raw_key) & 0xFF
                    amount = int(raw_amount)
                except Exception:
                    continue
                if amount > 0:
                    bill_to_amount[code] = amount

        raw_port = raw_settings.get("port", profile_info.get("default_port", DEFAULT_BILL_ACCEPTOR_SETTINGS["port"]))
        port_text = str(raw_port).strip()
        if _is_auto_serial_port(port_text):
            normalized["port"] = "AUTO"
        else:
            normalized["port"] = (
                port_text
                if port_text
                else str(profile_info.get("default_port", DEFAULT_BILL_ACCEPTOR_SETTINGS["port"]))
            )

        default_baud = int(profile_info.get("baud", DEFAULT_BILL_ACCEPTOR_SETTINGS["baud"]))
        try:
            baud = int(raw_settings.get("baud", default_baud))
        except Exception:
            baud = default_baud
        normalized["baud"] = max(300, min(921600, baud))
        return normalized

    def _resolve_bill_acceptor_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("bill_acceptor") if isinstance(config, dict) else None
        return self._normalize_bill_acceptor_settings(raw)

    def get_bill_acceptor_settings(self) -> dict:
        settings = dict(self.bill_acceptor_settings)
        denoms = settings.get("denoms")
        raw_bill_map = settings.get("bill_to_amount")
        bill_to_amount: dict[int, int] = {}
        if isinstance(raw_bill_map, dict):
            for raw_key, raw_amount in raw_bill_map.items():
                try:
                    code = int(raw_key) & 0xFF
                    amount = int(raw_amount)
                except Exception:
                    continue
                if amount > 0:
                    bill_to_amount[code] = amount
        settings["denoms"] = dict(denoms) if isinstance(denoms, dict) else dict(DEFAULT_BILL_ACCEPTOR_SETTINGS["denoms"])
        settings["bill_to_amount"] = bill_to_amount
        return settings

    def list_serial_ports(self) -> list[str]:
        if serial_list_ports is None:
            return []
        ports: list[str] = []
        try:
            for info in serial_list_ports.comports():
                device = str(getattr(info, "device", "")).strip()
                if device:
                    ports.append(device)
        except Exception as exc:
            print(f"[ADMIN] serial port scan failed: {exc}")
            return []

        unique = sorted(set(ports))
        return unique

    def is_bill_acceptor_running(self) -> bool:
        worker = self.bill_worker
        return bool(worker is not None and worker.isRunning())

    def _on_bill_worker_log(self, message: str) -> None:
        print(str(message))

    def _on_bill_worker_failed(self, message: str) -> None:
        print(f"[BILL] worker failed: {message}")

    def _on_bill_worker_accepted(self, amount: int, status: int, billdata: int) -> None:
        self.current_bill_total_amount += int(amount)
        print(
            f"[BILL] status=0x{int(status) & 0xFF:02X} -> billdata={int(billdata)} amount={int(amount)} "
            f"total={self.current_bill_total_amount}"
        )
        self._on_bill_event_for_payment(int(amount))

    def _on_bill_worker_finished(self) -> None:
        self.bill_worker = None
        print("[BILL] worker stopped")
        admin_screen = self.screens.get("admin")
        if isinstance(admin_screen, AdminScreen):
            admin_screen._refresh_bill_test_buttons()

    def start_bill_acceptor_test(self, settings: Optional[dict] = None) -> bool:
        if serial is None:
            print("[BILL] pyserial missing")
            return False

        normalized = self._normalize_bill_acceptor_settings(
            settings if settings is not None else self.bill_acceptor_settings
        )
        if not bool(normalized.get("enabled", False)):
            print("[BILL] start blocked: bill_acceptor disabled")
            return False

        if self.is_bill_acceptor_running():
            self.stop_bill_acceptor_test(wait_ms=3000)

        worker = BillAcceptorWorker(normalized, self)
        worker.log.connect(self._on_bill_worker_log)
        worker.bill_accepted.connect(self._on_bill_worker_accepted)
        worker.failed.connect(self._on_bill_worker_failed)
        worker.finished.connect(self._on_bill_worker_finished)
        self.bill_worker = worker
        self.bill_acceptor_settings = normalized
        self.current_bill_total_amount = 0
        worker.start()
        return True

    def stop_bill_acceptor_test(self, wait_ms: int = 3000) -> None:
        worker = self.bill_worker
        if worker is None:
            return
        worker.request_stop()
        if not worker.wait(max(500, int(wait_ms))):
            print("[BILL] worker stop timeout")
            return
        self.bill_worker = None

    @staticmethod
    def _resolve_payment_mode(methods: dict[str, bool]) -> str:
        cash = bool(methods.get("cash", False))
        card = bool(methods.get("card", False))
        coupon = bool(methods.get("coupon", False))
        if cash and card and coupon:
            return "cashcardcoupon_mode"
        if cash and card:
            return "cashcard_mode"
        if cash and coupon:
            return "cashcoupon_mode"
        if card and coupon:
            return "cardcoupon_mode"
        if cash:
            return "cash_only"
        if coupon:
            return "coupon_only"
        if card:
            return "card_only"
        return "cash_only"

    def get_payment_methods(self) -> dict[str, bool]:
        return dict(self.payment_methods)

    def _enabled_payment_method_list(self, methods: Optional[dict[str, bool]] = None) -> list[str]:
        source = methods if isinstance(methods, dict) else self.get_payment_methods()
        enabled: list[str] = []
        for key in ("cash", "card", "coupon"):
            if bool(source.get(key, False)):
                enabled.append(key)
        return enabled

    def _single_enabled_payment_method(self, methods: Optional[dict[str, bool]] = None) -> Optional[str]:
        enabled = self._enabled_payment_method_list(methods)
        if len(enabled) == 1:
            return enabled[0]
        return None

    def _enter_single_payment_flow(self, method: str) -> bool:
        target_method = str(method or "").strip().lower()
        enabled = self.get_payment_methods()
        if target_method not in {"cash", "card", "coupon"}:
            return False
        if not bool(enabled.get(target_method, False)):
            return False

        if target_method == "cash":
            self.current_payment_method = "cash"
            self.payment_method = self.current_payment_method
            self.current_coupon_value = 0
            self.current_coupon_code = None
            self.pending_coupon_code = None
            if self.current_required_amount <= 0:
                self._refresh_required_amount()
            print("[PAYMENT] single mode auto -> pay_cash")
            self.goto_screen("pay_cash")
            return True

        if target_method == "coupon":
            coupon_settings = self.get_coupon_settings()
            if not bool(coupon_settings.get("enabled", True)):
                print("[PAYMENT] single mode coupon blocked: coupon disabled")
                return False
            self.current_payment_method = "coupon"
            self.payment_method = self.current_payment_method
            print("[PAYMENT] single mode auto -> coupon_input")
            self.goto_screen("coupon_input")
            return True

        if target_method == "card":
            if self.is_test_mode():
                self.current_payment_method = "card"
                self.payment_method = self.current_payment_method
                print("[PAYMENT] single mode auto(test) -> payment_complete_success")
                self.goto_screen("payment_complete_success")
                return True
            print("[PAYMENT] single mode card unsupported -> keep payment_method")
            return False

        return False

    def _set_hotspot_rect(self, screen: str, hotspot_id: str, rect: list[int]) -> bool:
        hotspots = list(self.hotspot_map.get(screen, []))
        if not hotspots:
            return False
        changed = False
        normalized = tuple(int(v) for v in rect[:4]) if len(rect) == 4 else (0, 0, 0, 0)
        rebuilt: list[Hotspot] = []
        for hs in hotspots:
            if hs.id == hotspot_id:
                rebuilt.append(Hotspot(id=hs.id, rect=normalized, action=hs.action))
                changed = True
            else:
                rebuilt.append(hs)
        if changed:
            self.hotspot_map[screen] = rebuilt
        return changed

    def _set_hotspot_action(self, screen: str, hotspot_id: str, action: str) -> bool:
        hotspots = list(self.hotspot_map.get(screen, []))
        if not hotspots:
            return False
        changed = False
        rebuilt: list[Hotspot] = []
        for hs in hotspots:
            if hs.id == hotspot_id:
                rebuilt.append(Hotspot(id=hs.id, rect=hs.rect, action=action))
                changed = True
            else:
                rebuilt.append(hs)
        if changed:
            self.hotspot_map[screen] = rebuilt
        return changed

    def _ensure_payment_hotspot_baseline(self) -> None:
        defaults = [
            ("pay_select_cash", [0, 0, 1, 1], "payment:cash"),
            ("pay_select_card", [0, 0, 1, 1], "payment:card"),
            ("pay_select_coupon", [0, 0, 1, 1], "payment:coupon"),
            ("pay_next", [1740, 910, 180, 160], "payment:next"),
            ("pay_back", [40, 900, 220, 220], "goto:how_many_prints"),
        ]
        current = list(self.hotspot_map.get("payment_method", []))
        by_id = {hs.id: hs for hs in current}
        for hotspot_id, rect, action in defaults:
            if hotspot_id not in by_id:
                current.append(Hotspot(id=hotspot_id, rect=tuple(rect), action=action))
        self.hotspot_map["payment_method"] = current
        for hotspot_id, _rect, action in defaults:
            self._set_hotspot_action("payment_method", hotspot_id, action)

    def _apply_payment_hotspot_overrides(self) -> None:
        self._ensure_payment_hotspot_baseline()

        payment_screen = self.screens.get("payment_method")
        if isinstance(payment_screen, AppPaymentMethodScreen):
            mode = payment_screen.get_mode()
        else:
            mode = self._resolve_payment_mode(self.payment_methods)
        off_rect = [-10, -10, 1, 1]
        cash_rect = list(off_rect)
        card_rect = list(off_rect)
        coupon_rect = list(off_rect)

        if mode == "cashcardcoupon_mode":
            cash_rect = [317, 340, 366, 373]
            card_rect = [782, 340, 366, 373]
            coupon_rect = [1247, 340, 365, 373]
        elif mode == "cashcard_mode":
            cash_rect = [521, 379, 366, 373]
            card_rect = [1014, 379, 366, 373]
            coupon_rect = list(off_rect)
        elif mode == "cashcoupon_mode":
            cash_rect = [521, 379, 366, 373]
            coupon_rect = [1014, 379, 366, 373]
            card_rect = list(off_rect)
        elif mode == "cardcoupon_mode":
            card_rect = [521, 380, 366, 373]
            coupon_rect = [1014, 380, 366, 373]
            cash_rect = list(off_rect)
        elif mode == "card_only":
            card_rect = [521, 380, 366, 373]
            cash_rect = list(off_rect)
            coupon_rect = list(off_rect)
        elif mode == "coupon_only":
            coupon_rect = [521, 380, 366, 373]
            cash_rect = list(off_rect)
            card_rect = list(off_rect)
        else:
            cash_rect = [521, 379, 366, 373]
            card_rect = list(off_rect)
            coupon_rect = list(off_rect)

        self._set_hotspot_rect("payment_method", "pay_select_cash", cash_rect)
        self._set_hotspot_rect("payment_method", "pay_select_card", card_rect)
        self._set_hotspot_rect("payment_method", "pay_select_coupon", coupon_rect)
        self._set_hotspot_rect("payment_method", "pay_next", [1740, 910, 180, 160])
        self._set_hotspot_rect("payment_method", "pay_back", [40, 900, 220, 220])

        print(
            f"[PAYMENT_RECT] mode={mode} "
            f"cash={cash_rect} card={card_rect} coupon={coupon_rect}"
        )

        if isinstance(payment_screen, ImageScreen):
            payment_screen.set_hotspots(self.hotspot_map.get("payment_method", []))
            payment_screen.set_overlay_visible(self.show_hotspot_overlay)

    def _frame_select_layout_hotspots(self) -> list[tuple[str, Hotspot]]:
        entries = list(self.hotspot_map.get("frame_select", []))
        found: list[tuple[str, Hotspot]] = []
        for hotspot in entries:
            layout_id = self._parse_layout_id_from_action(hotspot.action)
            if not layout_id:
                continue
            found.append((layout_id, hotspot))
        return found

    def _clear_frame_select_price_labels(self) -> None:
        for label in self._frame_select_price_labels.values():
            try:
                label.deleteLater()
            except Exception:
                pass
        self._frame_select_price_labels = {}

    def _refresh_frame_select_price_labels(self) -> None:
        screen = self.screens.get("frame_select")
        if not isinstance(screen, ImageScreen):
            return
        layout_hotspots = self._frame_select_layout_hotspots()
        if not layout_hotspots:
            self._clear_frame_select_price_labels()
            return
        pricing = self.get_payment_pricing_settings()
        prefix = str(pricing.get("currency_prefix", ""))
        default_price = max(0, int(pricing.get("default_price", DEFAULT_PRICING_SETTINGS["default_price"])))
        layout_price_map = dict(pricing.get("layouts", {}))

        active_ids = {layout_id for layout_id, _ in layout_hotspots}
        for layout_id in list(self._frame_select_price_labels.keys()):
            if layout_id not in active_ids:
                label = self._frame_select_price_labels.pop(layout_id)
                label.deleteLater()

        for layout_id, hotspot in layout_hotspots:
            label = self._frame_select_price_labels.get(layout_id)
            if label is None:
                label = QLabel(screen)
                label.setAlignment(ALIGN_CENTER)
                label.setStyleSheet(
                    "QLabel { color: white; background-color: rgba(0,0,0,150); "
                    "font-size: 28px; font-weight: 700; border-radius: 4px; }"
                )
                label.setAttribute(WA_TRANSPARENT, True)
                self._frame_select_price_labels[layout_id] = label

            amount = layout_price_map.get(layout_id, default_price)
            try:
                amount_value = max(0, int(amount))
            except Exception:
                amount_value = default_price
            text = format_price(prefix, amount_value)
            label.setText(text)
            x, y, w, h = hotspot.rect
            label_h = 30
            layout_key = str(layout_id).strip()
            frame_bounds = self._detect_frame_bounds(layout_key, hotspot.rect)
            if frame_bounds is not None:
                frame_left, frame_right, frame_bottom = frame_bounds
                # Keep price top exactly under the visual black frame edge.
                mapped_y = int(frame_bottom) + 1
            else:
                mapped_y = self.FRAME_SELECT_PRICE_Y_BY_LAYOUT.get(layout_key)
                if mapped_y is None:
                    mapped_y = int(y) + int(h) - label_h - 6
            mapped_y += int(self.FRAME_SELECT_PRICE_Y_OFFSET_BY_LAYOUT.get(layout_key, 0))
            label_y = max(0, min(int(mapped_y), DESIGN_HEIGHT - label_h - 5))
            metrics = label.fontMetrics()
            text_w = int(metrics.horizontalAdvance(text))
            label_w = max(120, min(int(w) - 12, text_w + 54))
            if frame_bounds is not None:
                frame_center_x = int((int(frame_left) + int(frame_right)) // 2)
                label_x = frame_center_x - (label_w // 2)
            else:
                label_x = int(x) + max(0, (int(w) - label_w) // 2)
            label_x += int(self.FRAME_SELECT_PRICE_X_OFFSET_BY_LAYOUT.get(layout_key, 0))
            label_x = max(0, min(int(label_x), DESIGN_WIDTH - label_w))
            widget_rect = screen.design_rect_to_widget((int(label_x), int(label_y), int(label_w), int(label_h)))
            label.setGeometry(widget_rect)
            label.show()
            label.raise_()
            print(
                f"[FRAME_SELECT] price label layout={layout_id} "
                f"rect={[int(label_x), int(label_y), int(label_w), int(label_h)]} text=\"{text}\""
            )

    def _detect_frame_bounds(
        self,
        layout_id: str,
        rect: tuple[int, int, int, int],
    ) -> Optional[tuple[int, int, int]]:
        bg_path = self.FRAME_SELECT_BG_PATH
        cache_key = (str(bg_path), str(layout_id or ""), int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        if cache_key in _FRAME_SELECT_BOUNDS_CACHE:
            return _FRAME_SELECT_BOUNDS_CACHE[cache_key]
        if not bg_path.is_file():
            _FRAME_SELECT_BOUNDS_CACHE[cache_key] = None
            return None
        try:
            with Image.open(bg_path) as source:
                rgb = source.convert("RGB")
                width, height = rgb.size
                x, y, w, h = [int(v) for v in rect]
                left = max(0, min(width - 1, x))
                top = max(0, min(height - 1, y))
                right = max(left + 1, min(width, x + w))
                bottom = max(top + 1, min(height, y + h))
                crop = rgb.crop((left, top, right, bottom))
                px = crop.load()
                cw, ch = crop.size
                found = 0
                min_x = cw
                max_x = -1
                max_y = -1
                for yy in range(ch):
                    for xx in range(cw):
                        r, g, b = px[xx, yy]
                        if r < 55 and g < 55 and b < 55:
                            found += 1
                            if xx < min_x:
                                min_x = xx
                            if xx > max_x:
                                max_x = xx
                            if yy > max_y:
                                max_y = yy
                if found < 80 or max_y < 0 or max_x < min_x:
                    _FRAME_SELECT_BOUNDS_CACHE[cache_key] = None
                    return None
                detected_left = left + min_x
                detected_right = left + max_x
                detected_bottom = top + max_y
                detected = (int(detected_left), int(detected_right), int(detected_bottom))
                _FRAME_SELECT_BOUNDS_CACHE[cache_key] = detected
                return detected
        except Exception:
            _FRAME_SELECT_BOUNDS_CACHE[cache_key] = None
            return None

    def _ensure_frame_select_mode_buttons(self) -> None:
        screen = self.screens.get("frame_select")
        if not isinstance(screen, ImageScreen):
            return
        if self._frame_select_mode_buttons:
            self._layout_frame_select_mode_buttons()
            return

        celebrity_btn = QPushButton("연예인 모드\nCelebrity Mode", screen)
        ai_btn = QPushButton("AI모드\nAI Mode", screen)
        for btn in (celebrity_btn, ai_btn):
            btn.setStyleSheet(
                "QPushButton {"
                "background-color: rgba(0,0,0,150); color: white; font-size: 22px; font-weight: 700; "
                "border: 2px solid rgba(255,255,255,140); border-radius: 10px; }"
                "QPushButton:pressed { background-color: rgba(0,0,0,200); }"
            )
            btn.setFocusPolicy(Qt.NoFocus if hasattr(Qt, "NoFocus") else Qt.FocusPolicy.NoFocus)

        celebrity_btn.clicked.connect(self._on_frame_select_mode_celebrity_clicked)
        ai_btn.clicked.connect(self._on_frame_select_mode_ai_clicked)
        self._frame_select_mode_buttons = {
            "celebrity": celebrity_btn,
            "ai": ai_btn,
        }
        self._frame_select_mode_price_labels = {}
        for key in ("celebrity", "ai"):
            price_label = QLabel(screen)
            price_label.setAlignment(ALIGN_CENTER)
            price_label.setAttribute(WA_TRANSPARENT, True)
            price_label.setStyleSheet(
                "QLabel { color: white; background-color: rgba(0,0,0,150); "
                "font-size: 28px; font-weight: 700; border-radius: 4px; }"
            )
            self._frame_select_mode_price_labels[key] = price_label
        self._layout_frame_select_mode_buttons()

    def _frame_select_mode_layout_id(self, mode_key: str) -> str:
        key = str(mode_key or "").strip().lower()
        if key == "celebrity":
            celeb_layout = str(DEFAULT_CELEBRITY_SETTINGS.get("layout_id", "2461")).strip() or "2461"
            try:
                celeb_cfg = self.get_celebrity_settings()
                if isinstance(celeb_cfg, dict):
                    celeb_layout = str(celeb_cfg.get("layout_id", celeb_layout)).strip() or celeb_layout
            except Exception:
                pass
            return celeb_layout
        return str(AI_LAYOUT_ID).strip() or "4641"

    def _layout_frame_select_mode_buttons(self) -> None:
        screen = self.screens.get("frame_select")
        if not isinstance(screen, ImageScreen):
            return
        for key, button in self._frame_select_mode_buttons.items():
            rect = self.FRAME_SELECT_MODE_RECTS.get(key)
            if rect is None:
                continue
            button.setGeometry(screen.design_rect_to_widget(rect))
            button.raise_()
            price_label = self._frame_select_mode_price_labels.get(key)
            if price_label is not None:
                x, y, w, h = rect
                label_h = 34
                price_text = str(price_label.text() or "").strip()
                metrics = price_label.fontMetrics()
                text_w = int(metrics.horizontalAdvance(price_text)) if price_text else 140
                label_w = max(120, min(int(w) - 18, text_w + 54))
                label_x = int(x) + max(0, (int(w) - label_w) // 2)
                label_y = min(int(y) + int(h) + 2, DESIGN_HEIGHT - label_h - 5)
                price_label.setGeometry(screen.design_rect_to_widget((label_x, label_y, label_w, label_h)))
                price_label.raise_()

    def _refresh_frame_select_mode_buttons(self) -> None:
        self._ensure_frame_select_mode_buttons()
        self._layout_frame_select_mode_buttons()
        pricing = self.get_payment_pricing_settings()
        prefix = str(pricing.get("currency_prefix", ""))
        default_price = max(0, int(pricing.get("default_price", DEFAULT_PRICING_SETTINGS["default_price"])))
        layout_price_map = dict(pricing.get("layouts", {}))
        modes = self.get_modes_settings()
        celebrity_enabled = bool(modes.get("celebrity_enabled", DEFAULT_MODE_SETTINGS["celebrity_enabled"]))
        ai_enabled = bool(modes.get("ai_enabled", DEFAULT_MODE_SETTINGS["ai_enabled"]))
        ai_runtime_ready = self._has_runtime_gemini_api_key()
        ai_enabled = ai_enabled and ai_runtime_ready
        celebrity_btn = self._frame_select_mode_buttons.get("celebrity")
        ai_btn = self._frame_select_mode_buttons.get("ai")
        celebrity_price = self._frame_select_mode_price_labels.get("celebrity")
        ai_price = self._frame_select_mode_price_labels.get("ai")
        if celebrity_btn is not None:
            celebrity_btn.setVisible(celebrity_enabled)
        if celebrity_price is not None:
            amount = layout_price_map.get(self._frame_select_mode_layout_id("celebrity"), default_price)
            try:
                amount_value = max(0, int(amount))
            except Exception:
                amount_value = default_price
            celebrity_price.setText(format_price(prefix, amount_value))
            celebrity_price.setVisible(celebrity_enabled)
        if ai_btn is not None:
            ai_btn.setVisible(ai_enabled)
        if ai_price is not None:
            amount = layout_price_map.get(self._frame_select_mode_layout_id("ai"), default_price)
            try:
                amount_value = max(0, int(amount))
            except Exception:
                amount_value = default_price
            ai_price.setText(format_price(prefix, amount_value))
            ai_price.setVisible(ai_enabled)
        if self._last_ai_runtime_ready is None or self._last_ai_runtime_ready != ai_runtime_ready:
            print(
                "[AI_MODE] frame_select ai_button "
                f"visible={1 if ai_enabled else 0} key_ready={1 if ai_runtime_ready else 0}"
            )
            self._last_ai_runtime_ready = ai_runtime_ready
        # Re-layout after text updates so width fits the current price text.
        self._layout_frame_select_mode_buttons()

    def _on_frame_select_mode_celebrity_clicked(self) -> None:
        self.ui_sound.play("click")
        self._suppress_nav_sound_until = time.monotonic() + 0.35
        if not bool(self.mode_settings.get("celebrity_enabled", DEFAULT_MODE_SETTINGS["celebrity_enabled"])):
            self._show_runtime_notice("유명인 합성모드가 비활성화되었습니다", duration_ms=1000)
            return
        print("[MODE] click celebrity -> goto celebrity_template_select")
        self.goto_screen("celebrity_template_select")

    def _on_frame_select_mode_ai_clicked(self) -> None:
        self.ui_sound.play("click")
        self._suppress_nav_sound_until = time.monotonic() + 0.35
        if not bool(self.mode_settings.get("ai_enabled", DEFAULT_MODE_SETTINGS["ai_enabled"])):
            self._show_runtime_notice("AI 합성모드는 비활성화되었습니다", duration_ms=1000)
            return
        if not self._is_ai_mode_runtime_ready(stage="mode_button", probe_once=True):
            self._block_ai_mode_missing_key(
                stage="mode_button",
                notice="AI 서버 키가 없어 사용할 수 없습니다",
            )
            self.goto_screen("frame_select")
            return
        print("[MODE] click ai -> goto ai_style_select")
        self.goto_screen("ai_style_select")

    def _apply_mode_settings(
        self,
        modes: dict,
        emit_log: bool = True,
        update_base: bool = True,
    ) -> None:
        self.mode_settings = self._normalize_modes_settings(modes)
        if update_base:
            self._base_mode_settings = dict(self.mode_settings)
        self._refresh_frame_select_mode_buttons()
        if emit_log:
            print(
                "[ADMIN] modes "
                f"celebrity_enabled={1 if self.mode_settings.get('celebrity_enabled') else 0} "
                f"ai_enabled={1 if self.mode_settings.get('ai_enabled') else 0}"
            )

    def _is_card_runtime_supported(self) -> bool:
        if self.is_test_mode():
            return True
        return self._env_bool(os.environ.get("KIOSK_CARD_RUNTIME_ENABLED", "0"), False)

    def _apply_payment_methods(self, payment_methods: dict, emit_log: bool = True) -> bool:
        normalized, forced_cash = self._normalize_payment_methods(payment_methods)
        if normalized.get("card", False) and not self._is_card_runtime_supported():
            normalized["card"] = False
            if not (normalized.get("cash", False) or normalized.get("coupon", False)):
                normalized["cash"] = True
                forced_cash = True
            print("[PAYMENT_POLICY] card disabled by runtime policy (KIOSK_CARD_RUNTIME_ENABLED=0)")
        self.payment_methods = normalized
        payment_screen = self.screens.get("payment_method")
        if isinstance(payment_screen, AppPaymentMethodScreen):
            payment_screen.apply_payment_methods(normalized)
        self._apply_payment_hotspot_overrides()
        if emit_log:
            print(
                "[ADMIN] payment_methods set "
                f"cash={1 if normalized['cash'] else 0} "
                f"card={1 if normalized['card'] else 0} "
                f"coupon={1 if normalized['coupon'] else 0}"
            )
        return forced_cash

    def _resolve_share_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("share") if isinstance(config, dict) else None
        result = dict(DEFAULT_SHARE_SETTINGS)
        if isinstance(raw, dict):
            page_url = raw.get("base_page_url")
            file_url = raw.get("base_file_url")
            api_base_url = raw.get("api_base_url")
            device_code = raw.get("device_code")
            device_token = raw.get("device_token")
            timeout_sec = raw.get("timeout_sec")
            if isinstance(page_url, str) and page_url.strip():
                result["base_page_url"] = page_url.strip().rstrip("/")
            if isinstance(file_url, str) and file_url.strip():
                result["base_file_url"] = file_url.strip().rstrip("/")
            if isinstance(api_base_url, str) and api_base_url.strip():
                result["api_base_url"] = _normalize_kiosk_api_base_url(api_base_url)
            if isinstance(device_code, str):
                result["device_code"] = device_code.strip()
            if isinstance(device_token, str):
                result["device_token"] = device_token.strip()
            if timeout_sec is not None:
                try:
                    timeout_value = float(timeout_sec)
                except Exception:
                    timeout_value = float(DEFAULT_SHARE_SETTINGS.get("timeout_sec", 12.0))
                result["timeout_sec"] = min(60.0, max(3.0, timeout_value))
        return result

    def _probe_device_credentials(
        self,
        *,
        api_base_url: str,
        device_code: str,
        device_token: str,
        timeout_sec: float = 8.0,
    ) -> tuple[bool, str]:
        if requests is None:
            return False, "requests 모듈이 없어 인증 검증을 할 수 없습니다."
        api_base = _normalize_kiosk_api_base_url(api_base_url)
        if not api_base:
            return False, "API 주소가 비어 있습니다."
        code = str(device_code or "").strip()
        token = str(device_token or "").strip()
        if not code or not token:
            return False, "디바이스 코드/토큰을 모두 입력하세요."
        url = f"{api_base}/kiosk/config"
        headers = {
            "X-Device-Code": code,
            "X-Device-Token": token,
        }
        try:
            resp = requests.get(url, headers=headers, timeout=max(3.0, min(20.0, float(timeout_sec))))
        except Exception as exc:
            return False, f"서버 연결 실패: {exc}"
        if int(resp.status_code) == 200:
            return True, "OK"
        if int(resp.status_code) == 401:
            return False, "인증 실패: 코드/토큰이 올바르지 않습니다."
        body = ""
        try:
            body = str(resp.text or "").strip()
        except Exception:
            body = ""
        if len(body) > 200:
            body = body[:200] + "..."
        return False, f"인증 실패: HTTP {resp.status_code} {body}".strip()

    def _is_bundled_default_device_credentials(self, device_code: str, device_token: str) -> bool:
        if not getattr(sys, "frozen", False):
            return False
        code = str(device_code or "").strip()
        token = str(device_token or "").strip()
        if not code or not token:
            return False
        bundled_path = ROOT_DIR / "config" / "config.json"
        if not bundled_path.is_file():
            return False
        try:
            raw = json.loads(bundled_path.read_text(encoding="utf-8-sig"))
        except Exception:
            return False
        share = raw.get("share") if isinstance(raw, dict) else None
        if not isinstance(share, dict):
            return False
        bundled_code = str(share.get("device_code", "")).strip()
        bundled_token = str(share.get("device_token", "")).strip()
        if not bundled_code or not bundled_token:
            return False
        return code == bundled_code and token == bundled_token

    @staticmethod
    def _normalize_path_token(path: Path) -> str:
        try:
            return str(Path(path).resolve(strict=False)).strip().lower().replace("/", "\\")
        except Exception:
            return str(path).strip().lower().replace("/", "\\")

    @staticmethod
    def _current_runtime_machine_id() -> str:
        host = str(os.environ.get("COMPUTERNAME", "") or socket.gethostname() or "").strip().lower()
        try:
            mac = f"{uuid.getnode():012x}"
        except Exception:
            mac = ""
        seed = f"{host}|{mac}"
        if not seed.strip("|"):
            return ""
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    def _is_preferred_runtime_config_path(self, config_path: Path) -> bool:
        target = self._normalize_path_token(config_path)
        for root in _preferred_runtime_data_dirs():
            try:
                candidate = self._normalize_path_token(root / "config" / "config.json")
                if target == candidate:
                    return True
            except Exception:
                continue
        return False

    def _is_untrusted_runtime_credential_source(self, device_code: str, device_token: str) -> bool:
        if not getattr(sys, "frozen", False):
            return False
        code = str(device_code or "").strip()
        token = str(device_token or "").strip()
        if not code or not token:
            return False
        config = self._read_config_dict()
        share = config.get("share") if isinstance(config, dict) else None
        if not isinstance(share, dict):
            return True
        trusted_path = str(share.get("runtime_trusted_config_path", "")).strip()
        if not trusted_path:
            return True
        if self._normalize_path_token(Path(trusted_path)) != self._normalize_path_token(self.config_path):
            return True
        trusted_machine = str(share.get("runtime_machine_id", "")).strip().lower()
        current_machine = str(self._current_runtime_machine_id() or "").strip().lower()
        if not trusted_machine or not current_machine:
            return True
        if trusted_machine != current_machine:
            return True
        return False

    def _persist_device_credentials(
        self,
        *,
        api_base_url: str,
        device_code: str,
        device_token: str,
    ) -> None:
        config = self._read_config_dict()
        share = config.get("share") if isinstance(config.get("share"), dict) else {}
        share = dict(share)
        normalized_api = _normalize_kiosk_api_base_url(api_base_url)
        if normalized_api:
            share["api_base_url"] = normalized_api
            try:
                split = urlsplit(normalized_api)
                if split.scheme and split.netloc:
                    base = f"{split.scheme}://{split.netloc}"
                    share["base_page_url"] = f"{base}/s"
                    share["base_file_url"] = f"{base}/s"
            except Exception:
                pass
        share["device_code"] = str(device_code or "").strip()
        share["device_token"] = str(device_token or "").strip()
        share["runtime_trusted_config_path"] = str(self.config_path)
        share["runtime_machine_id"] = str(self._current_runtime_machine_id() or "").strip()
        share["runtime_trusted_at"] = datetime.now().isoformat(timespec="seconds")
        config["share"] = share
        self._write_config_dict_atomic(config)
        trusted_after_write = str(self.config_path)
        if str(share.get("runtime_trusted_config_path", "")).strip() != trusted_after_write:
            share["runtime_trusted_config_path"] = trusted_after_write
            share["runtime_trusted_at"] = datetime.now().isoformat(timespec="seconds")
            config["share"] = share
            self._write_config_dict_atomic(config)
        self.share_settings = self._resolve_share_settings()

    def _show_device_registration_dialog(
        self,
        *,
        reason: str,
        api_base_url: str,
        device_code: str,
        device_token: str,
    ) -> Optional[dict[str, str]]:
        dialog = QDialog(self)
        dialog.setWindowTitle("디바이스 등록 / Device Registration")
        dialog.setModal(True)
        dialog.setMinimumWidth(620)

        root_layout = QVBoxLayout(dialog)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(10)

        title = QLabel("최초 1회 디바이스 인증이 필요합니다.\nDevice token setup is required.", dialog)
        title.setWordWrap(True)
        root_layout.addWidget(title)

        status = QLabel(reason or "", dialog)
        status.setWordWrap(True)
        status.setStyleSheet("color:#b00020;")
        root_layout.addWidget(status)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        api_input = QLineEdit(dialog)
        api_input.setText(str(api_base_url or "").strip())
        api_input.setPlaceholderText("https://api.viorafilm.com/api")
        form.addRow("API Base URL", api_input)

        code_input = QLineEdit(dialog)
        code_input.setText(str(device_code or "").strip())
        code_input.setPlaceholderText("예: KIOSK001")
        form.addRow("Device Code", code_input)

        token_input = QLineEdit(dialog)
        token_input.setText(str(device_token or "").strip())
        token_input.setPlaceholderText("발급받은 1회 토큰")
        try:
            token_input.setEchoMode(QLineEdit.EchoMode.Password)
        except Exception:
            pass
        form.addRow("Device Token", token_input)

        root_layout.addLayout(form)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        exit_btn = QPushButton("종료 / Exit", dialog)
        verify_btn = QPushButton("검증 후 저장 / Verify & Save", dialog)
        button_row.addWidget(exit_btn)
        button_row.addWidget(verify_btn)
        root_layout.addLayout(button_row)

        result: dict[str, str] = {}

        def _verify() -> None:
            api_base = str(api_input.text() or "").strip()
            code = str(code_input.text() or "").strip()
            token = str(token_input.text() or "").strip()
            ok, message = self._probe_device_credentials(
                api_base_url=api_base,
                device_code=code,
                device_token=token,
                timeout_sec=8.0,
            )
            if not ok:
                status.setText(message)
                return
            result["api_base_url"] = api_base
            result["device_code"] = code
            result["device_token"] = token
            dialog.accept()

        verify_btn.clicked.connect(_verify)
        exit_btn.clicked.connect(dialog.reject)

        exec_fn = getattr(dialog, "exec", None) or getattr(dialog, "exec_", None)
        if not callable(exec_fn):
            return None
        accepted = int(exec_fn()) == int(getattr(QDialog, "Accepted", 1))
        if not accepted:
            return None
        return result if result else None

    def _ensure_device_registration_or_raise(self) -> None:
        api_base = str(self.share_settings.get("api_base_url", DEFAULT_SHARE_SETTINGS.get("api_base_url", ""))).strip()
        code = str(self.share_settings.get("device_code", "")).strip()
        token = str(self.share_settings.get("device_token", "")).strip()
        force_dialog = self._env_bool(os.environ.get("KIOSK_FORCE_DEVICE_AUTH", "0"), False)

        if force_dialog:
            ok = False
            reason = "환경변수(KIOSK_FORCE_DEVICE_AUTH=1)로 재등록이 강제되었습니다."
            print("[DEVICE_AUTH] force registration requested by env")
        elif self._is_bundled_default_device_credentials(code, token):
            ok = False
            reason = "새 설치 장비 등록이 필요합니다. 디바이스 코드/토큰을 입력하세요."
            print("[DEVICE_AUTH] bundled default credentials detected -> force registration")
        elif self._is_untrusted_runtime_credential_source(code, token):
            ok = False
            reason = "사용자 경로의 기존 인증정보가 감지되어 재등록이 필요합니다."
            print(
                "[DEVICE_AUTH] untrusted runtime credential source detected "
                f'config="{self.config_path}" -> force registration'
            )
        else:
            ok, reason = self._probe_device_credentials(
                api_base_url=api_base,
                device_code=code,
                device_token=token,
                timeout_sec=6.0,
            )
        if ok:
            print(f"[DEVICE_AUTH] startup credentials verified code={code} config={self.config_path}")
            return

        print(f"[DEVICE_AUTH] startup verification failed: {reason} config={self.config_path}")
        while True:
            entered = self._show_device_registration_dialog(
                reason=reason,
                api_base_url=api_base or str(DEFAULT_SHARE_SETTINGS.get("api_base_url", "")).strip(),
                device_code=code,
                device_token=token,
            )
            if not isinstance(entered, dict):
                raise RuntimeError("device registration canceled")
            api_base = str(entered.get("api_base_url", "")).strip()
            code = str(entered.get("device_code", "")).strip()
            token = str(entered.get("device_token", "")).strip()
            ok, reason = self._probe_device_credentials(
                api_base_url=api_base,
                device_code=code,
                device_token=token,
                timeout_sec=8.0,
            )
            if ok:
                self._persist_device_credentials(
                    api_base_url=api_base,
                    device_code=code,
                    device_token=token,
                )
                print(f"[DEVICE_AUTH] registered code={code}")
                return

    def _normalize_printing_settings(self, raw_settings: object) -> dict:
        result = {
            "enabled": bool(DEFAULT_PRINTING_SETTINGS["enabled"]),
            "dry_run": bool(DEFAULT_PRINTING_SETTINGS["dry_run"]),
            "printers": {
                "DS620": {
                    "win_name": str(DEFAULT_PRINTING_SETTINGS["printers"]["DS620"]["win_name"]),
                    "form_4x6": str(DEFAULT_PRINTING_SETTINGS["printers"]["DS620"]["form_4x6"]),
                    "form_2x6": str(DEFAULT_PRINTING_SETTINGS["printers"]["DS620"]["form_2x6"]),
                },
                "DS620_STRIP": {
                    "win_name": str(DEFAULT_PRINTING_SETTINGS["printers"]["DS620_STRIP"]["win_name"]),
                    "form_4x6": str(DEFAULT_PRINTING_SETTINGS["printers"]["DS620_STRIP"]["form_4x6"]),
                    "form_2x6": str(DEFAULT_PRINTING_SETTINGS["printers"]["DS620_STRIP"]["form_2x6"]),
                },
                "RX1HS": {
                    "win_name": str(DEFAULT_PRINTING_SETTINGS["printers"]["RX1HS"]["win_name"]),
                    "form_4x6": str(DEFAULT_PRINTING_SETTINGS["printers"]["RX1HS"]["form_4x6"]),
                    "form_2x6": str(DEFAULT_PRINTING_SETTINGS["printers"]["RX1HS"]["form_2x6"]),
                },
            },
            "default_model": str(DEFAULT_PRINTING_SETTINGS["default_model"]),
        }
        if not isinstance(raw_settings, dict):
            return result

        result["enabled"] = self._as_bool(raw_settings.get("enabled"), result["enabled"])
        result["dry_run"] = self._as_bool(raw_settings.get("dry_run"), result["dry_run"])

        raw_printers = raw_settings.get("printers")
        if isinstance(raw_printers, dict):
            for model in ("DS620", "DS620_STRIP", "RX1HS"):
                item = raw_printers.get(model)
                if isinstance(item, dict):
                    win_name = str(item.get("win_name", result["printers"][model]["win_name"])).strip()
                    form_4x6 = str(item.get("form_4x6", result["printers"][model]["form_4x6"])).strip()
                    form_2x6 = str(item.get("form_2x6", result["printers"][model]["form_2x6"])).strip()
                    if win_name:
                        result["printers"][model]["win_name"] = win_name
                    if form_4x6:
                        result["printers"][model]["form_4x6"] = form_4x6
                    if form_2x6:
                        result["printers"][model]["form_2x6"] = form_2x6

        default_model = str(raw_settings.get("default_model", result["default_model"])).strip().upper()
        result["default_model"] = default_model if default_model in {"DS620", "RX1HS"} else "DS620"
        return result

    def _resolve_printing_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("printing") if isinstance(config, dict) else None
        return self._normalize_printing_settings(raw)

    @staticmethod
    def _get_configured_gemini_api_key(config: object) -> str:
        if not isinstance(config, dict):
            return ""
        ai_section = config.get("ai") if isinstance(config.get("ai"), dict) else {}
        admin_section = config.get("admin") if isinstance(config.get("admin"), dict) else {}
        for candidate in (
            config.get("gemini_api_key"),
            config.get("google_api_key"),
            ai_section.get("gemini_api_key"),
            ai_section.get("google_api_key"),
            admin_section.get("gemini_api_key"),
            admin_section.get("google_api_key"),
        ):
            text = str(candidate or "").strip()
            if text:
                return text
        return ""

    @staticmethod
    def _set_configured_gemini_api_key(config: dict, api_key: str) -> bool:
        key = str(api_key or "").strip()
        if not key:
            return False
        current = str(config.get("gemini_api_key", "")).strip()
        if current == key:
            return False
        config["gemini_api_key"] = key
        return True

    def _apply_server_gemini_api_key(self, config_payload: object, trigger: str) -> bool:
        key = self._get_configured_gemini_api_key(config_payload)
        if not key:
            print(f"[AI] gemini api_key missing from server trigger={trigger}")
            return False

        changed = False
        env_key = str(os.environ.get("GEMINI_API_KEY", "")).strip()
        if env_key != key:
            os.environ["GEMINI_API_KEY"] = key
            changed = True

        config = self._read_config_dict()
        if not isinstance(config, dict):
            config = {}
        if self._set_configured_gemini_api_key(config, key):
            try:
                self._write_config_dict_atomic(config)
                changed = True
                print(
                    f"[AI] gemini api_key synced from server trigger={trigger} "
                    f"path={self.config_path}"
                )
            except Exception as exc:
                print(f"[AI] gemini api_key sync failed trigger={trigger} err={exc}")
        elif changed:
            print(f"[AI] gemini api_key set from server env trigger={trigger}")
        return changed

    def _has_runtime_gemini_api_key(self) -> bool:
        env_key = str(
            os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        ).strip()
        if env_key:
            return True
        config = self._read_config_dict()
        return bool(self._get_configured_gemini_api_key(config))

    def _sync_gemini_api_key_from_server_once(self, stage: str) -> bool:
        ok, msg = self._probe_server_lock_state()
        ready = self._has_runtime_gemini_api_key()
        print(
            f"[AI] key probe stage={stage} ok={1 if ok else 0} "
            f"key_ready={1 if ready else 0} msg={str(msg or '').strip()}"
        )
        return ok

    def _is_ai_mode_runtime_ready(self, stage: str, probe_once: bool = True) -> bool:
        if self._has_runtime_gemini_api_key():
            return True
        print(f"[AI] key missing stage={stage} local=0")
        if probe_once:
            self._sync_gemini_api_key_from_server_once(stage=stage)
        return self._has_runtime_gemini_api_key()

    def _clear_ai_mode_runtime_state(self) -> None:
        self.compose_mode = "normal"
        self.ai_style_id = None
        self.current_layout_id = None
        self.layout_id = None
        self.current_capture_slots = 0
        self.current_print_slots = 0
        self.current_captured_paths = []
        self.selected_print_paths = []
        self.ai_selected_source_paths = []
        self.current_design_index = None
        self.current_design_path = None
        self.current_design_is_gray = False
        self.current_design_flip_horizontal = False
        self.current_design_qr_enabled = True
        self.current_print_path = None
        self.current_print_job_path = None

    def _block_ai_mode_missing_key(self, stage: str, notice: str) -> None:
        print(f"[AI_MODE] ai_blocked:key_missing stage={stage}")
        self._clear_ai_mode_runtime_state()
        self._show_runtime_notice(notice, duration_ms=1300)

    @classmethod
    def _printer_name_matches_model(cls, model: str, printer_name: str) -> bool:
        token = cls._normalize_printer_name_token(printer_name)
        if not token:
            return False
        model_key = str(model or "").strip().upper()
        if model_key == "DS620":
            return "ds620" in token and "strip" not in token
        if model_key == "DS620_STRIP":
            return "strip" in token and ("ds620" in token or "rx1" in token)
        if model_key == "RX1HS":
            return ("rx1hs" in token or "dsrx1" in token or "rx1" in token) and ("strip" not in token)
        return False

    def _detect_auto_printer_mapping(self, installed_names: list[str]) -> dict[str, str]:
        mapped = {"DS620": "", "DS620_STRIP": "", "RX1HS": ""}
        physical = [name for name in (installed_names or []) if not self._is_virtual_printer_name(name)]
        for name in physical:
            token = self._normalize_printer_name_token(name)
            if not token:
                continue
            if "strip" in token and ("ds620" in token or "rx1" in token):
                if not mapped["DS620_STRIP"]:
                    mapped["DS620_STRIP"] = name
                continue
            if "ds620" in token and not mapped["DS620"]:
                mapped["DS620"] = name
                continue
            if ("rx1hs" in token or "dsrx1" in token or "rx1" in token) and not mapped["RX1HS"]:
                mapped["RX1HS"] = name
                continue
        return mapped

    def _should_auto_replace_printer(self, model: str, current_name: str, installed_names: list[str]) -> bool:
        name = str(current_name or "").strip()
        if not name:
            return True
        if not self._is_installed_printer_name(name, installed_names):
            return True
        if self._is_virtual_printer_name(name):
            return True
        if not self._printer_name_matches_model(model, name):
            return True
        return False

    def _apply_startup_runtime_defaults(self) -> None:
        config = self._read_config_dict()
        if not isinstance(config, dict):
            config = {}
        changed = False

        env_key = str(os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")).strip()
        config_key = self._get_configured_gemini_api_key(config)
        startup_key = env_key or config_key
        if startup_key:
            if not env_key:
                os.environ["GEMINI_API_KEY"] = startup_key
            if env_key and not config_key:
                if self._set_configured_gemini_api_key(config, startup_key):
                    changed = True
                    print("[AI] startup default gemini api_key applied")
        else:
            print("[AI] startup gemini api_key missing -> waiting for server config")

        printing = self._normalize_printing_settings(config.get("printing"))
        installed = self.list_windows_printers()
        auto_map = self._detect_auto_printer_mapping(installed)
        printers = printing.get("printers", {}) if isinstance(printing.get("printers"), dict) else {}

        for model_key in ("DS620", "DS620_STRIP", "RX1HS"):
            item = printers.get(model_key, {}) if isinstance(printers.get(model_key), dict) else {}
            current_name = str(item.get("win_name", "")).strip()
            detected_name = str(auto_map.get(model_key, "")).strip()
            if detected_name and self._should_auto_replace_printer(model_key, current_name, installed):
                item["win_name"] = detected_name
                printers[model_key] = item
                changed = True
                print(
                    f"[PRINT_AUTO] mapped model={model_key} "
                    f"from=\"{current_name}\" to=\"{detected_name}\""
                )

        ds620_ready = bool(str(printers.get("DS620", {}).get("win_name", "")).strip()) if isinstance(printers.get("DS620"), dict) else False
        rx1hs_ready = bool(str(printers.get("RX1HS", {}).get("win_name", "")).strip()) if isinstance(printers.get("RX1HS"), dict) else False
        current_default = str(printing.get("default_model", "DS620")).strip().upper()
        desired_default = current_default if current_default in {"DS620", "RX1HS"} else "DS620"
        if ds620_ready and not rx1hs_ready:
            desired_default = "DS620"
        elif rx1hs_ready and not ds620_ready:
            desired_default = "RX1HS"
        if desired_default != current_default:
            printing["default_model"] = desired_default
            changed = True
            print(f"[PRINT_AUTO] default_model {current_default}->{desired_default}")

        printing["printers"] = printers
        config["printing"] = printing

        if changed:
            try:
                self._write_config_dict_atomic(config)
                print(f"[STARTUP] runtime defaults saved config={self.config_path}")
            except Exception as exc:
                print(f"[STARTUP] runtime defaults save failed: {exc}")

        self.printing_settings = self._normalize_printing_settings(config.get("printing"))

    def _normalize_pricing_settings(
        self,
        raw_settings: object,
        legacy_settings: object = None,
        layout_ids: Optional[list[str]] = None,
    ) -> dict:
        result = {
            "currency_prefix": str(DEFAULT_PRICING_SETTINGS["currency_prefix"]),
            "default_price": int(DEFAULT_PRICING_SETTINGS["default_price"]),
            "layouts": {},
        }

        def _read_layout_map(obj: object) -> dict[str, int]:
            mapped: dict[str, int] = {}
            if not isinstance(obj, dict):
                return mapped
            for key, value in obj.items():
                layout_key = str(key).strip()
                if not layout_key:
                    continue
                try:
                    amount = int(value)
                except Exception:
                    continue
                mapped[layout_key] = max(0, amount)
            return mapped

        source = raw_settings if isinstance(raw_settings, dict) else {}
        legacy = legacy_settings if isinstance(legacy_settings, dict) else {}

        prefix = source.get("currency_prefix")
        if isinstance(prefix, str):
            result["currency_prefix"] = prefix.strip()

        try:
            default_price = int(source.get("default_price", result["default_price"]))
        except Exception:
            default_price = int(result["default_price"])
        if not isinstance(raw_settings, dict):
            try:
                default_price = int(legacy.get("default_price", default_price))
            except Exception:
                pass
        result["default_price"] = max(0, default_price)

        layouts = _read_layout_map(source.get("layouts"))
        if not layouts and isinstance(legacy, dict):
            layouts = _read_layout_map(legacy.get("pricing_by_layout"))

        detected = list(layout_ids or [])
        if not detected:
            detected = self._pricing_layout_ids_with_modes(self.available_layout_ids)
        for layout_id in detected:
            if layout_id not in layouts:
                layouts[layout_id] = int(result["default_price"])

        result["layouts"] = layouts
        return result

    def _resolve_payment_pricing_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("pricing") if isinstance(config, dict) else None
        legacy = config.get("payment_pricing") if isinstance(config, dict) else None
        raw_celebrity = config.get("celebrity") if isinstance(config, dict) else None
        celebrity_layout = ""
        if isinstance(raw_celebrity, dict):
            celebrity_layout = str(
                raw_celebrity.get("layout_id", DEFAULT_CELEBRITY_SETTINGS["layout_id"])
            ).strip()
        layout_ids = self._pricing_layout_ids_with_modes(
            self.available_layout_ids,
            celebrity_layout_id=celebrity_layout,
        )
        return self._normalize_pricing_settings(raw, legacy, layout_ids=layout_ids)

    def _resolve_coupon_value_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("coupons") if isinstance(config, dict) else None
        result = {
            "default_coupon_value": int(DEFAULT_COUPON_VALUE_SETTINGS["default_coupon_value"]),
            "values": dict(DEFAULT_COUPON_VALUE_SETTINGS["values"]),
        }
        if isinstance(raw, dict):
            try:
                default_value = int(raw.get("default_coupon_value", result["default_coupon_value"]))
            except Exception:
                default_value = int(result["default_coupon_value"])
            result["default_coupon_value"] = max(0, default_value)
            raw_values = raw.get("values")
            if isinstance(raw_values, dict):
                normalized: dict[str, int] = {}
                for key, value in raw_values.items():
                    code_key = str(key).strip()
                    if not code_key:
                        continue
                    try:
                        amount = int(value)
                    except Exception:
                        continue
                    normalized[code_key] = max(0, amount)
                result["values"] = normalized
        return result

    def _resolve_coupon_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("coupon") if isinstance(config, dict) else None
        result = dict(DEFAULT_COUPON_SETTINGS)
        if isinstance(raw, dict):
            result["enabled"] = self._as_bool(raw.get("enabled"), bool(DEFAULT_COUPON_SETTINGS["enabled"]))
            try:
                length = int(raw.get("length", DEFAULT_COUPON_SETTINGS["length"]))
            except Exception:
                length = int(DEFAULT_COUPON_SETTINGS["length"])
            result["length"] = max(1, min(12, length))
            result["accept_any_in_test"] = self._as_bool(
                raw.get("accept_any_in_test"),
                bool(DEFAULT_COUPON_SETTINGS["accept_any_in_test"]),
            )
            valid_codes = raw.get("valid_codes")
            if isinstance(valid_codes, list):
                codes: list[str] = []
                for code in valid_codes:
                    text = str(code).strip()
                    if text:
                        codes.append(text)
                result["valid_codes"] = codes
        return result

    def _resolve_gif_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("gif") if isinstance(config, dict) else None
        result = dict(DEFAULT_GIF_SETTINGS)
        if isinstance(raw, dict):
            result["enabled"] = self._as_bool(raw.get("enabled"), bool(DEFAULT_GIF_SETTINGS["enabled"]))
            try:
                frames_per_shot = int(raw.get("frames_per_shot", DEFAULT_GIF_SETTINGS["frames_per_shot"]))
            except Exception:
                frames_per_shot = int(DEFAULT_GIF_SETTINGS["frames_per_shot"])
            try:
                interval_ms = int(raw.get("interval_ms", DEFAULT_GIF_SETTINGS["interval_ms"]))
            except Exception:
                interval_ms = int(DEFAULT_GIF_SETTINGS["interval_ms"])
            try:
                max_width = int(raw.get("max_width", DEFAULT_GIF_SETTINGS["max_width"]))
            except Exception:
                max_width = int(DEFAULT_GIF_SETTINGS["max_width"])
            result["frames_per_shot"] = max(1, min(8, frames_per_shot))
            result["interval_ms"] = max(50, min(1000, interval_ms))
            result["max_width"] = max(64, min(1920, max_width))
        return result

    def _resolve_thank_you_settings(self) -> dict:
        config = self._read_config_dict()
        raw = config.get("thank_you") if isinstance(config, dict) else None
        result = dict(DEFAULT_THANK_YOU_SETTINGS)
        if isinstance(raw, dict):
            rect = raw.get("gif_rect")
            if isinstance(rect, list) and len(rect) == 4:
                try:
                    x = int(rect[0])
                    y = int(rect[1])
                    w = max(1, int(rect[2]))
                    h = max(1, int(rect[3]))
                    result["gif_rect"] = [x, y, w, h]
                except Exception:
                    pass
        return result

    def get_gif_settings(self) -> dict:
        return dict(self.gif_settings)

    def get_share_settings(self) -> dict:
        return dict(self.share_settings)

    def get_printing_settings(self) -> dict:
        printers = self.printing_settings.get("printers", {})
        ds620 = printers.get("DS620", {}) if isinstance(printers, dict) else {}
        ds620_strip = printers.get("DS620_STRIP", {}) if isinstance(printers, dict) else {}
        rx1hs = printers.get("RX1HS", {}) if isinstance(printers, dict) else {}
        return {
            "enabled": bool(self.printing_settings.get("enabled", True)),
            "dry_run": bool(self.printing_settings.get("dry_run", False)),
            "printers": {
                "DS620": {
                    "win_name": str(ds620.get("win_name", "")),
                    "form_4x6": str(ds620.get("form_4x6", "4x6")),
                    "form_2x6": str(ds620.get("form_2x6", "2x6")),
                },
                "DS620_STRIP": {
                    "win_name": str(ds620_strip.get("win_name", "")),
                    "form_4x6": str(ds620_strip.get("form_4x6", "4x6")),
                    "form_2x6": str(ds620_strip.get("form_2x6", "2x6")),
                },
                "RX1HS": {
                    "win_name": str(rx1hs.get("win_name", "")),
                    "form_4x6": str(rx1hs.get("form_4x6", "4x6")),
                    "form_2x6": str(rx1hs.get("form_2x6", "2x6")),
                },
            },
            "default_model": str(self.printing_settings.get("default_model", "DS620")),
        }

    @staticmethod
    def _normalize_printer_name_token(value: str) -> str:
        text = str(value or "").strip().lower()
        return re.sub(r"[^a-z0-9]+", "", text)

    @classmethod
    def _is_virtual_printer_name(cls, value: str) -> bool:
        token = cls._normalize_printer_name_token(value)
        if not token:
            return False
        virtual_tokens = (
            "microsoftprinttopdf",
            "microsoftxpsdocumentwriter",
            "onenoteforwindows10",
            "fax",
            "adobepdf",
            "pdfcreator",
            "printtopdf",
            "xpsdocumentwriter",
        )
        for marker in virtual_tokens:
            if marker in token:
                return True
        return False

    def _match_installed_printer_name(self, requested: str, model_hint: str = "") -> str:
        wanted = str(requested or "").strip()
        if not wanted:
            return ""

        names = self.list_windows_printers()
        if not names:
            return wanted

        # 1) Exact (case-sensitive / case-insensitive)
        for name in names:
            if name == wanted:
                return name
        wanted_low = wanted.lower()
        for name in names:
            if str(name).strip().lower() == wanted_low:
                return name

        # 2) Normalized exact: ignore spaces, '-', '_', etc.
        wanted_norm = self._normalize_printer_name_token(wanted)
        if wanted_norm:
            for name in names:
                if self._normalize_printer_name_token(name) == wanted_norm:
                    return name

        # 3) Fuzzy fallback scoring.
        hint = str(model_hint or "").strip().upper()
        best_name = ""
        best_score = -1.0
        for name in names:
            cand = str(name).strip()
            if not cand:
                continue
            cand_low = cand.lower()
            cand_norm = self._normalize_printer_name_token(cand)
            score = 0.0

            if wanted_low in cand_low:
                score += 35.0
            if cand_low in wanted_low:
                score += 20.0
            if wanted_norm and wanted_norm in cand_norm:
                score += 35.0
            if wanted_norm and cand_norm and cand_norm in wanted_norm:
                score += 15.0

            if hint in {"DS620", "DS620_STRIP"} and "ds620" in cand_low:
                score += 12.0
            if hint == "RX1HS" and ("rx1hs" in cand_low or "rx1" in cand_low):
                score += 12.0

            # Prefer closer names when fuzzy score ties.
            score -= abs(len(cand_low) - len(wanted_low)) * 0.2

            if score > best_score:
                best_score = score
                best_name = cand

        # Require a minimum confidence to avoid wrong routing.
        if best_name and best_score >= 25.0:
            return best_name
        return wanted

    def list_windows_printers(self) -> list[str]:
        try:
            import win32print

            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            entries = win32print.EnumPrinters(flags)
            names = sorted(
                set(
                    str(item[2]).strip()
                    for item in entries
                    if isinstance(item, (tuple, list)) and len(item) >= 3 and str(item[2]).strip()
                )
            )
            print(f"[ADMIN] printers found: {', '.join(names) if names else '(none)'}")
            return names
        except Exception as exc:
            print(f"[ADMIN] printers found: error {exc}")
            return []

    def list_printer_forms(self, printer_name: str) -> list[str]:
        name = str(printer_name or "").strip()
        if not name:
            return []
        handle = None
        try:
            import win32print

            handle = win32print.OpenPrinter(name)
            try:
                entries = win32print.EnumForms(handle, 1)
            except TypeError:
                entries = win32print.EnumForms(handle)
            except Exception:
                entries = []
            forms = sorted(
                {
                    str(item.get("Name", "")).strip()
                    for item in (entries or [])
                    if isinstance(item, dict) and str(item.get("Name", "")).strip()
                }
            )
            print(
                f"[ADMIN] forms printer=\"{name}\" found: "
                f"{', '.join(forms) if forms else '(none)'}"
            )
            return forms
        except Exception as exc:
            print(f"[ADMIN] forms printer=\"{name}\" error: {exc}")
            return []
        finally:
            if handle is not None:
                try:
                    import win32print

                    win32print.ClosePrinter(handle)
                except Exception:
                    pass

    def _candidate_runtime_log_dirs(self) -> list[Path]:
        dirs: list[Path] = []
        runtime_root = _default_runtime_data_dir()
        dirs.append(runtime_root / "logs")

        program_data = str(os.environ.get("PROGRAMDATA", "")).strip()
        if program_data:
            dirs.append(Path(program_data) / "ViorafilmKiosk" / "logs")

        public_root = str(os.environ.get("PUBLIC", "")).strip()
        if public_root:
            dirs.append(Path(public_root) / "Documents" / "ViorafilmKiosk" / "logs")

        temp_root = str(os.environ.get("TEMP", os.getcwd())).strip()
        if temp_root:
            dirs.append(Path(temp_root) / "ViorafilmKiosk" / "logs")

        dedup: list[Path] = []
        seen: set[str] = set()
        for item in dirs:
            key = str(item).strip().lower()
            if key and key not in seen:
                seen.add(key)
                dedup.append(item)
        return dedup

    def _candidate_runtime_log_markers(self) -> list[Path]:
        markers: list[Path] = []
        runtime_root = _default_runtime_data_dir()
        markers.append(runtime_root / "last_log_path.txt")
        markers.append(INSTALL_ROOT / "last_log_path.txt")

        program_data = str(os.environ.get("PROGRAMDATA", "")).strip()
        if program_data:
            markers.append(Path(program_data) / "ViorafilmKiosk" / "last_log_path.txt")

        public_root = str(os.environ.get("PUBLIC", "")).strip()
        if public_root:
            markers.append(Path(public_root) / "Documents" / "ViorafilmKiosk" / "last_log_path.txt")

        temp_root = str(os.environ.get("TEMP", os.getcwd())).strip()
        if temp_root:
            markers.append(Path(temp_root) / "ViorafilmKiosk" / "last_log_path.txt")
        return markers

    def get_runtime_log_file_path(self) -> str:
        global _LOG_FILE_PATH

        if isinstance(_LOG_FILE_PATH, Path):
            return str(_LOG_FILE_PATH)

        for marker in self._candidate_runtime_log_markers():
            try:
                if not marker.is_file():
                    continue
                raw = marker.read_text(encoding="utf-8").strip()
                if not raw:
                    continue
                p = Path(raw)
                if p.is_file():
                    return str(p)
                if p.parent.is_dir():
                    return str(p)
            except Exception:
                continue

        latest_file: Optional[Path] = None
        latest_mtime = -1.0
        for log_dir in self._candidate_runtime_log_dirs():
            try:
                if not log_dir.is_dir():
                    continue
                for path in log_dir.glob("kiosk_*.log"):
                    try:
                        mtime = float(path.stat().st_mtime)
                    except Exception:
                        continue
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_file = path
            except Exception:
                continue
        if latest_file is not None:
            return str(latest_file)
        return ""

    def open_runtime_log_folder(self) -> bool:
        log_file = self.get_runtime_log_file_path()
        folder = Path(log_file).parent if log_file else (_default_runtime_data_dir() / "logs")
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        try:
            if hasattr(os, "startfile"):
                os.startfile(str(folder))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            print(f"[ADMIN] open log folder path={folder}")
            return True
        except Exception as exc:
            print(f"[ADMIN] open log folder failed path={folder} err={exc}")
            return False

    def _show_runtime_notice(self, message: str, duration_ms: int = 1200) -> None:
        current = self.stack.currentWidget()
        if current is not None and hasattr(current, "show_notice"):
            try:
                current.show_notice(str(message), duration_ms=max(200, int(duration_ms)))
                return
            except Exception:
                pass
        print(f"[NOTICE] {message}")

    @staticmethod
    def _env_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return bool(default)

    @staticmethod
    def _parse_iso_to_ts(value: str) -> float:
        text = str(value or "").strip()
        if not text:
            return 0.0
        try:
            return float(datetime.fromisoformat(text).timestamp())
        except Exception:
            return 0.0

    @staticmethod
    def _format_duration_kr_en(total_seconds: float) -> str:
        sec = max(0, int(total_seconds))
        days, rem = divmod(sec, 86400)
        hours, rem = divmod(rem, 3600)
        minutes = rem // 60
        return f"{days}일 {hours}시간 {minutes}분 / {days}d {hours}h {minutes}m"

    @staticmethod
    def _iso_from_ts(ts_value: float) -> Optional[str]:
        if float(ts_value or 0.0) <= 0:
            return None
        try:
            return datetime.fromtimestamp(float(ts_value)).isoformat(timespec="seconds")
        except Exception:
            return None

    def _offline_telemetry_snapshot(self) -> dict[str, Any]:
        with self._license_state_lock:
            enabled = bool(self._offline_guard_enabled)
            grace_seconds = int(self._offline_grace_seconds)
            first_seen_ts = float(self._first_seen_ts or 0.0)
            last_online_ts = float(self._last_online_ts or 0.0)
            lock_active = bool(self._offline_lock_active)

        reference_ts = last_online_ts if last_online_ts > 0 else first_seen_ts
        reference_source = "last_online" if last_online_ts > 0 else "first_seen"
        remaining_seconds: Optional[int] = None
        if enabled and reference_ts > 0 and grace_seconds > 0:
            elapsed = max(0.0, time.time() - reference_ts)
            remaining_seconds = int(round(float(grace_seconds) - elapsed))
        elif not enabled:
            remaining_seconds = grace_seconds
        else:
            reference_source = "none"

        return {
            "offline_guard_enabled": enabled,
            "offline_lock_active": lock_active,
            "offline_grace_seconds": grace_seconds,
            "offline_grace_remaining_seconds": remaining_seconds,
            "offline_reference_source": reference_source,
            "offline_last_online_at": self._iso_from_ts(last_online_ts),
            "offline_first_seen_at": self._iso_from_ts(first_seen_ts),
        }

    def _load_license_state_unlocked(self) -> dict[str, Any]:
        path = Path(self._license_state_path)
        if not path.is_file():
            return {}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[LICENSE] state load failed path={path} err={exc}")
            return {}
        return loaded if isinstance(loaded, dict) else {}

    def _save_license_state_unlocked(self, state: dict[str, Any]) -> None:
        path = Path(self._license_state_path)
        payload = dict(state or {})
        payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(path, payload)
        except Exception as exc:
            self._switch_runtime_storage_to_fallback(f"license_state_write_failed:{exc}")
            fallback = Path(self._license_state_path)
            fallback.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(fallback, payload)

    def _compute_offline_guard_status(self) -> tuple[bool, str]:
        if not bool(self._offline_guard_enabled):
            return False, "offline guard disabled"

        last_online_ts = float(self._last_online_ts or 0.0)
        first_seen_ts = float(self._first_seen_ts or 0.0)
        reference_ts = last_online_ts if last_online_ts > 0 else first_seen_ts
        if reference_ts <= 0:
            return False, "license state unavailable"

        elapsed = max(0.0, time.time() - reference_ts)
        remaining = float(self._offline_grace_seconds) - elapsed
        if remaining > 0:
            return False, f"remaining={self._format_duration_kr_en(remaining)}"

        over = abs(remaining)
        base_line = (
            "마지막 온라인 인증 이후 제한 시간 초과"
            if last_online_ts > 0
            else "최초 실행 이후 온라인 인증 없이 제한 시간 초과"
        )
        lock_message = (
            f"{base_line}\n"
            "인터넷 미연결 시간이 제한(72시간)을 초과했습니다.\n"
            "Offline time limit exceeded.\n"
            f"초과 시간 / Overtime: {self._format_duration_kr_en(over)}"
        )
        return True, lock_message

    def _is_runtime_locked(self) -> bool:
        return bool(self._offline_lock_active or self._server_lock_active or self._ota_force_lock_active)

    def _current_runtime_lock_message(self) -> str:
        if self._server_lock_active:
            return str(self._server_lock_message or "").strip()
        if self._ota_force_lock_active:
            return str(self._ota_force_lock_message or "").strip()
        return str(self._offline_lock_message or "").strip()

    def _sync_runtime_lock_screen(self, trigger: str) -> None:
        active = self._is_runtime_locked()
        message = self._current_runtime_lock_message()
        lock_screen = self.screens.get("offline_locked")
        if isinstance(lock_screen, OfflineLockScreen):
            lock_screen.set_lock_message(message)

        current = self.stack.currentWidget()
        current_name = getattr(current, "screen_name", "")
        if active:
            if current_name not in {"offline_locked", "admin"} and isinstance(lock_screen, OfflineLockScreen):
                self.stack.setCurrentWidget(lock_screen)
                print(f"[NAV] runtime_lock({trigger}) -> offline_locked")
            return

        if current_name == "offline_locked":
            self.goto_screen("start")

    def _build_server_lock_message(self, reason: str, locked_at: str) -> str:
        reason_text = str(reason or "").strip() or "-"
        locked_text = str(locked_at or "").strip() or "-"
        return (
            "관리자에 의해 장치가 잠금되었습니다.\n"
            "This kiosk has been locked by administrator.\n"
            f"사유 / Reason: {reason_text}\n"
            f"잠금시각 / Locked At: {locked_text}"
        )

    def _set_server_lock(self, active: bool, message: str, trigger: str) -> None:
        was_active = bool(self._server_lock_active)
        self._server_lock_active = bool(active)
        self._server_lock_message = str(message or "").strip()
        if self._server_lock_active and not was_active:
            print(f"[SERVER_LOCK] LOCKED trigger={trigger} msg={self._server_lock_message}")
        if not self._server_lock_active and was_active:
            print(f"[SERVER_LOCK] UNLOCKED trigger={trigger}")
        self._sync_runtime_lock_screen(trigger=f"server:{trigger}")

    def _on_server_lock_signal(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        active = bool(payload.get("locked", False))
        reason = str(payload.get("lock_reason", "")).strip()
        locked_at = str(payload.get("locked_at", "")).strip()
        trigger = str(payload.get("trigger", "signal")).strip() or "signal"
        message = self._build_server_lock_message(reason, locked_at) if active else ""
        self._set_server_lock(active, message, trigger)

    def _on_server_mode_permissions_signal(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        permissions = payload.get("permissions") if isinstance(payload.get("permissions"), dict) else payload
        if not isinstance(permissions, dict):
            return
        base_modes = self._normalize_modes_settings(
            self._base_mode_settings if isinstance(getattr(self, "_base_mode_settings", None), dict) else self.mode_settings
        )
        allow_celebrity = bool(permissions.get("allow_celebrity_mode", True))
        allow_ai = bool(permissions.get("allow_ai_mode", True))
        effective_modes = {
            "celebrity_enabled": bool(base_modes.get("celebrity_enabled", False)) and allow_celebrity,
            "ai_enabled": bool(base_modes.get("ai_enabled", False)) and allow_ai,
        }
        current_modes = self._normalize_modes_settings(self.mode_settings)
        if effective_modes == current_modes:
            return
        self._apply_mode_settings(effective_modes, emit_log=False, update_base=False)
        print(
            "[SERVER_MODES] applied "
            f"celebrity_enabled={1 if effective_modes.get('celebrity_enabled') else 0} "
            f"ai_enabled={1 if effective_modes.get('ai_enabled') else 0} "
            f"(allow_celebrity={1 if allow_celebrity else 0} allow_ai={1 if allow_ai else 0})"
        )

    def _apply_server_lock_payload(self, payload: Any, trigger: str) -> None:
        if not isinstance(payload, dict):
            return
        event = {
            "locked": bool(payload.get("locked", False)),
            "lock_reason": str(payload.get("lock_reason", "")).strip(),
            "locked_at": str(payload.get("locked_at", "")).strip(),
            "trigger": str(trigger or "api"),
        }
        try:
            if QThread.currentThread() == self.thread():
                self._on_server_lock_signal(event)
            else:
                self.server_lock_signal.emit(event)
        except Exception:
            self.server_lock_signal.emit(event)

    def _build_ota_force_lock_message(
        self,
        target_version: str,
        min_supported_version: str,
        notes: str,
    ) -> str:
        target = str(target_version or "").strip() or "-"
        minimum = str(min_supported_version or "").strip() or "-"
        note_text = str(notes or "").strip()
        lines = [
            "필수 업데이트가 필요합니다.",
            "Mandatory update is required.",
            f"목표 버전 / Target Version: {target}",
            f"최소 지원 버전 / Min Supported: {minimum}",
        ]
        if note_text:
            lines.append(f"안내 / Notes: {note_text}")
        lines.append("관리자에게 문의 후 업데이트를 진행해주세요.")
        lines.append("Please contact admin and apply update.")
        return "\n".join(lines)

    def _set_ota_force_lock(self, active: bool, message: str, target_version: str, trigger: str) -> None:
        was_active = bool(self._ota_force_lock_active)
        self._ota_force_lock_active = bool(active)
        self._ota_force_lock_message = str(message or "").strip()
        self._ota_target_version = str(target_version or "").strip()
        if self._ota_force_lock_active and not was_active:
            print(
                f"[OTA] FORCE_LOCK trigger={trigger} target={self._ota_target_version or '-'} "
                f"msg={self._ota_force_lock_message}"
            )
        if not self._ota_force_lock_active and was_active:
            print(f"[OTA] FORCE_UNLOCK trigger={trigger}")
        self._sync_runtime_lock_screen(trigger=f"ota:{trigger}")

    def _on_ota_state_signal(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        active = bool(payload.get("active", False))
        message = str(payload.get("message", "")).strip()
        target_version = str(payload.get("target_version", "")).strip()
        update_available = bool(payload.get("update_available", False))
        force_update = bool(payload.get("force_update", False))
        current_version = str(payload.get("current_version", "")).strip()
        error = str(payload.get("error", "")).strip()
        signature = "|".join(
            [
                "1" if active else "0",
                "1" if update_available else "0",
                "1" if force_update else "0",
                target_version,
                current_version,
                error,
            ]
        )
        if signature != self._ota_last_state_signature:
            self._ota_last_state_signature = signature
            if error:
                print(f"[OTA] check fail: {error}")
            else:
                print(
                    f"[OTA] check ok current={current_version or '-'} target={target_version or '-'} "
                    f"update={1 if update_available else 0} force={1 if force_update else 0}"
                )
        self._set_ota_force_lock(active, message, target_version, trigger="check")
        self._ota_try_auto_download(payload)

    def _resolve_ota_download_dir(self) -> Path:
        raw = str(os.environ.get("KIOSK_OTA_DOWNLOAD_DIR", "")).strip()
        if not raw:
            return _resolve_runtime_out_dir() / "updates"
        path = Path(raw)
        if not path.is_absolute():
            base = _default_runtime_data_dir() if getattr(sys, "frozen", False) else ROOT_DIR
            path = (base / path).resolve()
        return path

    def _resolve_ota_state_path(self) -> Path:
        raw = str(os.environ.get("KIOSK_OTA_STATE_PATH", "")).strip()
        if not raw:
            return _resolve_runtime_out_dir() / "ota_state.json"
        path = Path(raw)
        if not path.is_absolute():
            base = _default_runtime_data_dir() if getattr(sys, "frozen", False) else ROOT_DIR
            path = (base / path).resolve()
        return path

    def _load_kiosk_app_version(self) -> str:
        env_version = str(os.environ.get("KIOSK_APP_VERSION", "kiosk-local")).strip() or "kiosk-local"
        path = Path(self._ota_state_path)
        if not path.is_file():
            return env_version
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return env_version
        if not isinstance(payload, dict):
            return env_version
        persisted = str(payload.get("current_version", "")).strip()
        if persisted:
            return persisted
        return env_version

    def _persist_kiosk_app_version(self, version: str, source: str = "ota") -> None:
        ver = str(version or "").strip()
        if not ver:
            return
        self._kiosk_app_version = ver
        payload = {
            "current_version": ver,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "source": str(source or "ota"),
        }
        path = Path(self._ota_state_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(path, payload)
        except Exception as exc:
            self._switch_runtime_storage_to_fallback(f"ota_state_write_failed:{exc}")
            fallback = Path(self._ota_state_path)
            fallback.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(fallback, payload)
        print(f"[OTA] version state updated current={ver} source={source}")

    def _current_kiosk_app_version(self) -> str:
        version = str(getattr(self, "_kiosk_app_version", "") or "").strip()
        if version:
            return version
        return str(os.environ.get("KIOSK_APP_VERSION", "kiosk-local")).strip() or "kiosk-local"

    @staticmethod
    def _sanitize_ota_filename(name: str, fallback: str = "kiosk_update.bin") -> str:
        text = str(name or "").strip()
        if not text:
            return fallback
        base = Path(text).name
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
        if not safe:
            return fallback
        return safe

    @staticmethod
    def _ota_filename_from_headers(content_disposition: str, content_type: str) -> str:
        cd = str(content_disposition or "").strip()
        ct = str(content_type or "").lower()
        filename = ""

        # RFC5987: filename*=UTF-8''encoded-name.zip
        if "filename*=" in cd:
            try:
                part = cd.split("filename*=", 1)[1].split(";", 1)[0].strip().strip('"').strip("'")
                if "''" in part:
                    part = part.split("''", 1)[1]
                filename = unquote(part).strip()
            except Exception:
                filename = ""

        if not filename and "filename=" in cd:
            try:
                part = cd.split("filename=", 1)[1].split(";", 1)[0].strip().strip('"').strip("'")
                filename = unquote(part).strip()
            except Exception:
                filename = ""

        if filename:
            return filename

        # Content-Type fallback
        if "application/zip" in ct or "x-zip" in ct:
            return "update.zip"
        if "application/x-msdownload" in ct or "application/vnd.microsoft.portable-executable" in ct:
            return "update.exe"
        return ""

    def _ota_try_auto_download(self, payload: dict[str, Any]) -> None:
        if not self._ota_auto_download_enabled:
            return
        if requests is None:
            return
        if not bool(payload.get("update_available", False)):
            return
        download_url = str(payload.get("download_url") or "").strip()
        if not download_url:
            return
        target_version = str(payload.get("target_version") or "").strip()
        expected_sha256 = str(payload.get("sha256") or "").strip().lower()
        signature = "|".join([target_version, expected_sha256, download_url])
        if signature and signature == self._ota_last_download_signature:
            return
        with self._ota_download_lock:
            if self._ota_download_inflight:
                return
            self._ota_download_inflight = True

        def _runner() -> None:
            try:
                candidate_urls: list[str] = [download_url]
                try:
                    fallback_url = self._updates_download_url(target_version)
                except Exception:
                    fallback_url = ""
                if fallback_url and fallback_url not in candidate_urls:
                    candidate_urls.append(fallback_url)

                last_exc: Optional[Exception] = None
                local_path: Optional[Path] = None
                for idx, candidate in enumerate(candidate_urls, start=1):
                    try:
                        if idx > 1:
                            print(f"[OTA] retry download via fallback url={candidate}")
                        local_path = self._ota_download_artifact(candidate, target_version, expected_sha256)
                        break
                    except Exception as exc:
                        last_exc = exc
                        if idx >= len(candidate_urls):
                            raise
                        print(f"[OTA] download attempt failed url={candidate} err={exc}")

                if local_path is None:
                    raise RuntimeError(str(last_exc or "download failed"))
                self._ota_last_download_signature = signature
                self._ota_last_downloaded_path = str(local_path)
                self._ota_last_download_error = ""
                print(
                    f"[OTA] download ready version={target_version or '-'} "
                    f"path={local_path}"
                )
                if self._ota_auto_apply_enabled:
                    self._ota_auto_apply(local_path, target_version)
            except Exception as exc:
                self._ota_last_download_error = str(exc)
                print(f"[OTA] download failed: {exc}")
            finally:
                with self._ota_download_lock:
                    self._ota_download_inflight = False

        threading.Thread(target=_runner, daemon=True, name="ota-download").start()

    def _ota_download_artifact(self, download_url: str, target_version: str, expected_sha256: str) -> Path:
        if requests is None:
            raise RuntimeError("requests module not installed")
        parsed = urlsplit(download_url)
        candidate_name = Path(parsed.path).name if parsed.path else ""
        out_dir = self._ota_download_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        timeout = max(15.0, min(180.0, self._sales_request_timeout() * 3))
        print(f"[OTA] download start url={download_url}")
        req_headers: dict[str, str] = {}
        try:
            req_headers = dict(self._build_kiosk_api_auth_headers())
            req_headers.pop("Content-Type", None)
        except Exception:
            req_headers = {}
        response = requests.get(download_url, headers=req_headers, stream=True, timeout=timeout)
        if int(response.status_code) >= 400:
            body_text = str(response.text or "").replace("\n", " ").replace("\r", " ").strip()
            raise RuntimeError(f"HTTP {response.status_code} {body_text[:180]}")

        header_name = self._ota_filename_from_headers(
            response.headers.get("Content-Disposition", ""),
            response.headers.get("Content-Type", ""),
        )
        if header_name:
            candidate_name = header_name

        if not Path(candidate_name).suffix:
            content_type = str(response.headers.get("Content-Type", "")).lower()
            if "zip" in content_type:
                candidate_name = f"{candidate_name or 'kiosk_update'}.zip"
            elif "msdownload" in content_type or "portable-executable" in content_type:
                candidate_name = f"{candidate_name or 'kiosk_update'}.exe"
        safe_name = self._sanitize_ota_filename(candidate_name, "kiosk_update.bin")
        version_tag = re.sub(r"[^A-Za-z0-9._-]+", "_", str(target_version or "").strip()) or "latest"
        final_name = f"v{version_tag}_{safe_name}"
        final_path = out_dir / final_name
        tmp_path = out_dir / f"{final_name}.part"
        print(f"[OTA] download target out={final_path}")

        digest = hashlib.sha256()
        bytes_written = 0
        try:
            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    digest.update(chunk)
                    bytes_written += len(chunk)
        finally:
            try:
                response.close()
            except Exception:
                pass

        if bytes_written <= 0:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise RuntimeError("empty download")

        actual_sha = digest.hexdigest().lower()
        if expected_sha256 and actual_sha != expected_sha256:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise RuntimeError(
                f"sha256 mismatch expected={expected_sha256} actual={actual_sha}"
            )

        if final_path.exists():
            try:
                final_path.unlink()
            except Exception:
                pass
        tmp_path.replace(final_path)

        meta = {
            "download_url": download_url,
            "target_version": target_version,
            "sha256": actual_sha,
            "size_bytes": bytes_written,
            "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        }
        meta_path = final_path.with_suffix(f"{final_path.suffix}.meta.json")
        _write_json_atomic(meta_path, meta)
        print(f"[OTA] download ok bytes={bytes_written} sha256={actual_sha}")
        return final_path

    def _ota_auto_apply(self, artifact_path: Path, target_version: str) -> None:
        path = Path(artifact_path)
        if not path.is_file():
            print(f"[OTA] auto apply skipped: file missing ({path})")
            return
        suffix = str(path.suffix).lower()
        cmd_tpl = str(self._ota_apply_cmd_template or "").strip()
        if cmd_tpl:
            cmd = cmd_tpl.format(artifact=str(path), version=str(target_version or ""))
            try:
                subprocess.Popen(cmd, shell=True)
                print(f"[OTA] auto apply command started: {cmd}")
                if self._ota_auto_restart_enabled and suffix == ".zip":
                    self._schedule_ota_restart(reason="custom_cmd_zip")
            except Exception as exc:
                print(f"[OTA] auto apply command failed: {exc}")
            return

        # Built-in default apply path for Windows deployments.
        script_path = INSTALL_ROOT / "deploy" / "windows" / "apply_update.ps1"
        try:
            if script_path.is_file():
                cmd_parts = [
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script_path),
                    "-ArtifactPath",
                    str(path),
                ]
                if suffix == ".zip":
                    cmd_parts.extend(
                        [
                            "-InstallDir",
                            str(INSTALL_ROOT),
                            "-TargetVersion",
                            str(target_version or ""),
                            "-StateFile",
                            str(self._ota_state_path),
                        ]
                    )
                else:
                    cmd_parts.append("-Silent")
                subprocess.Popen(cmd_parts, shell=False)
                print(f"[OTA] auto apply default started: {' '.join(cmd_parts)}")
                if self._ota_auto_restart_enabled and suffix == ".zip":
                    self._schedule_ota_restart(reason="default_zip")
                return
        except Exception as exc:
            print(f"[OTA] auto apply default failed: {exc}")

        # If no explicit command is configured and default script path is missing, skip.
        print(f"[OTA] auto apply skipped: no apply command/script (artifact={path})")

    def _build_self_restart_command(self) -> list[str]:
        if getattr(sys, "frozen", False):
            args = list(sys.argv[1:]) if len(sys.argv) > 1 else []
            return [str(sys.executable), *[str(x) for x in args]]

        argv = [str(x) for x in list(sys.argv or [])]
        if not argv:
            return [str(sys.executable), str((ROOT_DIR / "app" / "main.py").resolve())]
        return [str(sys.executable), *argv]

    def _schedule_ota_restart(self, reason: str) -> None:
        if self._ota_restart_scheduled:
            return
        self._ota_restart_scheduled = True
        delay_sec = float(self._ota_restart_delay_sec)
        cmd = self._build_self_restart_command()
        cmd_json = json.dumps(cmd)
        cwd_json = json.dumps(str(ROOT_DIR))
        launcher_code = (
            "import subprocess,time; "
            f"time.sleep({max(1.0, delay_sec):.2f}); "
            f"subprocess.Popen({cmd_json}, cwd={cwd_json}, close_fds=True)"
        )
        try:
            subprocess.Popen([str(sys.executable), "-c", launcher_code], close_fds=True)
            print(
                f"[OTA] restart scheduled reason={reason} delay={delay_sec:.1f}s "
                f"cmd={' '.join(cmd)}"
            )
        except Exception as exc:
            self._ota_restart_scheduled = False
            print(f"[OTA] restart scheduling failed: {exc}")
            return

        app_inst = QApplication.instance()
        if app_inst is None:
            print("[OTA] restart warning: QApplication instance missing, skip auto-quit")
            return
        quit_delay_ms = int(max(1200.0, min(10000.0, delay_sec * 500.0)))
        QTimer.singleShot(quit_delay_ms, app_inst.quit)

    def _probe_ota_state(self) -> dict[str, Any]:
        current_version = self._current_kiosk_app_version()
        result: dict[str, Any] = {
            "active": False,
            "message": "",
            "target_version": "",
            "update_available": False,
            "force_update": False,
            "download_url": "",
            "sha256": "",
            "notes": "",
            "min_supported_version": "",
            "current_version": current_version,
            "error": "",
        }
        if requests is None:
            result["error"] = "requests module not installed"
            return result
        try:
            url = self._updates_check_url()
            headers = self._build_kiosk_api_auth_headers()
            headers = dict(headers)
            headers.pop("Content-Type", None)
        except Exception as exc:
            result["error"] = f"client config missing ({exc})"
            return result

        timeout = min(6.0, self._sales_request_timeout())
        try:
            response = requests.get(
                url,
                headers=headers,
                params={"platform": "win", "current": current_version},
                timeout=timeout,
            )
        except Exception as exc:
            result["error"] = str(exc)
            return result

        lock_hit, parsed_payload = self._consume_server_lock_response(response, trigger="ota_check_api")
        if lock_hit:
            result["error"] = "DEVICE_LOCKED"
            return result

        if int(response.status_code) >= 400:
            body_text = str(response.text or "").replace("\n", " ").replace("\r", " ").strip()
            result["error"] = f"HTTP {response.status_code} {body_text[:180]}"
            return result

        data = parsed_payload if isinstance(parsed_payload, dict) else {}
        if not data:
            try:
                parsed = response.json()
                if isinstance(parsed, dict):
                    data = parsed
            except Exception:
                data = {}
        if not isinstance(data, dict):
            result["error"] = "invalid json payload"
            return result

        update_available = bool(data.get("update_available", False))
        force_update = bool(data.get("force_update", False))
        target_version = str(data.get("target_version") or data.get("active_version") or "").strip()
        min_supported = str(data.get("min_supported_version") or "").strip()
        notes = str(data.get("notes") or "").strip()
        download_url = str(data.get("download_url") or "").strip()
        sha256 = str(data.get("sha256") or "").strip().lower()

        result["update_available"] = update_available
        result["force_update"] = force_update
        result["target_version"] = target_version
        result["download_url"] = download_url
        result["sha256"] = sha256
        result["notes"] = notes
        result["min_supported_version"] = min_supported
        if force_update:
            result["active"] = True
            result["message"] = self._build_ota_force_lock_message(target_version, min_supported, notes)
        return result

    def _ota_check_tick(self) -> None:
        if self._ota_check_inflight:
            return
        self._ota_check_inflight = True

        def _runner() -> None:
            try:
                payload = self._probe_ota_state()
                self.ota_state_signal.emit(payload)
            finally:
                self._ota_check_inflight = False

        threading.Thread(target=_runner, daemon=True, name="ota-check").start()

    def _set_offline_lock(self, active: bool, message: str, trigger: str) -> None:
        was_active = bool(self._offline_lock_active)
        self._offline_lock_active = bool(active)
        self._offline_lock_message = str(message or "").strip()

        if self._offline_lock_active:
            if not was_active:
                print(f"[LICENSE] LOCKED trigger={trigger} message={self._offline_lock_message}")
        elif was_active:
            print(f"[LICENSE] UNLOCKED trigger={trigger}")
        self._sync_runtime_lock_screen(trigger=f"offline:{trigger}")

    def _enforce_offline_runtime_guard(self, trigger: str = "runtime") -> None:
        should_lock, message = self._compute_offline_guard_status()
        self._set_offline_lock(should_lock, message, trigger)

    def _record_online_heartbeat(self) -> None:
        now_ts = time.time()
        now_iso = datetime.now().isoformat(timespec="seconds")
        with self._license_state_lock:
            state = self._load_license_state_unlocked()
            state["last_online_at"] = now_iso
            state["last_online_ts"] = now_ts
            state["last_online_source"] = "heartbeat"
            if not str(state.get("first_seen_at", "")).strip():
                state["first_seen_at"] = now_iso
            try:
                first_seen_ts = float(state.get("first_seen_ts", 0.0) or 0.0)
            except Exception:
                first_seen_ts = 0.0
            if first_seen_ts <= 0:
                state["first_seen_ts"] = now_ts
                first_seen_ts = now_ts
            self._save_license_state_unlocked(state)
            self._first_seen_ts = first_seen_ts
            self._last_online_ts = now_ts
        print(f"[LICENSE] online heartbeat at={now_iso}")

    def _init_offline_license_state(self) -> None:
        raw_hours = os.environ.get("KIOSK_OFFLINE_GRACE_HOURS", str(DEFAULT_OFFLINE_GRACE_HOURS))
        try:
            grace_hours = float(raw_hours)
        except Exception:
            grace_hours = float(DEFAULT_OFFLINE_GRACE_HOURS)
        self._offline_grace_seconds = max(3600, int(grace_hours * 3600))

        guard_env = os.environ.get("KIOSK_OFFLINE_GUARD", "1")
        enabled = self._env_bool(guard_env, True)
        if self.is_test_mode():
            enabled = False
        self._offline_guard_enabled = bool(enabled)

        with self._license_state_lock:
            state = self._load_license_state_unlocked()
            now_iso = datetime.now().isoformat(timespec="seconds")
            changed = False
            if not str(state.get("first_seen_at", "")).strip():
                state["first_seen_at"] = now_iso
                changed = True
            try:
                first_seen_ts = float(state.get("first_seen_ts", 0.0) or 0.0)
            except Exception:
                first_seen_ts = 0.0
            if first_seen_ts <= 0:
                first_seen_ts = self._parse_iso_to_ts(str(state.get("first_seen_at", "")))
                if first_seen_ts <= 0:
                    first_seen_ts = time.time()
                state["first_seen_ts"] = first_seen_ts
                changed = True

            ts_value = 0.0
            try:
                ts_value = float(state.get("last_online_ts", 0.0) or 0.0)
            except Exception:
                ts_value = 0.0
            if ts_value <= 0:
                ts_value = self._parse_iso_to_ts(str(state.get("last_online_at", "")))
                if ts_value > 0:
                    state["last_online_ts"] = ts_value
                    changed = True
            self._first_seen_ts = first_seen_ts
            self._last_online_ts = ts_value
            if changed:
                self._save_license_state_unlocked(state)

        print(
            f"[LICENSE] init guard={1 if self._offline_guard_enabled else 0} "
            f"grace_hours={self._offline_grace_seconds / 3600:.1f} "
            f"first_seen_ts={self._first_seen_ts:.0f} "
            f"last_online_ts={self._last_online_ts:.0f}"
        )
        self._enforce_offline_runtime_guard("startup")

    def retry_offline_unlock(self) -> None:
        print("[LICENSE] manual retry requested")
        self._show_runtime_notice("재인증 시도중... / Retrying authorization...", duration_ms=1000)
        self._heartbeat_tick()

    def check_runtime_internet_health(self) -> tuple[bool, str]:
        share = self.get_share_settings()
        api_base = _normalize_kiosk_api_base_url(share.get("api_base_url", "")) if isinstance(share, dict) else ""
        ok, msg = check_internet(timeout=1.0, api_base_url=api_base)
        print(f"[HEALTH] internet={'OK' if ok else 'FAIL'} msg={msg}")
        return ok, msg

    def check_runtime_camera_health(self, backend: Optional[str] = None) -> tuple[bool, str]:
        backend_name = (
            str(backend or "").strip().lower()
            if isinstance(backend, str)
            else self._resolve_requested_camera_backend()
        )
        dll_path = self._resolve_canon_edsdk_dll_path()
        ok, msg = get_camera_health(dll_path, backend_name)
        print(f"[HEALTH] camera={'OK' if ok else 'FAIL'} msg={msg}")
        return ok, msg

    def check_runtime_printer_health(self, model: str, printer_name: str) -> tuple[bool, str]:
        model_key = str(model).strip().upper()
        if model_key == "DS620_STRIP":
            key = "printer_ds620_strip"
        elif model_key == "DS620":
            key = "printer_ds620"
        else:
            key = "printer_rx1hs"
        log_key = _health_log_key(key)
        ok, msg = get_printer_health(printer_name)
        print(f"[HEALTH] {log_key}={'OK' if ok else 'FAIL'} msg={msg}")
        return ok, msg

    @staticmethod
    def _resolve_print_model(settings: dict) -> str:
        model = str(settings.get("default_model", "DS620")).strip().upper()
        return model if model in {"DS620", "DS620_STRIP", "RX1HS"} else "DS620"

    def _resolve_printer_name_for_model(self, model: str, settings: Optional[dict] = None) -> str:
        cfg = settings if isinstance(settings, dict) else self.get_printing_settings()
        printers = cfg.get("printers", {})
        model_key = str(model or "DS620").strip().upper()

        def _finalize(candidate_name: str) -> str:
            value = str(candidate_name or "").strip()
            if not value:
                return ""
            matched = self._match_installed_printer_name(value, model_key)
            if matched and matched != value:
                print(
                    f"[PRINT] printer name auto-match model={model_key} "
                    f"requested=\"{value}\" matched=\"{matched}\""
                )
            return matched or value

        selected = ""
        if isinstance(printers, dict):
            item = printers.get(model_key)
            if isinstance(item, dict):
                selected = str(item.get("win_name", "")).strip()
        if selected:
            return _finalize(selected)

        data = self._read_config_dict()
        if model_key == "DS620_STRIP":
            if isinstance(printers, dict):
                item = printers.get("DS620")
                if isinstance(item, dict):
                    fallback = str(item.get("win_name", "")).strip()
                    if fallback:
                        return _finalize(fallback)
            value = data.get("default_printer_ds620") if isinstance(data, dict) else None
            if isinstance(value, str) and value.strip():
                return _finalize(value.strip())
            return _finalize(str(DEFAULT_PRINTING_SETTINGS["printers"]["DS620"]["win_name"]))
        if model_key == "RX1HS":
            value = data.get("default_printer_rx1hs") if isinstance(data, dict) else None
            if isinstance(value, str) and value.strip():
                return _finalize(value.strip())
            return _finalize(str(DEFAULT_PRINTING_SETTINGS["printers"]["RX1HS"]["win_name"]))
        value = data.get("default_printer_ds620") if isinstance(data, dict) else None
        if isinstance(value, str) and value.strip():
            return _finalize(value.strip())
        return _finalize(str(DEFAULT_PRINTING_SETTINGS["printers"]["DS620"]["win_name"]))

    def _resolve_dedicated_strip_queue_name(self, settings: Optional[dict] = None) -> str:
        cfg = settings if isinstance(settings, dict) else self.get_printing_settings()
        printers = cfg.get("printers", {}) if isinstance(cfg, dict) else {}
        strip_item = printers.get("DS620_STRIP", {}) if isinstance(printers, dict) else {}
        configured = str(strip_item.get("win_name", "")).strip() if isinstance(strip_item, dict) else ""

        installed = self.list_windows_printers()

        def _installed_member(name: str) -> str:
            probe = str(name or "").strip()
            if not probe:
                return ""
            for item in installed:
                cand = str(item).strip()
                if cand == probe:
                    return cand
            probe_low = probe.lower()
            for item in installed:
                cand = str(item).strip()
                if cand.lower() == probe_low:
                    return cand
            probe_norm = self._normalize_printer_name_token(probe)
            if probe_norm:
                for item in installed:
                    cand = str(item).strip()
                    if self._normalize_printer_name_token(cand) == probe_norm:
                        return cand
            return ""

        # 1) Explicit DS620_STRIP queue from config.
        if configured:
            matched = self._match_installed_printer_name(configured, "DS620_STRIP")
            found = _installed_member(matched or configured)
            if found:
                return found
            print(
                f"[PRINT_MODE] strip queue configured but missing: requested=\"{configured}\" "
                f"matched=\"{matched}\""
            )

        # 2) Optional auto-detect: disabled by default to avoid accidental routing
        # to *_STRIP queues where driver split/cut settings are unknown.
        auto_detect = str(os.environ.get("KIOSK_STRIP_QUEUE_AUTODETECT", "1")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if auto_detect:
            for probe in (
                "DS620_STRIP",
                "DS620 STRIP",
                "DP-DS620 STRIP",
                "DS620STRIP",
                "RX1HS_STRIP",
                "RX1HS STRIP",
                "RX1_STRIP",
                "RX1 STRIP",
                "DS-RX1_STRIP",
                "DS-RX1 STRIP",
            ):
                matched = self._match_installed_printer_name(probe, "DS620_STRIP")
                found = _installed_member(matched or probe)
                if found:
                    return found
        return ""

    def _is_installed_printer_name(self, name: str, installed: Optional[list[str]] = None) -> bool:
        probe = str(name or "").strip()
        if not probe:
            return False
        names = installed if isinstance(installed, list) else self.list_windows_printers()
        probe_low = probe.lower()
        probe_norm = self._normalize_printer_name_token(probe)
        for item in names:
            cand = str(item).strip()
            if not cand:
                continue
            if cand == probe or cand.lower() == probe_low:
                return True
            if probe_norm and self._normalize_printer_name_token(cand) == probe_norm:
                return True
        return False

    def _resolve_printer_candidates_for_model(
        self,
        model: str,
        primary_name: str = "",
        settings: Optional[dict] = None,
    ) -> list[str]:
        cfg = settings if isinstance(settings, dict) else self.get_printing_settings()
        model_key = str(model or "DS620").strip().upper()
        if model_key not in {"DS620", "DS620_STRIP", "RX1HS"}:
            model_key = "DS620"

        installed = self.list_windows_printers()
        candidates: list[str] = []
        seen: set[str] = set()

        def _push(raw: str) -> None:
            text = str(raw or "").strip()
            if not text:
                return
            matched = self._match_installed_printer_name(text, model_key)
            chosen = ""
            if matched and self._is_installed_printer_name(matched, installed):
                chosen = matched
            elif self._is_installed_printer_name(text, installed):
                chosen = text
            if not chosen:
                return
            key = self._normalize_printer_name_token(chosen)
            if key in seen:
                return
            seen.add(key)
            candidates.append(chosen)

        _push(primary_name)
        _push(self._resolve_printer_name_for_model(model_key, cfg))
        if model_key == "DS620_STRIP":
            _push(self._resolve_dedicated_strip_queue_name(cfg))
            for probe in (
                "DS620_STRIP",
                "DS620 STRIP",
                "DP-DS620 STRIP",
                "DS620STRIP",
                "RX1HS_STRIP",
                "RX1HS STRIP",
                "RX1_STRIP",
                "RX1 STRIP",
                "DS-RX1_STRIP",
                "DS-RX1 STRIP",
            ):
                _push(probe)
        elif model_key == "DS620":
            for probe in ("DP-DS620", "DS620"):
                _push(probe)
        elif model_key == "RX1HS":
            for probe in ("DNP RX1HS", "RX1HS", "RX1"):
                _push(probe)
        if candidates:
            physical = [name for name in candidates if not self._is_virtual_printer_name(name)]
            virtual = [name for name in candidates if self._is_virtual_printer_name(name)]
            if physical and virtual:
                candidates = physical + virtual
                print(
                    f"[PRINT] virtual queues deprioritized model={model_key} "
                    f"virtual={', '.join(virtual)}"
                )
        return candidates

    def _resolve_printer_form_name_for_job(
        self,
        model: str,
        job_size: str,
        settings: Optional[dict] = None,
    ) -> str:
        cfg = settings if isinstance(settings, dict) else self.get_printing_settings()
        model_key = str(model or "DS620").strip().upper()
        if model_key not in {"DS620", "DS620_STRIP", "RX1HS"}:
            model_key = "DS620"
        printers = cfg.get("printers", {}) if isinstance(cfg, dict) else {}
        item = printers.get(model_key, {}) if isinstance(printers, dict) else {}
        form_4x6 = str(item.get("form_4x6", "4x6")).strip() or "4x6"
        form_2x6 = str(item.get("form_2x6", "2x6")).strip() or "2x6"
        size_text = str(job_size or "4x6").strip().lower()
        if size_text.startswith("2x6"):
            return form_2x6
        return form_4x6

    def get_payment_pricing_settings(self) -> dict:
        return {
            "currency_prefix": str(self.payment_pricing_settings.get("currency_prefix", "")),
            "default_price": int(self.payment_pricing_settings.get("default_price", 0)),
            "layouts": dict(self.payment_pricing_settings.get("layouts", {})),
        }

    def get_modes_settings(self) -> dict[str, bool]:
        return dict(self.mode_settings)

    def get_ai_style_settings(self) -> dict[str, dict[str, Any]]:
        return {style_id: dict(info) for style_id, info in dict(self.ai_style_settings).items()}

    def get_celebrity_settings(self) -> dict[str, str]:
        return dict(self.celebrity_settings)

    def get_coupon_value_settings(self) -> dict:
        return {
            "default_coupon_value": int(self.coupon_value_settings.get("default_coupon_value", 0)),
            "values": dict(self.coupon_value_settings.get("values", {})),
        }

    def get_coupon_settings(self) -> dict:
        return dict(self.coupon_settings)

    def get_thank_you_gif_rect(self) -> tuple[int, int, int, int]:
        rect = self.thank_you_settings.get("gif_rect", DEFAULT_THANK_YOU_SETTINGS["gif_rect"])
        if isinstance(rect, list) and len(rect) == 4:
            return (int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))
        return tuple(DEFAULT_THANK_YOU_SETTINGS["gif_rect"])  # type: ignore[return-value]

    def _resolve_requested_camera_backend(self, settings: Optional[dict] = None) -> str:
        current = settings if isinstance(settings, dict) else self.admin_settings
        backend = str(current.get("camera_backend", "auto")).strip().lower()
        if backend in {"auto", "edsdk", "dummy"}:
            return backend
        return "auto"

    def get_countdown_seconds(self) -> int:
        return int(self.admin_settings.get("countdown_seconds", 3))

    def get_capture_slots_override(self) -> Optional[int]:
        value = self.admin_settings.get("capture_slots_override", "auto")
        if isinstance(value, int):
            return value
        return None

    def allow_dummy_when_camera_fail(self) -> bool:
        enabled = bool(
            self.admin_settings.get(
                "allow_dummy_when_camera_fail",
                bool(DEFAULT_ADMIN_SETTINGS["allow_dummy_when_camera_fail"]),
            )
        )
        # Dummy fallback is allowed only in test mode.
        return bool(self.is_test_mode() and enabled)

    def is_test_mode(self) -> bool:
        return bool(self.admin_settings.get("test_mode", False))

    def is_ai_strict_mode_enabled(self) -> bool:
        # In operation mode, AI must be Gemini-only (no local fallback).
        return not self.is_test_mode()

    def is_debug_fullscreen_shutter(self) -> bool:
        return bool(self.admin_settings.get("debug_fullscreen_shutter", False))

    def _apply_admin_hotspot_overrides(self) -> None:
        camera_hotspots = list(self.hotspot_map.get("camera", []))
        camera_hotspots = [h for h in camera_hotspots if h.id != "shutter_debug_full"]
        requested_backend = self._resolve_requested_camera_backend(self.admin_settings)
        enable_debug_shutter = bool(self.admin_settings.get("debug_fullscreen_shutter", False))
        if not enable_debug_shutter:
            enable_debug_shutter = bool(self.admin_settings.get("test_mode", False)) and requested_backend == "dummy"
        if enable_debug_shutter:
            camera_hotspots.append(
                Hotspot(
                    id="shutter_debug_full",
                    rect=(0, 0, DESIGN_WIDTH, DESIGN_HEIGHT),
                    action="camera:shutter",
                )
            )
        self.hotspot_map["camera"] = camera_hotspots
        camera_screen = self.screens.get("camera")
        if isinstance(camera_screen, ImageScreen):
            camera_screen.set_hotspots(camera_hotspots)
            camera_screen.set_overlay_visible(self.show_hotspot_overlay)

    def _apply_admin_settings(self, settings: dict, emit_log: bool = True) -> None:
        self.admin_settings = self._normalize_admin_settings(settings)
        effective_dry_run = bool(self.admin_settings.get("print_dry_run")) or bool(
            self.printing_settings.get("dry_run", False)
        )
        os.environ["DRY_RUN_PRINT"] = "1" if effective_dry_run else "0"
        os.environ["UPLOAD_DRY_RUN"] = "1" if bool(self.admin_settings.get("upload_dry_run")) else "0"
        self._apply_admin_hotspot_overrides()

        camera_screen = self.screens.get("camera")
        if isinstance(camera_screen, CameraScreen):
            camera_screen.camera_backend = self._resolve_requested_camera_backend(self.admin_settings)
            if camera_screen.layout_id:
                camera_screen.set_layout(camera_screen.layout_id)
            if camera_screen.isVisible():
                camera_screen._stop_liveview_worker(wait=False)
                camera_screen._start_liveview_worker()

        if emit_log:
            print(
                "[ADMIN] applied "
                f"camera_backend={self._resolve_requested_camera_backend(self.admin_settings)} "
                f"test_mode={self.is_test_mode()} "
                f"allow_dummy={self.allow_dummy_when_camera_fail()} "
                f"countdown={self.get_countdown_seconds()} "
                f"capture_override={self.admin_settings.get('capture_slots_override')}"
            )

    def save_admin_settings(
        self,
        settings: dict,
        payment_methods: Optional[dict] = None,
        modes: Optional[dict] = None,
        ai_styles: Optional[dict] = None,
        bill_acceptor: Optional[dict] = None,
        celebrity: Optional[dict] = None,
        pricing: Optional[dict] = None,
        printing: Optional[dict] = None,
    ) -> bool:
        was_bill_running = self.is_bill_acceptor_running()
        normalized = self._normalize_admin_settings(settings)
        config = self._read_config_dict()
        config["admin"] = normalized
        source_payment = payment_methods if payment_methods is not None else config.get("payment_methods")
        normalized_payment, forced_cash = self._normalize_payment_methods(source_payment)
        config["payment_methods"] = normalized_payment
        source_modes = modes if modes is not None else config.get("modes")
        normalized_modes = self._normalize_modes_settings(source_modes)
        config["modes"] = normalized_modes
        source_ai_styles = ai_styles if ai_styles is not None else config.get("ai_styles")
        normalized_ai_styles = self._normalize_ai_styles_settings(source_ai_styles)
        config["ai_styles"] = normalized_ai_styles
        source_bill = bill_acceptor if bill_acceptor is not None else config.get("bill_acceptor")
        normalized_bill = self._normalize_bill_acceptor_settings(source_bill)
        config["bill_acceptor"] = normalized_bill
        source_celebrity = celebrity if celebrity is not None else config.get("celebrity")
        normalized_celebrity = self._normalize_celebrity_settings(source_celebrity)
        config["celebrity"] = normalized_celebrity
        source_pricing = pricing if pricing is not None else config.get("pricing")
        normalized_pricing = self._normalize_pricing_settings(
            source_pricing,
            legacy_settings=config.get("payment_pricing"),
            layout_ids=self._pricing_layout_ids_with_modes(
                self.available_layout_ids,
                celebrity_layout_id=str(
                    normalized_celebrity.get("layout_id", DEFAULT_CELEBRITY_SETTINGS["layout_id"])
                ).strip(),
            ),
        )
        config["pricing"] = normalized_pricing
        # Backward-compatible mirror.
        config["payment_pricing"] = {
            "default_price": int(normalized_pricing.get("default_price", DEFAULT_PRICING_SETTINGS["default_price"])),
            "pricing_by_layout": dict(normalized_pricing.get("layouts", {})),
        }
        source_printing = printing if printing is not None else config.get("printing")
        if isinstance(printing, dict) and isinstance(config.get("printing"), dict):
            # Preserve extra printer profiles (e.g. DS620_STRIP) when admin UI submits DS620/RX1HS only.
            merged_printing = dict(config.get("printing", {}))
            merged_printing.update(printing)
            merged_printers = dict(merged_printing.get("printers", {}))
            new_printers = printing.get("printers")
            if isinstance(new_printers, dict):
                for key, value in new_printers.items():
                    merged_printers[key] = value
            merged_printing["printers"] = merged_printers
            source_printing = merged_printing
        normalized_printing = self._normalize_printing_settings(source_printing)
        config["printing"] = normalized_printing
        self._write_config_dict_atomic(config)
        self._apply_admin_settings(normalized, emit_log=False)
        self._apply_payment_methods(normalized_payment, emit_log=False)
        self._apply_mode_settings(normalized_modes, emit_log=False)
        self._apply_ai_style_settings(normalized_ai_styles, emit_log=False)
        self.bill_acceptor_settings = normalized_bill
        self.celebrity_settings = normalized_celebrity
        self.payment_pricing_settings = normalized_pricing
        self.printing_settings = normalized_printing
        self._sync_pricing_layout_defaults(persist=False)
        self._refresh_frame_select_price_labels()
        if was_bill_running:
            print("[BILL] settings changed -> restarting worker")
            self.stop_bill_acceptor_test(wait_ms=3000)
            if bool(normalized_bill.get("enabled", False)):
                self.start_bill_acceptor_test(normalized_bill)
        print(f"[ADMIN] config_path={self.config_path}")
        print(f"[ADMIN] saved {json.dumps(normalized, ensure_ascii=False, separators=(',', ':'))}")
        print(
            "[ADMIN] payment_methods set "
            f"cash={1 if normalized_payment['cash'] else 0} "
            f"card={1 if normalized_payment['card'] else 0} "
            f"coupon={1 if normalized_payment['coupon'] else 0}"
        )
        print(
            "[ADMIN] modes "
            f"celebrity_enabled={1 if normalized_modes['celebrity_enabled'] else 0} "
            f"ai_enabled={1 if normalized_modes['ai_enabled'] else 0}"
        )
        print(
            "[ADMIN] ai_styles "
            + ", ".join(
                f"{sid}=\"{info.get('label_ko', sid)}\"(enabled={1 if bool(info.get('enabled', True)) else 0},order={int(info.get('order', 0) or 0)})"
                for sid, info in normalized_ai_styles.items()
            )
        )
        print(
            f"[ADMIN] pricing prefix={normalized_pricing.get('currency_prefix', '')} "
            f"default={normalized_pricing.get('default_price', DEFAULT_PRICING_SETTINGS['default_price'])} "
            f"layouts={json.dumps(normalized_pricing.get('layouts', {}), ensure_ascii=False, sort_keys=True)}"
        )
        print(
            "[ADMIN] printing "
            f"enabled={1 if normalized_printing.get('enabled', True) else 0} "
            f"dry_run={1 if normalized_printing.get('dry_run', False) else 0} "
            f"DS620=\"{normalized_printing.get('printers', {}).get('DS620', {}).get('win_name', '')}\" "
            f"RX1HS=\"{normalized_printing.get('printers', {}).get('RX1HS', {}).get('win_name', '')}\""
        )
        print(
            "[ADMIN] DS620 "
            f"form_4x6=\"{normalized_printing.get('printers', {}).get('DS620', {}).get('form_4x6', '')}\" "
            f"form_2x6=\"{normalized_printing.get('printers', {}).get('DS620', {}).get('form_2x6', '')}\""
        )
        print(
            "[ADMIN] RX1HS "
            f"form_4x6=\"{normalized_printing.get('printers', {}).get('RX1HS', {}).get('form_4x6', '')}\" "
            f"form_2x6=\"{normalized_printing.get('printers', {}).get('RX1HS', {}).get('form_2x6', '')}\""
        )
        print(
            "[ADMIN] bill_acceptor "
            f"enabled={1 if normalized_bill['enabled'] else 0} "
            f"profile={normalized_bill['profile']} "
            f"port={normalized_bill['port']} "
            f"denoms={json.dumps(normalized_bill['denoms'], ensure_ascii=False, separators=(',', ':'))}"
        )
        return forced_cash

    def open_admin(self) -> None:
        current = self.stack.currentWidget()
        current_name = getattr(current, "screen_name", None)
        if isinstance(current_name, str) and current_name and current_name != "admin":
            self._admin_return_screen = current_name
        self.goto_screen("admin")

    def close_admin(self) -> None:
        self.goto_screen(self._admin_return_screen or "start")

    def _reset_start_admin_taps(self) -> None:
        self._start_admin_tap_count = 0

    def _ensure_admin_camera_base(self) -> tuple[Optional[CameraScreen], list[str]]:
        prepared: list[str] = []
        camera_screen = self.screens.get("camera")
        if not isinstance(camera_screen, CameraScreen):
            return None, prepared

        layout_id = self.current_layout_id or "2641"
        if self.current_layout_id != layout_id:
            self.current_layout_id = layout_id
            prepared.append("layout_id")

        camera_screen.camera_backend = self._resolve_requested_camera_backend()
        if camera_screen.layout_id != layout_id or not camera_screen.slot_rects:
            camera_screen.set_layout(layout_id)
            prepared.append("camera_layout")
        camera_screen.set_design(self.current_design_index, self.current_design_path)
        if camera_screen.session is None:
            camera_screen.start_session(layout_id, self.current_design_path)
            prepared.append("session")
        else:
            camera_screen.session.set_context(layout_id=layout_id, design_path=self.current_design_path)
        if camera_screen.session is not None:
            camera_screen.session.print_count = int(self.current_print_count or self.print_count or 2)
        return camera_screen, prepared

    def _ensure_admin_dummy_shots(self, camera_screen: CameraScreen, required_count: int) -> list[str]:
        prepared: list[str] = []
        required = max(0, int(required_count))
        added = 0
        while len(camera_screen.shot_paths) < required:
            index = len(camera_screen.shot_paths) + 1
            saved = camera_screen.capture_still(index)
            if len(camera_screen.shot_paths) >= index:
                camera_screen.shot_paths[index - 1] = saved
            elif len(camera_screen.shot_paths) == index - 1:
                camera_screen.shot_paths.append(saved)
            added += 1
        if added > 0:
            camera_screen.update()
            prepared.append(f"dummy_shots={added}")
            print(f"[ADMIN] generated dummy shots={added}")
        self.current_captured_paths = [str(p) for p in camera_screen.shot_paths]
        self.current_capture_slots = camera_screen.capture_slots
        self.current_print_slots = camera_screen.print_slots
        return prepared

    def _create_dummy_print_image(self) -> Image.Image:
        image = Image.new("RGB", (DESIGN_WIDTH, DESIGN_HEIGHT), (252, 252, 252))
        draw = ImageDraw.Draw(image)
        layout = self.current_layout_id or "2641"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        draw.text((120, 140), "DUMMY PRINT", fill=(20, 20, 20))
        draw.text((120, 240), f"layout={layout}", fill=(55, 55, 55))
        draw.text((120, 300), timestamp, fill=(75, 75, 75))
        return image

    def _ensure_admin_print_image(self, camera_screen: CameraScreen) -> list[str]:
        prepared: list[str] = []
        session = camera_screen.session
        if session is None:
            return prepared
        if self.current_print_path and Path(self.current_print_path).is_file():
            return prepared

        print_path = session.save_print(self._create_dummy_print_image())
        self.current_print_path = str(print_path)
        session.print_job_path = str(print_path)
        session.print_job_copies = 2
        session.print_job_size = "4x6"
        session.print_job_mode = "full"
        self.current_print_job_path = str(print_path)
        self.current_print_job_copies = 2
        self.current_print_job_size = "4x6"
        self.current_print_job_mode = "full"
        prepared.append("dummy_print")
        print(f"[ADMIN] generated print={print_path}")
        return prepared

    def prepare_state_for(self, target_screen: str) -> list[str]:
        prepared: list[str] = []
        if target_screen in {
            "camera",
            "after_camera_loading",
            "select_photo",
            "select_design",
            "preview",
            "loading",
            "qr_generating",
            "qr_code",
            "thank_you",
        }:
            camera_screen, prep = self._ensure_admin_camera_base()
            prepared.extend(prep)
            if not isinstance(camera_screen, CameraScreen):
                return prepared

            if target_screen in {
                "after_camera_loading",
                "select_photo",
                "select_design",
                "preview",
                "loading",
                "qr_generating",
            }:
                need_shots = max(1, int(camera_screen.capture_slots or camera_screen.print_slots or 4))
                prepared.extend(self._ensure_admin_dummy_shots(camera_screen, need_shots))

            if target_screen in {"select_design", "preview", "loading", "qr_generating", "qr_code"}:
                slots = max(1, int(camera_screen.print_slots or self.current_print_slots or 4))
                if self.current_print_slots <= 0:
                    self.current_print_slots = slots
                if len(self.selected_print_paths) < slots:
                    if len(self.current_captured_paths) < slots:
                        prepared.extend(self._ensure_admin_dummy_shots(camera_screen, slots))
                    self.selected_print_paths = self.current_captured_paths[:slots]
                    self.print_slots = slots
                    prepared.append(f"selected_paths={len(self.selected_print_paths)}")

            if target_screen in {"preview", "loading", "qr_generating", "qr_code"}:
                prepared.extend(self._ensure_admin_print_image(camera_screen))

        return prepared

    def admin_jump_to_screen(self, screen_name: str) -> None:
        target = (screen_name or "").strip()
        if target not in self.screens:
            print(f"[ADMIN] jump blocked unknown screen={target}")
            return

        prepared = self.prepare_state_for(target)
        if target == "select_photo":
            self._prepare_select_photo_screen()
        elif target == "select_design":
            self._prepare_select_design_screen()
        elif target == "preview":
            if not self._set_preview_from_print_job():
                return
        self.goto_screen(target)
        summary = ",".join(prepared) if prepared else "none"
        print(f"[ADMIN] jump screen={target} prepared={summary}")

    def enter_select_photo_from_camera(self) -> bool:
        camera_screen = self.screens.get("camera")
        if not isinstance(camera_screen, CameraScreen):
            print("[SELECT_PHOTO] enter blocked: camera screen missing")
            return False
        if not camera_screen.can_go_next():
            print(
                "[CAMERA] next blocked: shots incomplete "
                f"{len(camera_screen.shot_paths)}/{camera_screen.capture_slots}"
            )
            return False
        self.current_layout_id = camera_screen.layout_id
        self.current_captured_paths = [str(p) for p in camera_screen.shot_paths]
        self.current_capture_slots = camera_screen.capture_slots
        self.current_print_slots = camera_screen.print_slots
        self._start_select_photo_preload()
        return True

    def _save_selected_print_count(self) -> int:
        selected = int(self.current_print_count or self.print_count or 2)
        how_many_screen = self.screens.get("how_many_prints")
        if isinstance(how_many_screen, AppHowManyPrintsScreen):
            selected = int(how_many_screen.print_count)
        selected = max(2, min(10, selected))
        if selected % 2 != 0:
            selected -= 1
        if selected < 2:
            selected = 2
        self.current_print_count = selected
        self.print_count = selected
        session = self.get_active_session()
        if session is not None:
            session.print_count = int(selected)
        print(f"[PRINT_COUNT] selected={selected}")
        self._refresh_required_amount()
        return selected

    @staticmethod
    def _rect_contains(x: int, y: int, rect: tuple[int, int, int, int]) -> bool:
        rx, ry, rw, rh = rect
        return rx <= int(x) < rx + rw and ry <= int(y) < ry + rh

    def _price_per_set_for_layout(self, layout_id: Optional[str]) -> int:
        pricing = self.get_payment_pricing_settings()
        by_layout = pricing.get("layouts", {})
        if isinstance(by_layout, dict) and layout_id:
            value = by_layout.get(str(layout_id))
            if value is not None:
                try:
                    return max(0, int(value))
                except Exception:
                    pass
        return max(0, int(pricing.get("default_price", 0)))

    def _refresh_required_amount(self) -> int:
        layout_id = self.current_layout_id
        prints = int(self.current_print_count or self.print_count or 2)
        prints = max(2, prints)
        sets = max(1, prints // 2)
        base = self._price_per_set_for_layout(layout_id)
        required = max(0, base * sets)
        self.current_required_amount = int(required)
        remaining = max(0, self.current_required_amount - self.current_coupon_value - self.current_inserted_amount)
        self.current_remaining_amount = int(remaining)
        self._sync_payment_state_to_session()
        print(
            f"[PAYMENT] required_amount={self.current_required_amount} "
            f"layout={layout_id} base={base} sets={sets} prints={prints}"
        )
        return self.current_required_amount

    def _resolve_coupon_value(self, code_digits: str) -> int:
        code = "".join(ch for ch in str(code_digits) if ch.isdigit())[:6]
        hyphen = f"{code[:3]}-{code[3:6]}" if len(code) >= 6 else code
        settings = self.get_coupon_value_settings()
        values = settings.get("values", {})
        if isinstance(values, dict):
            for key in (hyphen, code):
                if key in values:
                    try:
                        return max(0, int(values[key]))
                    except Exception:
                        pass
        try:
            return max(0, int(settings.get("default_coupon_value", 0)))
        except Exception:
            return 0

    def _sync_payment_state_to_session(self) -> None:
        session = self.get_active_session()
        if session is None:
            return
        setattr(session, "payment_method", self.current_payment_method)
        setattr(session, "coupon_code", self.current_coupon_code)
        setattr(session, "coupon_value", int(self.current_coupon_value))
        setattr(session, "payment_required", int(self.current_required_amount))
        setattr(session, "payment_inserted", int(self.current_inserted_amount))
        setattr(session, "payment_remaining", int(self.current_remaining_amount))

    def _start_bill_acceptor_for_payment(self) -> bool:
        settings = self.get_bill_acceptor_settings()
        if not bool(settings.get("enabled", False)):
            print("[BILL] payment start blocked: bill_acceptor disabled")
            return False
        started = self.start_bill_acceptor_test(settings)
        if not started:
            print("[BILL] payment start failed")
            return False
        print("[BILL] payment listener started")
        return True

    def _stop_bill_acceptor_for_payment(self) -> None:
        if self.is_bill_acceptor_running():
            self.stop_bill_acceptor_test(wait_ms=3000)
            print("[BILL] payment listener stopped")

    def _enter_pay_cash_screen(self) -> None:
        required = self.current_required_amount if self.current_required_amount > 0 else self._refresh_required_amount()
        self.current_coupon_value = 0
        self.current_inserted_amount = 0
        self.current_remaining_amount = max(0, required)
        self._sync_payment_state_to_session()
        screen = self.screens.get("pay_cash")
        if isinstance(screen, PayCashScreen):
            screen.set_amounts(required, 0)
        print(
            f"[PAYMENT_CASH] enter required={self.current_required_amount} "
            f"inserted={self.current_inserted_amount} remaining={self.current_remaining_amount}"
        )
        if not self._start_bill_acceptor_for_payment():
            if isinstance(screen, PayCashScreen):
                screen.show_notice("지폐기 연결 실패", duration_ms=1200)

    def _enter_coupon_remaining_method_screen(self) -> None:
        required = self.current_required_amount if self.current_required_amount > 0 else self._refresh_required_amount()
        remaining = max(0, required - self.current_coupon_value)
        self.current_inserted_amount = 0
        self.current_remaining_amount = remaining
        self._sync_payment_state_to_session()
        print(
            f"[PAYMENT] coupon remaining select enter required={required} "
            f"coupon={self.current_coupon_value} remaining={remaining}"
        )

    def _enter_pay_cash_remaining_screen(self) -> None:
        required = self.current_required_amount if self.current_required_amount > 0 else self._refresh_required_amount()
        self.current_inserted_amount = 0
        self.current_remaining_amount = max(0, required - self.current_coupon_value)
        self._sync_payment_state_to_session()
        screen = self.screens.get("pay_cash_remaining")
        if isinstance(screen, PayCashRemainingScreen):
            screen.set_amounts(required, self.current_coupon_value, self.current_inserted_amount)
        print(
            f"[PAYMENT_CASH] enter remaining required={required} "
            f"coupon={self.current_coupon_value} inserted={self.current_inserted_amount} "
            f"remaining={self.current_remaining_amount}"
        )
        if not self._start_bill_acceptor_for_payment():
            if isinstance(screen, PayCashRemainingScreen):
                screen.show_notice("지폐기 연결 실패", duration_ms=1200)

    def _on_bill_event_for_payment(self, amount: int) -> None:
        current = self.stack.currentWidget()
        screen_name = getattr(current, "screen_name", None)
        if screen_name == "pay_cash":
            self.current_inserted_amount += int(amount)
            self.current_remaining_amount = max(0, self.current_required_amount - self.current_inserted_amount)
            screen = self.screens.get("pay_cash")
            if isinstance(screen, PayCashScreen):
                screen.set_amounts(self.current_required_amount, self.current_inserted_amount)
            self._sync_payment_state_to_session()
            print(
                f"[PAYMENT_CASH] required={self.current_required_amount} "
                f"inserted={self.current_inserted_amount} remaining={self.current_remaining_amount}"
            )
            if self.current_inserted_amount >= self.current_required_amount:
                self._stop_bill_acceptor_for_payment()
                self.goto_screen("payment_complete_success")
            return
        if screen_name == "pay_cash_remaining":
            self.current_inserted_amount += int(amount)
            self.current_remaining_amount = max(
                0,
                self.current_required_amount - self.current_coupon_value - self.current_inserted_amount,
            )
            screen = self.screens.get("pay_cash_remaining")
            if isinstance(screen, PayCashRemainingScreen):
                screen.set_amounts(
                    self.current_required_amount,
                    self.current_coupon_value,
                    self.current_inserted_amount,
                )
            self._sync_payment_state_to_session()
            print(
                f"[PAYMENT_CASH] required={self.current_required_amount} coupon={self.current_coupon_value} "
                f"inserted={self.current_inserted_amount} remaining={self.current_remaining_amount}"
            )
            if self.current_remaining_amount <= 0:
                self._stop_bill_acceptor_for_payment()
                self.goto_screen("payment_complete_success")

    def _handle_coupon_success(self, code: str, coupon_value: Optional[int] = None) -> None:
        self.current_payment_method = "coupon"
        self.payment_method = "coupon"
        self.current_coupon_code = str(code)
        self.coupon_code = self.current_coupon_code
        self.pending_coupon_code = self.current_coupon_code
        if coupon_value is None:
            resolved_coupon_value = self._resolve_coupon_value(code)
        else:
            resolved_coupon_value = max(0, self._safe_int(coupon_value, 0))
        self.current_coupon_value = resolved_coupon_value
        self.coupon_value = int(self.current_coupon_value)
        required = self.current_required_amount if self.current_required_amount > 0 else self._refresh_required_amount()
        self.current_inserted_amount = 0
        self.current_remaining_amount = max(0, required - self.current_coupon_value)
        self._sync_payment_state_to_session()
        print(
            f"[COUPON] ok code={code} value={self.current_coupon_value} "
            f"required={required} remaining={self.current_remaining_amount}"
        )
        if self.current_remaining_amount <= 0:
            self.goto_screen("payment_complete_success")
        else:
            self.goto_screen("coupon_remaining_method")

    def _continue_from_select_photo(self) -> bool:
        select_photo_screen = self.screens.get("select_photo")
        if not isinstance(select_photo_screen, SelectPhotoScreen):
            print("[SELECT_PHOTO] next blocked: select_photo screen missing")
            return False
        if self.is_ai_mode_active():
            selected_paths = [p for p in select_photo_screen.get_selected_paths() if isinstance(p, Path) and p.is_file()]
            selected_source_paths = [
                p for p in select_photo_screen.get_selected_source_paths() if isinstance(p, Path) and p.is_file()
            ]
            if len(selected_paths) < AI_SELECT_SLOTS:
                print(f"[SELECT_PHOTO] ai_mode blocked: incomplete {len(selected_paths)}/{AI_SELECT_SLOTS}")
                select_photo_screen.show_notice("사진 2장을 선택해주세요", duration_ms=1000)
                return False
            if not self._prepare_ai_selected_paths_from_captures(selected_paths, selected_source_paths):
                select_photo_screen.show_notice("촬영 원본이 부족합니다", duration_ms=1000)
                return False
            print("[SELECT_PHOTO] ai_mode -> select_design (2 selected)")
            self.goto_screen("select_design")
            return True

        selected_paths = select_photo_screen.get_selected_paths()
        total_slots = len(selected_paths)
        filled_slots = select_photo_screen.selected_filled_count()
        if total_slots <= 0:
            print("[SELECT_PHOTO] next blocked: no slots")
            select_photo_screen.show_notice("사진을 모두 선택해주세요", duration_ms=1000)
            return False
        if filled_slots < total_slots:
            print(f"[SELECT_PHOTO] next blocked: incomplete {filled_slots}/{total_slots}")
            select_photo_screen.show_notice("사진을 모두 선택해주세요", duration_ms=1000)
            return False

        resolved_selected = [str(path) for path in selected_paths if path is not None]
        self.selected_print_paths = resolved_selected
        self.print_slots = total_slots
        self.current_print_slots = total_slots
        print(f"[SELECT_PHOTO] next ok selected={total_slots} -> select_design")
        self.goto_screen("select_design")
        return True

    @staticmethod
    def _design_sort_key(path: Path) -> tuple[int, int, str]:
        stem = path.stem.strip()
        if stem.isdigit():
            return (0, int(stem), path.name.lower())
        match = re.search(r"\d+", stem)
        if match:
            return (1, int(match.group(0)), path.name.lower())
        return (2, 0, path.name.lower())

    def _resolve_default_frame_path(self, layout_id: Optional[str]) -> Optional[Path]:
        if not layout_id:
            print("[SELECT_DESIGN] default frame blocked: layout_id missing")
            return None
        frame_dir = (
            ROOT_DIR
            / "assets"
            / "ui"
            / "10_select_Design"
            / "Frame"
            / "Frame2"
            / layout_id
        )
        if not frame_dir.is_dir():
            print(f"[SELECT_DESIGN] frame dir missing: {frame_dir}")
            return None
        preferred = frame_dir / "1.png"
        if preferred.is_file():
            return preferred
        png_files = [p for p in frame_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"]
        if not png_files:
            print(f"[SELECT_DESIGN] frame png missing: {frame_dir}")
            return None
        return sorted(png_files, key=self._design_sort_key)[0]

    def _prepare_share_files(
        self,
        session: Session,
        print_path: Path,
        frame_path: Optional[Path],
    ) -> dict[str, Optional[Path]]:
        share_dir = ensure_share_dir(session.session_dir)
        out_print = share_dir / "print.jpg"
        out_frame = share_dir / "frame.png"
        out_video = share_dir / "video.gif"
        out_meta = share_dir / "share.json"

        try:
            if print_path.is_file():
                shutil.copy2(print_path, out_print)
                print(f"[SHARE] copy print -> {out_print}")
            else:
                print(f"[SHARE] print missing: {print_path}")
        except Exception as exc:
            print(f"[SHARE] copy print failed: {exc}")

        chosen_frame = frame_path
        if chosen_frame is None or not chosen_frame.is_file():
            chosen_frame = self._resolve_default_frame_path(self.current_layout_id)
        try:
            if chosen_frame is not None and chosen_frame.is_file():
                shutil.copy2(chosen_frame, out_frame)
                print(f"[SHARE] copy frame -> {out_frame}")
            else:
                print("[SHARE] frame missing")
        except Exception as exc:
            print(f"[SHARE] copy frame failed: {exc}")

        return {
            "share_dir": share_dir,
            "print": out_print if out_print.is_file() else None,
            "frame": out_frame if out_frame.is_file() else None,
            "video": out_video if out_video.is_file() else None,
            "meta": out_meta,
        }

    def _get_session_print_job_path(self) -> Optional[Path]:
        session = self.get_active_session()
        if session is None:
            return None
        raw = getattr(session, "print_job_path", None)
        if not isinstance(raw, str) or not raw.strip():
            return None
        candidate = Path(raw)
        if not candidate.is_file():
            return None
        return candidate

    def _set_preview_from_print_job(self) -> bool:
        preview_screen = self.screens.get("preview")
        if not isinstance(preview_screen, PreviewScreen):
            return False
        print_job_path = self._get_session_print_job_path()
        if print_job_path is None:
            print("[PREVIEW] missing print_job_path -> back to select_design")
            self.goto_screen("select_design")
            return False
        preview_screen.set_layout(self.current_layout_id)
        preview_screen.set_print_image(str(print_job_path))
        return True

    def _continue_from_select_design(self) -> bool:
        layout_id = self.current_layout_id
        if not layout_id:
            print("[SELECT_DESIGN] next blocked: layout_id missing")
            return False

        select_design_screen = self.screens.get("select_design")
        if not isinstance(select_design_screen, SelectDesignScreen):
            print("[SELECT_DESIGN] next blocked: screen missing")
            return False

        frame_index = int(select_design_screen.frame_index)
        selected_paths = list(select_design_screen.selected_print_paths)
        print(
            f"[SELECT_DESIGN] confirm clicked layout={layout_id} "
            f"frame={frame_index} selected={len(selected_paths)}"
        )
        assets = resolve_design_asset_paths(layout_id, frame_index)
        print(
            f"[SELECT_DESIGN] assets frame1={assets.get('frame1_path')} "
            f"frame2={assets.get('frame2_path')} showing={assets.get('preview_frame_path')}"
        )

        self.selected_print_paths = [str(p) for p in select_design_screen.selected_print_paths]
        photos = [Path(p) for p in self.selected_print_paths if p]
        expected_slots = max(1, int(self.current_print_slots or self.print_slots or len(photos)))
        has_none = any(p is None for p in selected_paths)
        if (not photos) or has_none or (len(photos) < expected_slots):
            print("[SELECT_DESIGN] confirm blocked: selection incomplete")
            select_design_screen.show_notice("사진을 모두 선택해주세요", duration_ms=1000)
            return False

        missing = [p for p in photos if not p.is_file()]
        if missing:
            print("[SELECT_DESIGN] confirm blocked: selection incomplete")
            select_design_screen.show_notice("사진을 모두 선택해주세요", duration_ms=1000)
            return False

        session = self.get_active_session()
        if session is None:
            print("[SELECT_DESIGN] next blocked: session missing")
            return False

        loading_screen = self.screens.get("loading")
        if isinstance(loading_screen, LoadingScreen):
            loading_screen.set_status_message(
                "합성중 0%\nComposing 0%\n잠시만 기다려주세요\nPlease wait",
                animate=False,
            )
        self.goto_screen("loading")
        try:
            app = QApplication.instance()
            if app is not None:
                app.processEvents()
        except Exception:
            pass

        out_print = session.print_dir / "print.jpg"
        try:
            def _on_compose_progress(percent: int, ko: str, en: str) -> None:
                safe = max(0, min(100, int(percent)))
                if isinstance(loading_screen, LoadingScreen):
                    loading_screen.set_status_message(
                        f"{str(ko or '합성중')} {safe}%\n"
                        f"{str(en or 'Composing')} {safe}%\n"
                        "잠시만 기다려주세요\nPlease wait",
                        animate=False,
                    )
                try:
                    inner_app = QApplication.instance()
                    if inner_app is not None:
                        inner_app.processEvents()
                except Exception:
                    pass

            composed, frame_path, slot_count, copies_per_page = select_design_screen.build_final_print(
                progress_cb=_on_compose_progress
            )
            print_path = session.save_print(composed, filename="print.jpg")
            _on_compose_progress(100, "합성 완료", "Composition complete")
            print(
                f"[DESIGN] confirm built print.jpg w={composed.width} h={composed.height} "
                f"slots={slot_count} copies_per_page={copies_per_page}"
            )
        except Exception as exc:
            print(f"[SELECT_DESIGN] confirm FAILED {exc}")
            if isinstance(loading_screen, LoadingScreen):
                loading_screen.clear_status_message()
            self.goto_screen("select_design")
            select_design_screen.show_notice("합성 실패", duration_ms=1000)
            return False

        print_job_path = out_print if out_print.is_file() else print_path
        requested_raw = getattr(session, "print_count", self.current_print_count or self.print_count or 2)
        try:
            requested = int(requested_raw)
        except Exception:
            requested = 2
        requested = max(2, min(10, requested))
        if requested % 2 != 0:
            requested -= 1
        if requested < 2:
            requested = 2
        strip_layouts = self.get_strip_2x6_layouts()
        if layout_id in strip_layouts:
            print_job_copies = max(1, requested // 2)  # sets
            print_job_size = "2x6x2"
            print_job_mode = "strip_split"
            print(
                f"[PRINT_MODE] strip layout={layout_id} job={print_job_path} "
                f"print_count={requested} sets={print_job_copies} size={print_job_size}"
            )
        else:
            print_job_copies = requested
            print_job_size = "4x6"
            print_job_mode = "full"
            print(
                f"[PRINT_MODE] full layout={layout_id} job={print_job_path} "
                f"requested={requested} copies={print_job_copies} size={print_job_size}"
            )

        session.print_job_path = str(print_job_path)
        session.print_job_copies = int(print_job_copies)
        session.print_job_size = str(print_job_size)
        session.print_job_mode = str(print_job_mode)
        print(f"[SELECT_DESIGN] confirm saved print_job_path={session.print_job_path}")

        share_files = self._prepare_share_files(session, print_path, frame_path)

        self.current_design_index = int(select_design_screen.frame_index)
        self.current_design_path = str(frame_path)
        self.current_design_is_gray = bool(select_design_screen.is_gray)
        self.current_design_flip_horizontal = bool(select_design_screen.flip_horizontal)
        self.current_design_qr_enabled = bool(select_design_screen.qr_enabled)
        self.current_print_path = str(print_path)
        self.current_print_job_path = str(print_job_path)
        self.current_print_job_copies = int(print_job_copies)
        self.current_print_job_size = str(print_job_size)
        self.current_print_job_mode = str(print_job_mode)
        session.set_context(layout_id=layout_id, design_path=self.current_design_path)
        session.qr_enabled = bool(self.current_design_qr_enabled)
        try:
            session.clear_share()
        except Exception:
            pass

        print(
            f"[SELECT_DESIGN] confirm -> print saved={print_path} "
            f"frame={self.current_design_index} "
            f"gray={1 if self.current_design_is_gray else 0} "
            f"flip={1 if self.current_design_flip_horizontal else 0} "
            f"qr={1 if self.current_design_qr_enabled else 0} "
            f"job={print_job_path} job_size={print_job_size} copies={print_job_copies} "
            f"share_print={share_files.get('print')} share_frame={share_files.get('frame')}"
        )
        print("[NAV] select_design -> loading")
        started = self._start_print_pipeline()
        if not started:
            if isinstance(loading_screen, LoadingScreen):
                loading_screen.clear_status_message()
            self.goto_screen("select_design")
            select_design_screen.show_notice("인쇄 준비 실패", duration_ms=1000)
        return started

    def handle_payment_complete_success(self) -> None:
        if self._prepare_camera_entry(skip_health_check=True):
            self.goto_screen("camera")
            return
        print("[PAYMENT_COMPLETE] camera transition failed -> fallback frame_select")
        self._show_runtime_notice("카메라 화면 전환 실패: 프레임 선택으로 복귀합니다", duration_ms=1200)
        self.goto_screen("frame_select")

    def _resolve_printer_name(self) -> str:
        return self._resolve_printer_name_for_model("DS620", self.get_printing_settings())

    def _resolve_canon_edsdk_dll_path(self) -> str:
        default_path = (
            "C:\\Program Files (x86)\\Canon\\EOS Network Setting Tool\\runtimes\\windows\\native\\EDSDK.dll"
        )
        data = self._read_config_dict()

        if isinstance(data, dict):
            value = data.get("canon_edsdk_dll_path")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return default_path

    def _resolve_camera_backend(self) -> str:
        config = self._read_config_dict()
        admin = config.get("admin") if isinstance(config, dict) else None
        settings = self._normalize_admin_settings(admin)
        backend = self._resolve_requested_camera_backend(settings)
        return backend

    def _start_print_from_preview(self) -> None:
        preview_screen = self.screens.get("preview")
        if not isinstance(preview_screen, PreviewScreen):
            return
        if preview_screen.confirm_locked:
            print("[PRINT] confirm blocked: already in progress")
            return
        self._start_print_pipeline()

    def _start_print_pipeline(self) -> bool:
        session = self.get_active_session()
        if session is None:
            print("[PREVIEW] missing print_job_path -> back to select_design")
            self.goto_screen("select_design")
            return False

        image_path: Optional[Path] = None
        session_path = getattr(session, "print_job_path", None)
        if isinstance(session_path, str) and session_path.strip():
            candidate = Path(session_path)
            if candidate.is_file():
                image_path = candidate
        if image_path is None:
            print("[PREVIEW] missing print_job_path -> back to select_design")
            self.goto_screen("select_design")
            return False

        try:
            copies = max(1, int(getattr(session, "print_job_copies", 2)))
        except Exception:
            copies = 2
        job_size = str(getattr(session, "print_job_size", "4x6") or "4x6").strip() or "4x6"
        job_mode = str(getattr(session, "print_job_mode", "full") or "full").strip().lower()
        strip_split = job_mode == "strip_split"
        if strip_split and copies < 1:
            copies = 1

        self.current_print_job_path = str(image_path)
        self.current_print_job_copies = int(copies)
        self.current_print_job_size = str(job_size)
        self.current_print_job_mode = job_mode
        printing_settings = self.get_printing_settings()
        model = self._resolve_print_model(printing_settings)

        def _has_model_candidates(check_model: str) -> bool:
            primary = self._resolve_printer_name_for_model(check_model, printing_settings)
            items = self._resolve_printer_candidates_for_model(
                model=check_model,
                primary_name=primary,
                settings=printing_settings,
            )
            if strip_split and items:
                physical_only = [name for name in items if not self._is_virtual_printer_name(name)]
                if physical_only:
                    items = physical_only
            return bool(items)

        # New installations can be RX1HS-only. Avoid pinning to DS620 default
        # when the alternate printer model is the only one installed.
        if model in {"DS620", "RX1HS"}:
            alt_model = "RX1HS" if model == "DS620" else "DS620"
            if not _has_model_candidates(model) and _has_model_candidates(alt_model):
                print(f"[PRINT] default model auto-switch {model}->{alt_model} reason=no_candidates")
                model = alt_model

        forced_printer_name: Optional[str] = None
        use_driver_default_form = False
        if strip_split:
            strip_name = self._resolve_dedicated_strip_queue_name(printing_settings)
            if strip_name:
                model = "DS620_STRIP"
                forced_printer_name = strip_name
                print(f"[PRINT] strip queue override model={model} win_name=\"{strip_name}\"")
                # Dedicated strip queues are configured to output 2x6x2 at driver level.
                # If app-side split is also enabled, one set(2 prints) can become 4 pieces
                # and center-cut artifacts can appear on some DS620/RX1HS setups.
                strip_split = False
                use_driver_default_form = True
                print("[PRINT_MODE] dedicated strip queue active -> app split disabled")
                print("[PRINT_FORM] dedicated strip queue -> use driver default form/cut")
            else:
                print("[PRINT_MODE] strip queue override skipped: dedicated DS620_STRIP queue not found")
        printer_name = forced_printer_name or self._resolve_printer_name_for_model(model, printing_settings)
        exists = image_path.is_file()
        size = image_path.stat().st_size if exists else 0
        print(f"[PRINT] request image={image_path} exists={1 if exists else 0} size={size}")
        print(
            f"[PRINT] mode enabled={1 if printing_settings.get('enabled', True) else 0} "
            f"dry_run={1 if printing_settings.get('dry_run', False) else 0} "
            f"test_mode={1 if self.is_test_mode() else 0}"
        )
        print(
            f"[PRINT] target model={model} win_name=\"{printer_name}\" "
            f"copies={max(1, int(copies))}"
        )
        form_job_size = "2x6" if strip_split else job_size
        form_name = self._resolve_printer_form_name_for_job(model, form_job_size, printing_settings)
        if use_driver_default_form:
            form_name = ""
            print("[PRINT_FORM] dedicated strip queue -> use driver default form/cut")
        if strip_split and not _is_likely_2x6_form_name(form_name):
            # Keep strip mode and force canonical 2x6 target name so win_print_image
            # can apply named form or custom DEVMODE size.
            print(
                "[PRINT_MODE] strip form override: "
                f"invalid configured 2x6 form \"{form_name}\" -> \"2x6\""
            )
            form_name = "2x6"
        print(f"[PRINT_FORM] selected model={model} size={job_size} form=\"{form_name}\"")
        should_check_printer = bool(printing_settings.get("enabled", True))
        should_check_printer = should_check_printer and not bool(printing_settings.get("dry_run", False))
        should_check_printer = should_check_printer and not bool(self.is_test_mode())
        if should_check_printer:
            def _reselect_model_candidates(reason: str) -> list[str]:
                nonlocal model, printer_name, form_name
                if strip_split:
                    if model == "DS620_STRIP":
                        alt_model = "RX1HS"
                    elif model == "RX1HS":
                        alt_model = "DS620"
                    elif model == "DS620":
                        alt_model = "RX1HS"
                    else:
                        alt_model = ""
                else:
                    alt_model = "RX1HS" if model in {"DS620", "DS620_STRIP"} else "DS620"
                if alt_model == model:
                    return []
                if not alt_model:
                    return []
                alt_candidates = self._resolve_printer_candidates_for_model(
                    model=alt_model,
                    primary_name=self._resolve_printer_name_for_model(alt_model, printing_settings),
                    settings=printing_settings,
                )
                if not alt_candidates:
                    return []

                previous_model = model
                model = alt_model
                printer_name = str(alt_candidates[0]).strip() or printer_name
                fallback_form_size = "2x6" if strip_split else job_size
                form_name = self._resolve_printer_form_name_for_job(model, fallback_form_size, printing_settings)
                if use_driver_default_form:
                    form_name = ""
                    print("[PRINT_FORM] dedicated strip queue -> use driver default form/cut")
                if strip_split and not _is_likely_2x6_form_name(form_name):
                    print(
                        "[PRINT_MODE] strip form override: "
                        f"invalid configured 2x6 form \"{form_name}\" -> \"2x6\""
                    )
                    form_name = "2x6"
                print(
                    f"[PRINT] route fallback model={previous_model}->{model} "
                    f"reason={reason} printer=\"{printer_name}\""
                )
                print(f"[PRINT_FORM] selected model={model} size={job_size} form=\"{form_name}\"")
                return alt_candidates

            candidates = self._resolve_printer_candidates_for_model(
                model=model,
                primary_name=printer_name,
                settings=printing_settings,
            )
            if strip_split and candidates:
                physical_only = [name for name in candidates if not self._is_virtual_printer_name(name)]
                if physical_only:
                    candidates = physical_only
            if not candidates:
                candidates = _reselect_model_candidates("no_candidates")
            if strip_split and candidates:
                physical_only = [name for name in candidates if not self._is_virtual_printer_name(name)]
                if physical_only:
                    candidates = physical_only
            if not candidates:
                if strip_split:
                    self._show_runtime_notice("소형프레임용 프린터(STRIP)를 찾을 수 없습니다.", duration_ms=1800)
                    print("[PRINT] blocked: no strip printer candidates (physical)")
                    return False
                self._show_runtime_notice("사용 가능한 프린터를 찾을 수 없습니다.", duration_ms=1500)
                print(f"[PRINT] blocked: no installed printer candidates model={model}")
                return False
            if candidates:
                printer_name = str(candidates[0]).strip() or printer_name
            first_fail_msg = ""
            selected_ok = False
            for cand in candidates:
                p_ok, p_msg = self.check_runtime_printer_health(model, cand)
                if p_ok:
                    if cand != printer_name:
                        print(
                            f"[PRINT] health fallback selected model={model} "
                            f"printer=\"{cand}\" (from \"{printer_name}\")"
                        )
                    printer_name = cand
                    selected_ok = True
                    break
                if not first_fail_msg:
                    first_fail_msg = str(p_msg)

            if not selected_ok:
                hard_block = str(os.environ.get("KIOSK_PRINT_BLOCK_ON_HEALTH_FAIL", "0")).strip().lower()
                should_block = hard_block in {"1", "true", "yes", "on"}
                if should_block:
                    self._show_runtime_notice(
                        "프린터가 오프라인입니다. 프린터를 연결해주세요.",
                        duration_ms=1500,
                    )
                    print(
                        f"[PRINT] blocked offline printer=\"{printer_name}\" "
                        f"msg=\"{first_fail_msg or 'health_check_failed'}\" "
                        "policy=block"
                    )
                    return False
                print(
                    f"[PRINT] health warning ignored model={model} printer=\"{printer_name}\" "
                    f"msg=\"{first_fail_msg or 'health_check_failed'}\" policy=soft"
                )
        loading_screen = self.screens.get("loading")
        if isinstance(loading_screen, LoadingScreen):
            loading_screen.set_status_message("PRINTING\n인쇄중", animate=True)
        self.goto_screen("loading")
        self._start_print_worker(
            printer_name,
            image_path,
            copies=copies,
            job_size=job_size,
            model=model,
            form_name=form_name,
            strip_split=strip_split,
            strip_sets=max(1, int(copies)) if strip_split else 1,
            layout_id=self.current_layout_id,
        )
        return True

    def _start_print_worker(
        self,
        printer_name: str,
        image_path: Path,
        copies: int = 2,
        job_size: str = "4x6",
        model: str = "DS620",
        form_name: str = "",
        strip_split: bool = False,
        strip_sets: int = 1,
        layout_id: Optional[str] = None,
    ) -> None:
        if self.print_thread is not None and self.print_thread.isRunning():
            print("[PRINT] worker already running")
            return

        preview_screen = self.screens.get("preview")
        safe_copies = max(1, int(copies))
        printing_settings = self.get_printing_settings()
        worker = MainPrintWorker(
            image_path=image_path,
            printer_name=printer_name,
            copies=safe_copies,
            model=model,
            form_name=form_name,
            strip_split=bool(strip_split),
            strip_sets=max(1, int(strip_sets)),
            layout_id=layout_id,
            enabled=bool(printing_settings.get("enabled", True)),
            dry_run=bool(printing_settings.get("dry_run", False)),
            test_mode=bool(self.is_test_mode()),
        )
        self._active_print_context = {
            "model": str(model or "DS620"),
            "enabled": bool(printing_settings.get("enabled", True)),
            "dry_run": bool(printing_settings.get("dry_run", False)),
            "test_mode": bool(self.is_test_mode()),
            "strip_split": bool(strip_split),
            "strip_sets": max(1, int(strip_sets)),
            "copies": int(safe_copies),
        }
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.success.connect(self._on_print_success)
        worker.failure.connect(self._on_print_failure)
        worker.success.connect(thread.quit)
        worker.failure.connect(thread.quit)
        worker.success.connect(worker.deleteLater)
        worker.failure.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_print_thread_finished)

        self.print_worker = worker
        self.print_thread = thread
        print(f"[PRINT_MODE] size hint={job_size} (driver default)")
        if strip_split:
            total_parts = max(1, int(strip_sets)) * 2
            for index in range(1, total_parts + 1):
                print(f"[PRINT_JOB] start i={index}/{total_parts} path={image_path}")
        else:
            for index in range(1, safe_copies + 1):
                print(f"[PRINT_JOB] start i={index}/{safe_copies} path={image_path}")
        print(
            f"[PRINT] start printer={printer_name} image={image_path} "
            f"copies={safe_copies} size={job_size} form=\"{form_name}\" "
            f"strip_split={1 if strip_split else 0}"
        )
        thread.start()

        if isinstance(preview_screen, PreviewScreen):
            preview_screen.set_confirm_locked(True)

    def _create_admin_test_print_image(self, model: str) -> Path:
        out_dir = _resolve_runtime_out_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"admin_print_test_{str(model).upper()}.jpg"
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        image = Image.new("RGB", (1200, 1800), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        title = f"TEST PRINT {str(model).upper()}"
        draw.text((80, 120), title, fill=(0, 0, 0))
        draw.text((80, 220), now_text, fill=(0, 0, 0))
        draw.rectangle((70, 320, 1130, 1710), outline=(0, 0, 0), width=6)
        image.save(out_path, format="JPEG", quality=95)
        return out_path

    def resolve_admin_printer_name(
        self,
        model: str,
        printing_override: Optional[dict] = None,
    ) -> str:
        cfg = self._normalize_printing_settings(
            printing_override if isinstance(printing_override, dict) else self.get_printing_settings()
        )
        model_key = str(model or self._resolve_print_model(cfg)).strip().upper()
        if model_key not in {"DS620", "DS620_STRIP", "RX1HS"}:
            model_key = "DS620"
        return self._resolve_printer_name_for_model(model_key, cfg)

    def run_admin_printer_health_check(
        self,
        model: str,
        printing_override: Optional[dict] = None,
    ) -> tuple[bool, str]:
        cfg = self._normalize_printing_settings(
            printing_override if isinstance(printing_override, dict) else self.get_printing_settings()
        )
        model_key = str(model or self._resolve_print_model(cfg)).strip().upper()
        if model_key not in {"DS620", "DS620_STRIP", "RX1HS"}:
            model_key = "DS620"
        printer_name = self._resolve_printer_name_for_model(model_key, cfg)
        ok, msg = self.check_runtime_printer_health(model_key, printer_name)
        print(
            f"[PRINT] health_check model={model_key} printer=\"{printer_name}\" "
            f"ok={1 if ok else 0} msg=\"{msg}\""
        )
        return ok, msg

    def run_admin_print_test(self, model: str, printing_override: Optional[dict] = None) -> bool:
        cfg = self._normalize_printing_settings(
            printing_override if isinstance(printing_override, dict) else self.get_printing_settings()
        )
        model_key = str(model or self._resolve_print_model(cfg)).strip().upper()
        if model_key not in {"DS620", "DS620_STRIP", "RX1HS"}:
            model_key = "DS620"
        printer_name = self._resolve_printer_name_for_model(model_key, cfg)
        form_name = self._resolve_printer_form_name_for_job(model_key, "4x6", cfg)
        image_path = self._create_admin_test_print_image(model_key)
        exists = image_path.is_file()
        size = image_path.stat().st_size if exists else 0
        enabled = bool(cfg.get("enabled", True))
        dry_run = bool(cfg.get("dry_run", False))
        test_mode = bool(self.is_test_mode())

        print(f"[PRINT_TEST] start model={model_key} printer=\"{printer_name}\"")
        print(f"[PRINT] request image={image_path} exists={1 if exists else 0} size={size}")
        print(
            f"[PRINT] mode enabled={1 if enabled else 0} "
            f"dry_run={1 if dry_run else 0} test_mode={1 if test_mode else 0}"
        )
        print(
            f"[PRINT] target model={model_key} win_name=\"{printer_name}\" "
            f"copies=1 form=\"{form_name}\""
        )

        try:
            if not enabled:
                print("[PRINT] blocked: printing.enabled=0")
                if test_mode:
                    print("[PRINT_TEST] ok (disabled+test_mode)")
                    return True
                return False
            if dry_run or test_mode:
                reason = "dry_run" if dry_run else "test_mode"
                print(f"[PRINT] DRY_RUN reason={reason}")
                print("[PRINT_TEST] ok")
                return True
            win_print_image(printer_name, str(image_path), copies=1, form_name=form_name)
            print(f"[PRINT] sent to spooler ok printer=\"{printer_name}\" copies=1")
            print("[PRINT_TEST] ok")
            return True
        except Exception as exc:
            print(f"[PRINT] ERROR {exc!r}")
            print(f"[PRINT_TEST] fail {exc}")
            return False

    def _build_share_urls(self, session: Session) -> dict:
        share_cfg = self.get_share_settings()
        base_page_url = str(share_cfg.get("base_page_url", DEFAULT_SHARE_SETTINGS["base_page_url"])).rstrip("/")
        base_file_url = str(share_cfg.get("base_file_url", DEFAULT_SHARE_SETTINGS["base_file_url"])).rstrip("/")
        session_id = session.session_id or session.session_dir.name
        page_url = f"{base_page_url}/{session_id}"
        frame_url = f"{base_file_url}/{session_id}/frame.png"
        image_url = f"{base_file_url}/{session_id}/print.jpg"
        video_url = f"{base_file_url}/{session_id}/video.gif"
        return {
            "session_id": session_id,
            "page_url": page_url,
            "frame_url": frame_url,
            "image_url": image_url,
            "video_url": video_url,
        }

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except Exception:
            return int(default)

    @staticmethod
    def _normalize_film_model(model: str) -> str:
        key = str(model or "").strip().upper()
        if key == "DS620_STRIP":
            return "DS620"
        if key not in {"DS620", "RX1HS"}:
            return "DS620"
        return key

    @staticmethod
    def _env_optional_nonnegative_int(name: str) -> Optional[int]:
        raw = str(os.environ.get(name, "")).strip()
        if not raw:
            return None
        try:
            parsed = int(raw)
        except Exception:
            return None
        if parsed < 0:
            return None
        return parsed

    def _save_film_remaining_state_unlocked(self) -> None:
        payload = {
            "models": dict(self._film_remaining_by_model),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            _write_json_atomic(self._film_state_path, payload)
        except Exception as exc:
            self._switch_runtime_storage_to_fallback(f"film_state_write_failed:{exc}")
            _write_json_atomic(Path(self._film_state_path), payload)

    def _load_film_remaining_state_unlocked(self) -> dict[str, int]:
        path = Path(self._film_state_path)
        if not path.is_file():
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[FILM] state load failed path={path} err={exc}")
            return {}
        models = raw.get("models") if isinstance(raw, dict) else None
        if not isinstance(models, dict):
            return {}
        loaded: dict[str, int] = {}
        for key, value in models.items():
            model = self._normalize_film_model(str(key))
            parsed = self._safe_int(value, -1)
            if parsed >= 0:
                loaded[model] = parsed
        return loaded

    def _init_film_remaining_state(self) -> None:
        printing = self.get_printing_settings()
        printers = printing.get("printers", {}) if isinstance(printing, dict) else {}
        default_model = self._normalize_film_model(str(printing.get("default_model", "DS620")))

        env_global = self._env_optional_nonnegative_int("KIOSK_FILM_REMAINING")
        env_ds620 = self._env_optional_nonnegative_int("KIOSK_FILM_REMAINING_DS620")
        env_rx1hs = self._env_optional_nonnegative_int("KIOSK_FILM_REMAINING_RX1HS")
        env_values = {
            "DS620": env_ds620,
            "RX1HS": env_rx1hs,
        }
        if env_global is not None and env_values.get(default_model) is None:
            env_values[default_model] = env_global

        config_values: dict[str, Optional[int]] = {"DS620": None, "RX1HS": None}
        if isinstance(printers, dict):
            for model in ("DS620", "RX1HS"):
                item = printers.get(model, {})
                if isinstance(item, dict):
                    parsed = self._safe_int(item.get("film_remaining"), -1)
                    if parsed >= 0:
                        config_values[model] = parsed

        with self._film_state_lock:
            saved = self._load_film_remaining_state_unlocked()
            state: dict[str, int] = {}
            for model in ("DS620", "RX1HS"):
                value = env_values.get(model)
                if value is None:
                    value = saved.get(model)
                if value is None:
                    value = config_values.get(model)
                if value is None:
                    value = int(DEFAULT_FILM_REMAINING_BY_MODEL.get(model, 400))
                state[model] = max(0, int(value))
            self._film_remaining_by_model = state
            self._save_film_remaining_state_unlocked()
        print(
            "[FILM] init "
            f"DS620={self._film_remaining_by_model.get('DS620')} "
            f"RX1HS={self._film_remaining_by_model.get('RX1HS')}"
        )

    def _get_film_remaining(self, model: str) -> Optional[int]:
        key = self._normalize_film_model(model)
        with self._film_state_lock:
            value = self._film_remaining_by_model.get(key)
        if value is None:
            return None
        return max(0, int(value))

    def _consume_film_remaining(self, model: str, used_units: int) -> None:
        key = self._normalize_film_model(model)
        consume = max(0, int(used_units))
        if consume <= 0:
            return
        with self._film_state_lock:
            before = max(0, int(self._film_remaining_by_model.get(key, 0)))
            after = max(0, before - consume)
            self._film_remaining_by_model[key] = after
            self._save_film_remaining_state_unlocked()
        print(f"[FILM] consume model={key} used={consume} remaining={after}")

    def _resolve_sale_payment_method(self, required: int, coupon_value: int) -> str:
        if self.is_test_mode():
            return "TEST"

        method = str(self.current_payment_method or "").strip().lower()
        if method == "card":
            if required > 0 and coupon_value >= required:
                return "COUPON"
            if 0 < coupon_value < required:
                return "COUPON_CASH"
            return "CARD"
        if method == "coupon":
            if required > 0 and coupon_value >= required:
                return "COUPON"
            if 0 < coupon_value < required:
                return "COUPON_CASH"
            # Coupon flow selected but value was not resolved yet.
            # Keep coupon method so server can resolve authoritative amount.
            return "COUPON"
        if method == "cash":
            if required > 0 and coupon_value >= required:
                return "COUPON"
            if 0 < coupon_value < required:
                return "COUPON_CASH"
            return "CASH"

        if 0 < coupon_value < required:
            return "COUPON_CASH"
        if coupon_value == required:
            return "COUPON"
        return "CASH"

    def _build_sale_complete_payload(self, session: Session) -> Optional[dict[str, Any]]:
        session_id = str(getattr(session, "session_id", "") or session.session_dir.name).strip()
        if not session_id:
            return None

        required = max(0, self._safe_int(getattr(session, "payment_required", self.current_required_amount), 0))
        if required <= 0:
            required = max(0, self._safe_int(self.current_required_amount, 0))
        if required <= 0:
            print("[SALES] skip: required_amount missing")
            return None

        coupon_value = max(0, self._safe_int(getattr(session, "coupon_value", self.current_coupon_value), 0))
        payment_method = self._resolve_sale_payment_method(required, coupon_value)
        coupon_code = str(
            getattr(session, "coupon_code", self.current_coupon_code)
            or self.current_coupon_code
            or self.pending_coupon_code
            or ""
        ).strip()
        original_coupon_code = coupon_code
        prints = max(1, self._safe_int(getattr(session, "print_count", self.current_print_count), 2))
        layout_id = str(self.current_layout_id or getattr(session, "layout_id", "") or "").strip()
        if not layout_id:
            layout_id = "unknown"

        # If coupon code exists, resolve authoritative amount from server when possible.
        # This prevents stale local coupon values from causing USED sync failures.
        if coupon_code and required > 0:
            try:
                server_coupon = self._verify_coupon_with_server(coupon_code, required)
            except Exception as exc:
                server_coupon = {"checked": False, "valid": False, "reason": f"EXC:{exc}"}
            if bool(server_coupon.get("checked", False)) and bool(server_coupon.get("valid", False)):
                coupon_value = max(0, self._safe_int(server_coupon.get("coupon_amount"), 0))
                payment_method = self._resolve_sale_payment_method(required, coupon_value)
                print(
                    f"[SALES] coupon value restored from server code={coupon_code} "
                    f"value={coupon_value} method={payment_method}"
                )

        if payment_method in {"CASH", "CARD", "TEST"}:
            amount_coupon = 0
            amount_cash = required
            # Keep coupon_code on CASH so server can reconcile coupon usage
            # when kiosk-side coupon amount is stale/missing.
            if payment_method in {"TEST"}:
                coupon_code = ""
        elif payment_method == "COUPON":
            if not coupon_code:
                print("[SALES] skip: coupon_code missing for COUPON")
                return None
            amount_coupon = required
            amount_cash = 0
        else:  # COUPON_CASH
            if not coupon_code:
                print("[SALES] skip: coupon_code missing for COUPON_CASH")
                return None
            amount_coupon = max(0, min(required, coupon_value))
            amount_cash = max(0, required - amount_coupon)
            if amount_coupon <= 0:
                payment_method = "CASH"
                coupon_code = ""
                amount_coupon = 0
                amount_cash = required

        payload = {
            "session_id": session_id,
            "layout_id": layout_id,
            "prints": int(prints),
            "currency": "KRW",
            "price_total": int(required),
            "payment_method": payment_method,
            "amount_cash": int(amount_cash),
            "coupon_code": coupon_code,
            "amount_coupon": int(amount_coupon),
            "meta": {
                "compose_mode": str(self.compose_mode or "normal"),
                "ai_generated_count": 2 if str(self.compose_mode or "").strip().lower() == "ai" else 0,
                "ai_model": CHEAPEST_GEMINI_IMAGE_MODEL
                if str(self.compose_mode or "").strip().lower() == "ai"
                else "",
                "kiosk_required_amount": int(required),
                "kiosk_coupon_value": int(coupon_value),
                "kiosk_coupon_code": str(original_coupon_code or ""),
                "kiosk_inserted_amount": int(self._safe_int(getattr(session, "payment_inserted", self.current_inserted_amount), 0)),
            },
        }
        print(
            f"[SALES] payload session={session_id} method={payment_method} "
            f"required={required} cash={amount_cash} coupon={amount_coupon} "
            f"coupon_code={coupon_code or '-'}"
        )
        return payload

    def _is_sale_already_reported(self, session_id: str) -> bool:
        with self._sale_report_lock:
            return session_id in self._reported_sale_sessions

    def _mark_sale_reported(self, session_id: str) -> None:
        with self._sale_report_lock:
            self._reported_sale_sessions.add(session_id)

    def _build_kiosk_api_auth_headers(self) -> dict[str, str]:
        share_cfg = self.get_share_settings()
        device_code = str(share_cfg.get("device_code", "")).strip() or str(os.environ.get("KIOSK_DEVICE_CODE", "")).strip()
        device_token = str(share_cfg.get("device_token", "")).strip() or str(os.environ.get("KIOSK_DEVICE_TOKEN", "")).strip()
        if not device_code or not device_token:
            raise RuntimeError("share.device_code/device_token missing")
        return {
            "X-Device-Code": device_code,
            "X-Device-Token": device_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _sales_complete_url(self) -> str:
        share_cfg = self.get_share_settings()
        api_base = _normalize_kiosk_api_base_url(share_cfg.get("api_base_url", ""))
        if not api_base:
            api_base = _normalize_kiosk_api_base_url(DEFAULT_SHARE_SETTINGS.get("api_base_url", ""))
        if not api_base:
            raise RuntimeError("share.api_base_url missing")
        return f"{api_base}/kiosk/sales/complete"

    def _kiosk_config_url(self) -> str:
        share_cfg = self.get_share_settings()
        api_base = _normalize_kiosk_api_base_url(share_cfg.get("api_base_url", ""))
        if not api_base:
            api_base = _normalize_kiosk_api_base_url(DEFAULT_SHARE_SETTINGS.get("api_base_url", ""))
        if not api_base:
            raise RuntimeError("share.api_base_url missing")
        return f"{api_base}/kiosk/config"

    def _updates_check_url(self) -> str:
        share_cfg = self.get_share_settings()
        api_base = _normalize_kiosk_api_base_url(share_cfg.get("api_base_url", ""))
        if not api_base:
            api_base = _normalize_kiosk_api_base_url(DEFAULT_SHARE_SETTINGS.get("api_base_url", ""))
        if not api_base:
            raise RuntimeError("share.api_base_url missing")
        return f"{api_base}/kiosk/updates/check"

    def _updates_download_url(self, target_version: str) -> str:
        share_cfg = self.get_share_settings()
        api_base = _normalize_kiosk_api_base_url(share_cfg.get("api_base_url", ""))
        if not api_base:
            api_base = _normalize_kiosk_api_base_url(DEFAULT_SHARE_SETTINGS.get("api_base_url", ""))
        if not api_base:
            raise RuntimeError("share.api_base_url missing")
        params = {"platform": "win"}
        version = str(target_version or "").strip()
        if version:
            params["version"] = version
        query = urlencode(params)
        return f"{api_base}/kiosk/updates/download?{query}"

    def _coupon_check_url(self) -> str:
        share_cfg = self.get_share_settings()
        api_base = _normalize_kiosk_api_base_url(share_cfg.get("api_base_url", ""))
        if not api_base:
            api_base = _normalize_kiosk_api_base_url(DEFAULT_SHARE_SETTINGS.get("api_base_url", ""))
        if not api_base:
            raise RuntimeError("share.api_base_url missing")
        return f"{api_base}/kiosk/coupon/check"

    def _verify_coupon_with_server(self, code_digits: str, amount_due: int) -> dict[str, Any]:
        result: dict[str, Any] = {
            "checked": False,
            "valid": False,
            "coupon_amount": 0,
            "remaining_due": max(0, int(amount_due)),
            "reason": "CHECK_SKIPPED",
        }
        if requests is None:
            result["reason"] = "REQUESTS_MISSING"
            return result

        code = "".join(ch for ch in str(code_digits or "") if ch.isdigit())[:6]
        if len(code) != 6:
            result.update({"checked": True, "reason": "INVALID_FORMAT"})
            return result

        try:
            url = self._coupon_check_url()
            headers = self._build_kiosk_api_auth_headers()
        except Exception as exc:
            print(f"[COUPON] server check skipped: {exc}")
            result["reason"] = "CLIENT_NOT_CONFIGURED"
            return result

        timeout = min(8.0, self._sales_request_timeout())
        payload = {"coupon_code": code, "amount_due": max(0, int(amount_due))}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        except Exception as exc:
            print(f"[COUPON] server check request failed: {exc}")
            result["reason"] = "REQUEST_FAILED"
            return result

        lock_hit, parsed_payload = self._consume_server_lock_response(response, trigger="coupon_check_api")
        if lock_hit:
            result.update({"checked": True, "reason": "DEVICE_LOCKED"})
            return result

        if int(response.status_code) >= 400:
            body_text = str(response.text or "").replace("\n", " ").replace("\r", " ").strip()
            print(f"[COUPON] server check http={response.status_code} body={body_text[:160]}")
            result["reason"] = f"HTTP_{response.status_code}"
            return result

        data = parsed_payload if isinstance(parsed_payload, dict) else {}
        if not data:
            try:
                parsed = response.json()
                if isinstance(parsed, dict):
                    data = parsed
            except Exception:
                data = {}
        if not isinstance(data, dict):
            result["reason"] = "INVALID_RESPONSE"
            return result

        result["checked"] = True
        valid = bool(data.get("valid", False))
        reason = str(data.get("reason", "UNKNOWN")).strip() or "UNKNOWN"

        raw_coupon_amount = self._safe_int(data.get("coupon_amount"), 0)
        raw_remaining_due = self._safe_int(data.get("remaining_due"), max(0, int(amount_due)))

        # Backward/variant response compatibility:
        # - {"coupon":{"amount":...}}
        # - missing coupon_amount but provides remaining_due
        coupon_obj = data.get("coupon")
        if raw_coupon_amount <= 0 and isinstance(coupon_obj, dict):
            raw_coupon_amount = self._safe_int(coupon_obj.get("amount"), 0)
        if raw_coupon_amount <= 0 and "remaining_due" in data:
            raw_coupon_amount = max(0, int(amount_due) - max(0, raw_remaining_due))
        # If server says valid but omits amount fields, assume full-apply to avoid
        # unexpected fallback to cash/card screen in kiosk flow.
        if valid and raw_coupon_amount <= 0 and int(amount_due) > 0:
            raw_coupon_amount = int(amount_due)
            raw_remaining_due = 0
            print(
                f"[COUPON] server valid but amount missing -> assume full amount_due={amount_due}"
            )

        result["valid"] = valid
        result["coupon_amount"] = max(0, int(raw_coupon_amount))
        result["remaining_due"] = max(0, int(raw_remaining_due))
        result["reason"] = reason
        print(
            f"[COUPON] server checked code={code} valid={1 if result['valid'] else 0} "
            f"amount={result['coupon_amount']} due={payload['amount_due']} reason={result['reason']}"
        )
        return result

    def _sales_request_timeout(self) -> float:
        share_cfg = self.get_share_settings()
        raw = share_cfg.get("timeout_sec", DEFAULT_SHARE_SETTINGS.get("timeout_sec", 12.0))
        try:
            timeout = float(raw)
        except Exception:
            timeout = 12.0
        return min(45.0, max(3.0, timeout))

    def _consume_server_lock_response(self, response: Any, trigger: str) -> tuple[bool, Optional[dict[str, Any]]]:
        payload: Optional[dict[str, Any]] = None
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                payload = parsed
        except Exception:
            payload = None

        if isinstance(payload, dict):
            lock_payload = payload.get("device_lock")
            if isinstance(lock_payload, dict):
                self._apply_server_lock_payload(lock_payload, trigger=trigger)
            elif str(payload.get("reason", "")).strip().upper() == "DEVICE_LOCKED":
                self._apply_server_lock_payload(
                    {
                        "locked": True,
                        "lock_reason": str(payload.get("lock_reason", "")).strip(),
                        "locked_at": str(payload.get("locked_at", "")).strip(),
                    },
                    trigger=trigger,
                )
                return True, payload
        return False, payload

    def _offline_queue_count(self) -> int:
        with self._offline_queue_lock:
            return len(self._load_offline_queue_unlocked())

    def _load_offline_queue_unlocked(self) -> list[dict[str, Any]]:
        path = Path(self._offline_queue_path)
        if not path.is_file():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[QUEUE] load failed path={path} err={exc}")
            return []
        items = raw.get("items", []) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            return []
        normalized: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind", "")).strip().lower()
            payload = item.get("payload")
            if kind not in {"sale_complete", "heartbeat"} or not isinstance(payload, dict):
                continue
            dedupe_key = str(item.get("dedupe_key", "")).strip()
            retry_count = self._safe_int(item.get("retry_count"), 0)
            try:
                next_try_ts = float(item.get("next_try_ts", time.time()))
            except Exception:
                next_try_ts = time.time()
            try:
                created_ts = float(item.get("created_ts", next_try_ts))
            except Exception:
                created_ts = next_try_ts
            normalized.append(
                {
                    "event_id": str(item.get("event_id", "")).strip()
                    or f"{kind}-{int(created_ts * 1000)}",
                    "kind": kind,
                    "dedupe_key": dedupe_key,
                    "payload": payload,
                    "retry_count": max(0, retry_count),
                    "created_ts": created_ts,
                    "next_try_ts": next_try_ts,
                    "last_error": str(item.get("last_error", "")).strip(),
                }
            )
        return normalized

    def _save_offline_queue_unlocked(self, items: list[dict[str, Any]]) -> None:
        path = Path(self._offline_queue_path)
        payload = {"items": items, "updated_at": datetime.now().isoformat(timespec="seconds")}
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(path, payload)
        except Exception as exc:
            self._switch_runtime_storage_to_fallback(f"offline_queue_write_failed:{exc}")
            fallback = Path(self._offline_queue_path)
            fallback.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(fallback, payload)

    @staticmethod
    def _offline_retry_backoff_sec(retry_count: int) -> float:
        step = max(0, int(retry_count))
        return float(min(300, 5 * (2 ** min(step, 6))))

    @staticmethod
    def _is_non_retryable_sale_error(reason: str) -> bool:
        text = str(reason or "").upper()
        tokens = (
            "COUPON_NOT_FOUND",
            "COUPON_REQUIRED",
            "INVALID_PAYMENT_METHOD",
            "INVALID_COUPON_AMOUNT_FOR_METHOD",
            "AMOUNT_SUM_MISMATCH",
        )
        return any(token in text for token in tokens)

    @staticmethod
    def _sale_queue_max_age_sec() -> float:
        raw = str(os.environ.get("KIOSK_SALE_QUEUE_MAX_AGE_HOURS", "24")).strip()
        try:
            hours = float(raw)
        except Exception:
            hours = 24.0
        return float(max(1.0, min(168.0, hours)) * 3600.0)

    def _enqueue_offline_event(self, *, kind: str, payload: dict[str, Any], dedupe_key: str) -> None:
        event_kind = str(kind or "").strip().lower()
        if event_kind not in {"sale_complete", "heartbeat"}:
            return
        safe_payload = dict(payload) if isinstance(payload, dict) else {}
        now_ts = time.time()
        event = {
            "event_id": f"{event_kind}-{int(now_ts * 1000)}-{os.getpid()}",
            "kind": event_kind,
            "dedupe_key": str(dedupe_key or "").strip(),
            "payload": safe_payload,
            "retry_count": 0,
            "created_ts": now_ts,
            "next_try_ts": now_ts,
            "last_error": "",
        }
        with self._offline_queue_lock:
            items = self._load_offline_queue_unlocked()
            if event["dedupe_key"]:
                filtered: list[dict[str, Any]] = []
                replaced = False
                for item in items:
                    if str(item.get("dedupe_key", "")).strip() != event["dedupe_key"]:
                        filtered.append(item)
                        continue
                    if replaced:
                        continue
                    replaced = True
                    if event_kind == "sale_complete":
                        filtered.append(item)
                    else:
                        filtered.append(event)
                if not replaced:
                    filtered.append(event)
                items = filtered
            else:
                items.append(event)
            self._save_offline_queue_unlocked(items)
            print(
                f"[QUEUE] enqueue kind={event_kind} key={event['dedupe_key'] or '-'} "
                f"size={len(items)}"
            )

    def _flush_offline_queue_once(self) -> tuple[int, int]:
        now_ts = time.time()
        delivered = 0
        with self._offline_queue_lock:
            items = self._load_offline_queue_unlocked()
        if not items:
            return 0, 0
        due_items: list[dict[str, Any]] = []
        keep_items: list[dict[str, Any]] = []
        for item in items:
            try:
                next_try_ts = float(item.get("next_try_ts", now_ts))
            except Exception:
                next_try_ts = now_ts
            if now_ts < next_try_ts:
                keep_items.append(item)
            else:
                due_items.append(item)
        with self._offline_queue_lock:
            self._save_offline_queue_unlocked(keep_items)

        requeue_items: list[dict[str, Any]] = []
        stale_age_sec = self._sale_queue_max_age_sec()
        for item in due_items:
            kind = str(item.get("kind", "")).strip().lower()
            payload = item.get("payload")
            if not isinstance(payload, dict):
                continue
            try:
                created_ts = float(item.get("created_ts", now_ts))
            except Exception:
                created_ts = now_ts
            if kind == "sale_complete" and (now_ts - created_ts) > stale_age_sec:
                age_hours = (now_ts - created_ts) / 3600.0
                print(
                    f"[QUEUE] drop kind={kind} key={str(item.get('dedupe_key', '')).strip() or '-'} "
                    f"reason=stale age_h={age_hours:.1f} limit_h={stale_age_sec / 3600.0:.1f}"
                )
                continue
            ok = False
            reason = "unknown"
            if kind == "sale_complete":
                ok, reason = self._send_sale_complete_request(payload)
                if ok:
                    session_id = str(payload.get("session_id", "")).strip()
                    if session_id:
                        self._mark_sale_reported(session_id)
            elif kind == "heartbeat":
                ok, reason = self._send_heartbeat_request(payload=payload)
            else:
                continue
            if ok:
                delivered += 1
                print(
                    f"[QUEUE] delivered kind={kind} key={str(item.get('dedupe_key', '')).strip() or '-'}"
                )
                continue
            if kind == "sale_complete" and self._is_non_retryable_sale_error(reason):
                print(
                    f"[QUEUE] drop kind={kind} key={str(item.get('dedupe_key', '')).strip() or '-'} "
                    f"reason=non-retryable({reason})"
                )
                continue
            if str(reason).strip().upper().startswith("DEVICE_LOCKED"):
                print(
                    f"[QUEUE] drop kind={kind} key={str(item.get('dedupe_key', '')).strip() or '-'} "
                    "reason=DEVICE_LOCKED"
                )
                continue
            retry_count = max(0, self._safe_int(item.get("retry_count"), 0) + 1)
            backoff = self._offline_retry_backoff_sec(retry_count)
            item["retry_count"] = retry_count
            item["next_try_ts"] = now_ts + backoff
            item["last_error"] = str(reason)[:240]
            requeue_items.append(item)
            print(
                f"[QUEUE] retry kind={kind} attempt={retry_count} "
                f"backoff={int(backoff)}s reason={reason}"
            )
        with self._offline_queue_lock:
            pending = self._load_offline_queue_unlocked()
            for item in requeue_items:
                dedupe_key = str(item.get("dedupe_key", "")).strip()
                kind = str(item.get("kind", "")).strip().lower()
                if dedupe_key:
                    if kind == "heartbeat":
                        pending = [
                            existing
                            for existing in pending
                            if str(existing.get("dedupe_key", "")).strip() != dedupe_key
                        ]
                        pending.append(item)
                        continue
                    if any(
                        str(existing.get("dedupe_key", "")).strip() == dedupe_key
                        for existing in pending
                    ):
                        continue
                pending.append(item)
            self._save_offline_queue_unlocked(pending)
        return delivered, len(pending)

    def _flush_offline_queue_async(self, reason: str = "manual") -> None:
        with self._offline_flush_lock:
            if self._offline_flush_inflight:
                return
            self._offline_flush_inflight = True

        def _runner() -> None:
            try:
                delivered, pending = self._flush_offline_queue_once()
                if delivered > 0:
                    print(f"[QUEUE] flush reason={reason} delivered={delivered} pending={pending}")
            finally:
                with self._offline_flush_lock:
                    self._offline_flush_inflight = False

        threading.Thread(target=_runner, daemon=True, name=f"offline-queue-{reason}").start()

    def _send_sale_complete_request(self, payload: dict[str, Any]) -> tuple[bool, str]:
        if requests is None:
            return False, "requests module not installed"
        url = self._sales_complete_url()
        headers = self._build_kiosk_api_auth_headers()
        timeout = self._sales_request_timeout()

        for attempt in range(1, 4):
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                body_text = str(response.text or "").replace("\n", " ").replace("\r", " ").strip()
                lock_hit, parsed_payload = self._consume_server_lock_response(response, trigger="sales_api")
                if lock_hit:
                    return False, "DEVICE_LOCKED"
                if int(response.status_code) >= 400:
                    reason = f"HTTP {response.status_code} {body_text[:220]}"
                    print(f"[SALES] report fail attempt={attempt} reason={reason}")
                    if self._is_non_retryable_sale_error(reason):
                        return False, reason
                    if attempt < 3:
                        time.sleep(0.5 * attempt)
                    continue
                data = parsed_payload if isinstance(parsed_payload, dict) else (response.json() if response.content else {})
                if not isinstance(data, dict):
                    data = {}
                ok = bool(data.get("ok", False))
                if not ok:
                    reason = f"ok=0 payload={str(data)[:220]}"
                    print(f"[SALES] report fail attempt={attempt} reason={reason}")
                    if attempt < 3:
                        time.sleep(0.5 * attempt)
                    continue
                sale_id = data.get("sale_id")
                created = bool(data.get("created", False))
                already_exists = bool(data.get("already_exists", False))
                return True, f"sale_id={sale_id} created={1 if created else 0} exists={1 if already_exists else 0}"
            except Exception as exc:
                reason = f"{exc}"
                print(f"[SALES] report fail attempt={attempt} reason={reason}")
                if attempt < 3:
                    time.sleep(0.5 * attempt)
        return False, "max retries reached"

    def _heartbeat_url(self) -> str:
        share_cfg = self.get_share_settings()
        api_base = _normalize_kiosk_api_base_url(share_cfg.get("api_base_url", ""))
        if not api_base:
            api_base = _normalize_kiosk_api_base_url(DEFAULT_SHARE_SETTINGS.get("api_base_url", ""))
        if not api_base:
            raise RuntimeError("share.api_base_url missing")
        return f"{api_base}/kiosk/heartbeat"

    def _build_heartbeat_payload(self) -> dict[str, Any]:
        share_cfg = self.get_share_settings()
        api_base = _normalize_kiosk_api_base_url(share_cfg.get("api_base_url", "")) if isinstance(share_cfg, dict) else ""
        internet_ok, _internet_msg = check_internet(timeout=0.8, api_base_url=api_base)
        printing_settings = self.get_printing_settings()
        printers = printing_settings.get("printers", {}) if isinstance(printing_settings, dict) else {}

        def _printer_any_ok(config_keys: tuple[str, ...]) -> bool:
            configured = False
            for config_key in config_keys:
                item = printers.get(config_key, {}) if isinstance(printers, dict) else {}
                name = str(item.get("win_name", "")).strip() if isinstance(item, dict) else ""
                if not name:
                    continue
                configured = True
                ok, _msg = get_printer_health(name)
                if bool(ok):
                    return True
            # Preserve existing behavior: when not configured, don't hard-fail heartbeat.
            return not configured

        ds620_ok = _printer_any_ok(("DS620", "DS620_STRIP"))
        rx1hs_ok = _printer_any_ok(("RX1HS",))
        printer_ok = bool(ds620_ok or rx1hs_ok)

        payload: dict[str, Any] = {
            "app_version": self._current_kiosk_app_version(),
            "internet_ok": bool(internet_ok),
            "camera_ok": True,
            "printer_ok": bool(printer_ok),
            "last_error": None,
        }
        ds620_remaining = self._get_film_remaining("DS620")
        rx1hs_remaining = self._get_film_remaining("RX1HS")

        env_all = self._env_optional_nonnegative_int("KIOSK_FILM_REMAINING")
        env_ds620 = self._env_optional_nonnegative_int("KIOSK_FILM_REMAINING_DS620")
        env_rx1hs = self._env_optional_nonnegative_int("KIOSK_FILM_REMAINING_RX1HS")
        if env_ds620 is not None:
            ds620_remaining = env_ds620
        if env_rx1hs is not None:
            rx1hs_remaining = env_rx1hs

        if ds620_remaining is not None:
            ds_payload = payload.get("printer_ds620")
            if not isinstance(ds_payload, dict):
                ds_payload = {}
            ds_payload["ok"] = bool(ds620_ok)
            ds_payload["film_remaining"] = int(ds620_remaining)
            payload["printer_ds620"] = ds_payload
        if rx1hs_remaining is not None:
            rx_payload = payload.get("printer_rx1hs")
            if not isinstance(rx_payload, dict):
                rx_payload = {}
            rx_payload["ok"] = bool(rx1hs_ok)
            rx_payload["film_remaining"] = int(rx1hs_remaining)
            payload["printer_rx1hs"] = rx_payload

        default_model = self._normalize_film_model(str(printing_settings.get("default_model", "DS620")))
        primary_remaining = ds620_remaining if default_model == "DS620" else rx1hs_remaining
        if primary_remaining is None:
            primary_remaining = ds620_remaining if ds620_remaining is not None else rx1hs_remaining
        if env_all is not None:
            primary_remaining = env_all
        if primary_remaining is not None:
            payload["film_remaining"] = int(primary_remaining)
        payload.update(self._offline_telemetry_snapshot())
        return payload

    def _send_heartbeat_request(
        self, payload: Optional[dict[str, Any]] = None
    ) -> tuple[bool, str]:
        if requests is None:
            return False, "requests module not installed"
        url = self._heartbeat_url()
        headers = self._build_kiosk_api_auth_headers()
        body = payload if isinstance(payload, dict) else self._build_heartbeat_payload()
        timeout = self._sales_request_timeout()

        try:
            response = requests.post(url, json=body, headers=headers, timeout=timeout)
            body_text = str(response.text or "").replace("\n", " ").replace("\r", " ").strip()
            lock_hit, parsed_payload = self._consume_server_lock_response(response, trigger="heartbeat_api")
            if lock_hit:
                return False, "DEVICE_LOCKED"
            if int(response.status_code) >= 400:
                return False, f"HTTP {response.status_code} {body_text[:220]}"
            data = parsed_payload if isinstance(parsed_payload, dict) else (response.json() if response.content else {})
            if not isinstance(data, dict):
                data = {}
            heartbeat_id = data.get("heartbeat_id")
            return True, f"id={heartbeat_id}"
        except Exception as exc:
            return False, str(exc)

    def _probe_server_lock_state(self) -> tuple[bool, str]:
        if requests is None:
            return False, "requests module not installed"
        url = self._kiosk_config_url()
        headers = self._build_kiosk_api_auth_headers()
        headers = dict(headers)
        headers.pop("Content-Type", None)
        timeout = min(5.0, self._sales_request_timeout())
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            body_text = str(response.text or "").replace("\n", " ").replace("\r", " ").strip()
            lock_hit, parsed_payload = self._consume_server_lock_response(response, trigger="config_probe")
            if lock_hit:
                return True, "locked"
            if int(response.status_code) >= 400:
                return False, f"HTTP {response.status_code} {body_text[:180]}"
            data = parsed_payload if isinstance(parsed_payload, dict) else (response.json() if response.content else {})
            if not isinstance(data, dict):
                return False, "invalid json payload"
            self._apply_server_lock_payload(data.get("device_lock"), trigger="config_probe")
            config_payload = data.get("config") if isinstance(data.get("config"), dict) else {}
            if isinstance(config_payload, dict):
                self._apply_server_gemini_api_key(config_payload, trigger="config_probe")
                mode_perms = config_payload.get("device_mode_permissions")
                if isinstance(mode_perms, dict):
                    event = {"permissions": dict(mode_perms), "trigger": "config_probe"}
                    if QThread.currentThread() == self.thread():
                        self._on_server_mode_permissions_signal(event)
                    else:
                        self.server_mode_permissions_signal.emit(event)
            return True, "ok"
        except Exception as exc:
            return False, str(exc)

    def _server_lock_probe_tick(self) -> None:
        with self._server_lock_probe_lock:
            if self._server_lock_probe_inflight:
                return
            self._server_lock_probe_inflight = True

        def _runner() -> None:
            try:
                ok, msg = self._probe_server_lock_state()
                now_ts = time.monotonic()
                text = str(msg or "").strip()
                if ok:
                    self._server_lock_probe_last_error = ""
                    self._server_lock_probe_last_error_ts = 0.0
                else:
                    should_log = (
                        text != self._server_lock_probe_last_error
                        or (now_ts - float(self._server_lock_probe_last_error_ts)) >= 30.0
                    )
                    if should_log:
                        print(f"[SERVER_LOCK] probe fail {text}")
                        self._server_lock_probe_last_error = text
                        self._server_lock_probe_last_error_ts = now_ts
            finally:
                with self._server_lock_probe_lock:
                    self._server_lock_probe_inflight = False

        threading.Thread(target=_runner, daemon=True, name="server-lock-probe").start()

    def _heartbeat_tick(self) -> None:
        self._enforce_offline_runtime_guard("heartbeat_timer")
        with self._heartbeat_lock:
            if self._heartbeat_inflight:
                return
            self._heartbeat_inflight = True

        def _runner() -> None:
            try:
                delivered, pending = self._flush_offline_queue_once()
                if delivered > 0:
                    print(f"[QUEUE] pre-heartbeat delivered={delivered} pending={pending}")
                payload = self._build_heartbeat_payload()
                ok, msg = self._send_heartbeat_request(payload=payload)
                if ok:
                    self._record_online_heartbeat()
                    print(f"[HEARTBEAT] ok {msg}")
                    self.offline_guard_signal.emit("heartbeat_ok")
                else:
                    print(f"[HEARTBEAT] fail {msg}")
                    if not str(msg).strip().upper().startswith("DEVICE_LOCKED"):
                        self._enqueue_offline_event(
                            kind="heartbeat",
                            payload=payload,
                            dedupe_key="heartbeat",
                        )
                    self.offline_guard_signal.emit("heartbeat_fail")
            finally:
                with self._heartbeat_lock:
                    self._heartbeat_inflight = False

        threading.Thread(target=_runner, daemon=True, name="heartbeat-report").start()

    def _report_sale_complete_async(self) -> None:
        session = self.get_active_session()
        if session is None:
            print("[SALES] skip: session missing")
            return
        payload = self._build_sale_complete_payload(session)
        if payload is None:
            return
        session_id = str(payload.get("session_id", "")).strip()
        if not session_id:
            return
        if self._is_sale_already_reported(session_id):
            print(f"[SALES] skip duplicate session={session_id}")
            return

        def _runner() -> None:
            print(f"[SALES] report start session={session_id}")
            ok, message = self._send_sale_complete_request(payload)
            if ok:
                self._mark_sale_reported(session_id)
                print(f"[SALES] report ok session={session_id} {message}")
            else:
                print(f"[SALES] report failed session={session_id} {message}")
                if str(message).strip().upper().startswith("DEVICE_LOCKED"):
                    print(f"[SALES] queue skipped session={session_id} reason=DEVICE_LOCKED")
                    return
                self._enqueue_offline_event(
                    kind="sale_complete",
                    payload=payload,
                    dedupe_key=f"sale:{session_id}",
                )
                self._flush_offline_queue_async(reason="sale_fail")

        threading.Thread(target=_runner, daemon=True, name=f"sale-report-{session_id}").start()

    def _write_share_json(self, session: Session, urls: dict) -> Optional[Path]:
        try:
            share_dir = ensure_share_dir(session.session_dir)
            share_json_path = share_dir / "share.json"
            frame_local = share_dir / "frame.png"
            image_local = share_dir / "print.jpg"
            video_local = share_dir / "video.gif"
            payload: dict[str, Any] = {
                "session_id": urls.get("session_id"),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "layout_id": self.current_layout_id,
                "print_slots": self.current_print_slots,
                "capture_slots": self.current_capture_slots,
                "design_index": self.current_design_index,
                "page_url": urls.get("page_url"),
                "files": {
                    "frame": {
                        "name": "frame.png",
                        "url": urls.get("frame_url"),
                    },
                    "image": {
                        "name": "print.jpg",
                        "url": urls.get("image_url"),
                    },
                    "video": None,
                },
            }
            if video_local.is_file():
                payload["files"]["video"] = {  # type: ignore[index]
                    "name": "video.gif",
                    "url": urls.get("video_url"),
                }
            _write_json_atomic(share_json_path, payload)
            print(f"[SHARE] share.json written path={share_json_path}")
            return share_json_path
        except Exception as exc:
            print(f"[SHARE] share.json write failed: {exc}")
            return None

    def _refresh_qr_for_page_url(self, session: Session, page_url: str) -> Optional[Path]:
        try:
            qr_path = generate_qr_png(page_url, session.qr_dir / "qr.png")
            session.set_share_url(page_url)
            session.save_qr(qr_path)
            print(f"[QR] page_url={page_url}")
            return qr_path
        except Exception as exc:
            print(f"[QR] generate failed: {exc}")
            return None

    def _on_print_success(self) -> None:
        ctx = dict(self._active_print_context) if isinstance(self._active_print_context, dict) else {}
        self._active_print_context = {}
        should_consume = bool(ctx.get("enabled", True)) and not bool(ctx.get("dry_run", False)) and not bool(
            ctx.get("test_mode", False)
        )
        if should_consume:
            model = str(ctx.get("model", "DS620"))
            strip_split = bool(ctx.get("strip_split", False))
            if strip_split:
                used_units = max(1, self._safe_int(ctx.get("strip_sets"), 1)) * 2
            else:
                used_units = max(1, self._safe_int(ctx.get("copies"), 1))
            self._consume_film_remaining(model, used_units)
        print("[PRINT] success")
        self._report_sale_complete_async()
        loading_screen = self.screens.get("loading")
        if isinstance(loading_screen, LoadingScreen):
            loading_screen.clear_status_message()
        preview_screen = self.screens.get("preview")
        if isinstance(preview_screen, PreviewScreen):
            preview_screen.set_confirm_locked(False)
        thank_you_screen = self.screens.get("thank_you")
        if isinstance(thank_you_screen, ThankYouScreen):
            thank_you_screen.set_qr_path(None)
        session = self.get_active_session()
        qr_enabled = bool(getattr(session, "qr_enabled", self.current_design_qr_enabled))
        if not qr_enabled:
            print("[QR] enabled=0 -> thank_you")
            self.goto_screen("thank_you")
            return
        print("[QR] enabled=1 -> qr_generating")
        self.goto_screen("qr_generating")

    def open_qr_code_screen(self, qr_path: Optional[Path], page_url: Optional[str]) -> None:
        qr_screen = self.screens.get("qr_code")
        if isinstance(qr_screen, AppQrCodeScreen):
            qr_screen.set_qr_context(qr_path, page_url)
        self.goto_screen("qr_code")

    def handle_qr_generating_done(self, qr_path: Optional[Path] = None) -> None:
        current = self.stack.currentWidget()
        if getattr(current, "screen_name", None) != "qr_generating":
            return
        thank_you_screen = self.screens.get("thank_you")
        if isinstance(thank_you_screen, ThankYouScreen):
            thank_you_screen.set_qr_path(qr_path)
        self.goto_screen("thank_you")

    def go_start_from_thankyou(self, reason: str = "tap") -> None:
        if reason == "tap":
            print("[THANKYOU] tap -> start")
        elif reason == "auto":
            auto_ms = getattr(AppThankYouScreen, "AUTO_BACK_MS", 0)
            auto_sec = max(1, int(auto_ms // 1000)) if isinstance(auto_ms, int) else 20
            print(f"[NAV] thank_you -> start ({auto_sec}s)")
        self.goto_screen("start")

    def on_upload_success(self, share_url: str) -> None:
        print(f"[UPLOAD] ok url={share_url}")
        session = self.get_active_session()
        if session is None:
            self.handle_qr_generating_done(None)
            return
        urls = self._build_share_urls(session)
        page_url = str(urls.get("page_url"))
        self._write_share_json(session, urls)
        qr_path = self._refresh_qr_for_page_url(session, page_url)
        if qr_path is None:
            self.handle_qr_generating_done(None)
            return
        self.open_qr_code_screen(qr_path, page_url)

    def on_upload_fail(self, error_message: str) -> None:
        print(f"[UPLOAD] fail: {error_message}")
        self.handle_qr_generating_done(None)

    def _on_print_failure(self, error_message: str) -> None:
        self._active_print_context = {}
        print(f"[PRINT] failure: {error_message}")
        loading_screen = self.screens.get("loading")
        if isinstance(loading_screen, LoadingScreen):
            loading_screen.clear_status_message()
        preview_screen = self.screens.get("preview")
        if isinstance(preview_screen, PreviewScreen):
            preview_screen.set_confirm_locked(False)
        self.goto_screen("error")

    def _on_print_thread_finished(self) -> None:
        self.print_thread = None
        self.print_worker = None

    def _on_thank_you_timeout(self) -> None:
        current = self.stack.currentWidget()
        if getattr(current, "screen_name", None) == "thank_you":
            self.goto_screen("start")

    def reload_hotspots(self) -> None:
        try:
            loaded = load_hotspots(self.hotspots_path)
        except Exception as exc:
            print(f"[F5] Failed to reload hotspots: {exc}")
            return

        self.hotspot_map = loaded
        self._apply_admin_hotspot_overrides()
        self._apply_payment_hotspot_overrides()
        self._sync_pricing_layout_defaults(persist=True)
        for name, screen in self.screens.items():
            screen.set_hotspots(self.hotspot_map.get(name, []))
            screen.set_overlay_visible(self.show_hotspot_overlay)
        self._refresh_frame_select_mode_buttons()
        self._refresh_frame_select_price_labels()
        print("[F5] hotspots.json reloaded")

    def toggle_hotspot_overlay(self) -> None:
        self.show_hotspot_overlay = not self.show_hotspot_overlay
        for screen in self.screens.values():
            screen.set_overlay_visible(self.show_hotspot_overlay)
        state = "ON" if self.show_hotspot_overlay else "OFF"
        print(f"[F1] Hotspot overlay: {state}")

    def toggle_click_logging(self) -> None:
        self.log_click_coords = not self.log_click_coords
        state = "ON" if self.log_click_coords else "OFF"
        print(f"[F2] Click coordinate logging: {state}")

    def toggle_record_mode(self) -> None:
        self.record_mode = not self.record_mode
        self.record_start = None
        state = "ON" if self.record_mode else "OFF"
        print(f"[R] Rectangle record mode: {state}")

    def apply_celebrity_template_selection(self, template_dir: Path, template_name: str) -> None:
        if not isinstance(template_dir, Path):
            return

        celeb_cfg = self.get_celebrity_settings()
        layout_id = str(
            celeb_cfg.get("layout_id", DEFAULT_CELEBRITY_SETTINGS["layout_id"])
        ).strip() or str(DEFAULT_CELEBRITY_SETTINGS["layout_id"])

        self.compose_mode = "celebrity"
        self.celebrity_template_dir = str(template_dir)
        self.celebrity_template_name = str(template_name or template_dir.name)
        self.current_layout_id = layout_id
        self.layout_id = layout_id
        self.current_design_index = None
        self.current_design_path = None
        self.design_index = 1
        self.design_path = None

        base_price = self._price_per_set_for_layout(layout_id)
        print(
            f"[CELEB] selected template_dir={template_dir} layout={layout_id} price={base_price}"
        )
        self.goto_screen("how_many_prints")

    def apply_ai_style_selection(self, style_id: str) -> None:
        style_key = _resolve_preferred_ai_style_id(style_id)
        style_info = AI_STYLE_PRESETS.get(style_key) or {}
        label_ko = str(style_info.get("label_ko", style_key))
        if not self._is_ai_mode_runtime_ready(stage="style_select", probe_once=True):
            self._block_ai_mode_missing_key(
                stage="style_select",
                notice="AI 서버 키가 없어 사용할 수 없습니다",
            )
            self.goto_screen("frame_select")
            return

        self.compose_mode = "ai"
        self.celebrity_template_dir = None
        self.celebrity_template_name = None
        self.ai_style_id = style_key
        self.current_layout_id = AI_LAYOUT_ID
        self.layout_id = AI_LAYOUT_ID
        self.current_design_index = None
        self.current_design_path = None
        self.design_index = 1
        self.design_path = None

        base_price = self._price_per_set_for_layout(AI_LAYOUT_ID)
        print(
            f"[AI_MODE] selected style={style_key} label={label_ko} "
            f"layout={AI_LAYOUT_ID} capture={AI_CAPTURE_SLOTS} price={base_price}"
        )
        self.goto_screen("how_many_prints")

    def is_ai_mode_active(self) -> bool:
        mode = str(self.compose_mode or "").strip().lower()
        return mode == "ai" and str(self.current_layout_id or "").strip() == AI_LAYOUT_ID

    def select_layout(self, layout_id: str) -> None:
        self.current_layout_id = layout_id
        self.compose_mode = "normal"
        self.celebrity_template_dir = None
        self.celebrity_template_name = None
        self.ai_style_id = None
        self.current_design_index = None
        self.current_design_path = None
        self.design_key_buffer = ""
        self.design_key_timer.stop()
        print(f"[LAYOUT] selected={layout_id}")
        self.goto_screen("how_many_prints")

    def flush_design_key_buffer(self) -> None:
        self.design_key_buffer = ""

    def _coupon_handle_click(self, x: int, y: int) -> bool:
        coupon_screen = self.screens.get("coupon_input")
        if not isinstance(coupon_screen, CouponInputScreen):
            return False
        handled = coupon_screen.handle_design_click(x, y)
        if handled:
            return True
        return False

    def handle_screen_click(self, screen: ImageScreen, x: int, y: int) -> None:
        if self.log_click_coords:
            print(f"[CLICK] screen={screen.screen_name} x={x} y={y}")

        if self.record_mode:
            if self.record_start is None:
                self.record_start = (x, y)
                print(f"[R] start=({x}, {y})")
                return

            x1, y1 = self.record_start
            left = min(x1, x)
            top = min(y1, y)
            width = abs(x - x1)
            height = abs(y - y1)
            print(f"[R] rect=[{left}, {top}, {width}, {height}]")
            self.record_start = None
            return

        if not self._server_lock_active:
            self._server_lock_probe_tick()

        if self._is_runtime_locked() and screen.screen_name not in {"offline_locked", "admin"}:
            self.goto_screen("offline_locked")
            return

        if screen.screen_name == "start" and 0 <= x < 100 and 0 <= y < 100:
            self._start_admin_tap_count += 1
            self._start_admin_tap_timer.start(2000)
            print(f"[ADMIN] start taps={self._start_admin_tap_count}/5")
            if self._start_admin_tap_count >= 5:
                self._reset_start_admin_taps()
                self.open_admin()
            return

        if screen.screen_name == "pay_cash":
            if self._rect_contains(x, y, PayCashScreen.BACK_RECT):
                back_target = "payment_method"
                if self._single_enabled_payment_method() == "cash":
                    back_target = "how_many_prints"
                print(f"[PAYMENT_CASH] back -> {back_target}")
                self._stop_bill_acceptor_for_payment()
                self.goto_screen(back_target)
                return

        if screen.screen_name == "coupon_remaining_method":
            if self._rect_contains(x, y, CouponRemainingMethodScreen.CASH_RECT):
                print("[PAYMENT] remaining_select cash")
                self.goto_screen("pay_cash_remaining")
                return
            if self._rect_contains(x, y, CouponRemainingMethodScreen.CARD_RECT):
                print("[PAYMENT] remaining_select card")
                remaining_screen = self.screens.get("coupon_remaining_method")
                if isinstance(remaining_screen, CouponRemainingMethodScreen):
                    remaining_screen.show_notice("카드결제는 추후 지원됩니다", duration_ms=1000)
                return
            if self._rect_contains(x, y, CouponRemainingMethodScreen.BACK_RECT):
                print("[PAYMENT] remaining_select back -> payment_method")
                self.goto_screen("payment_method")
                return

        if screen.screen_name == "pay_cash_remaining":
            if self._rect_contains(x, y, PayCashRemainingScreen.BACK_RECT):
                print("[PAYMENT_CASH] back -> coupon_remaining_method")
                self._stop_bill_acceptor_for_payment()
                self.goto_screen("coupon_remaining_method")
                return

        action: Optional[str] = None
        if screen.screen_name == "coupon_input":
            if self._coupon_handle_click(x, y):
                return
            action = hit_test(screen.hotspots, x, y)
        elif screen.screen_name == "payment_method":
            payment_screen = self.screens.get("payment_method")
            picked_method = None
            payment_mode = "unknown"
            if isinstance(payment_screen, AppPaymentMethodScreen):
                picked_method = payment_screen.pick_method_at(x, y)
                payment_mode = payment_screen.get_payment_mode()
            print(f"[PAYMENT_CLICK] x={x} y={y} picked={picked_method} mode={payment_mode}")
            if picked_method is not None:
                action = f"payment:{picked_method}"
            else:
                action = hit_test(screen.hotspots, x, y)
        else:
            action = hit_test(screen.hotspots, x, y)
        if action is None and screen.screen_name == "camera":
            print(f"[HIT_TEST] none x={x} y={y}")
            force_shutter = self.is_debug_fullscreen_shutter()
            camera_screen = self.screens.get("camera")
            if not force_shutter and isinstance(camera_screen, CameraScreen):
                if camera_screen._backend_active in {"dummy", "fallback_dummy"}:
                    force_shutter = True
                    print("[CAMERA] dummy backend click -> force shutter")
            if force_shutter and isinstance(camera_screen, CameraScreen):
                print("[CAMERA] shutter requested (force)")
                camera_screen.request_shutter()
                return
        if action:
            self.ui_sound.play("click")
            self._suppress_nav_sound_until = time.monotonic() + 0.35
            print(f"[ACTION] screen={screen.screen_name} action={action}")
            if screen.screen_name == "camera" and action == "camera:shutter":
                print("[HOTSPOT] screen=camera action=camera:shutter")
            else:
                print(f"[HOTSPOT] screen={screen.screen_name} action={action}")
            if action.startswith("camera:"):
                camera_screen = self.screens.get("camera")
                if not isinstance(camera_screen, CameraScreen):
                    return
                command = action.split(":", 1)[1].strip()
                if command == "shutter":
                    print("[CAMERA] shutter requested (hotspot)")
                    camera_screen.request_shutter()
                elif command == "next":
                    self.enter_select_photo_from_camera()
                else:
                    print(f"[CAMERA] unknown action: {command}")
                return
            if action.startswith("how_many:"):
                command = action.split(":", 1)[1].strip()
                how_many_screen = self.screens.get("how_many_prints")
                if not isinstance(how_many_screen, AppHowManyPrintsScreen):
                    return
                if command == "plus":
                    old_value, new_value = how_many_screen.adjust_print_count(+1)
                    self.current_print_count = int(new_value)
                    self.print_count = int(new_value)
                    print(f"[PRINT_COUNT] plus old={old_value} new={new_value}")
                elif command == "minus":
                    old_value, new_value = how_many_screen.adjust_print_count(-1)
                    self.current_print_count = int(new_value)
                    self.print_count = int(new_value)
                    print(f"[PRINT_COUNT] minus old={old_value} new={new_value}")
                else:
                    print(f"[PRINT_COUNT] unknown action: {command}")
                return
            if action.startswith("payment:"):
                command = action.split(":", 1)[1].strip()
                payment_screen = self.screens.get("payment_method")
                if not isinstance(payment_screen, AppPaymentMethodScreen):
                    return
                enabled = self.get_payment_methods()
                if command == "cash":
                    if not enabled.get("cash", False):
                        print("[PAYMENT] blocked disabled method=cash")
                        payment_screen.show_notice("해당 결제수단이 비활성화되었습니다", duration_ms=1000)
                        return
                    payment_screen.set_payment_method("cash")
                    self.current_payment_method = "cash"
                    self.payment_method = self.current_payment_method
                    print("[PAYMENT] select=cash")
                elif command == "card":
                    if not enabled.get("card", False):
                        print("[PAYMENT] blocked disabled method=card")
                        payment_screen.show_notice("해당 결제수단이 비활성화되었습니다", duration_ms=1000)
                        return
                    payment_screen.set_payment_method("card")
                    self.current_payment_method = "card"
                    self.payment_method = self.current_payment_method
                    print("[PAYMENT] select=card")
                elif command == "coupon":
                    if not enabled.get("coupon", False):
                        print("[PAYMENT] blocked disabled method=coupon")
                        payment_screen.show_notice("해당 결제수단이 비활성화되었습니다", duration_ms=1000)
                        return
                    coupon_settings = self.get_coupon_settings()
                    if not bool(coupon_settings.get("enabled", True)):
                        print("[PAYMENT] coupon disabled")
                        payment_screen.show_notice("쿠폰 사용이 비활성화되었습니다", duration_ms=1000)
                        return
                    payment_screen.set_payment_method("coupon")
                    self.current_payment_method = "coupon"
                    self.payment_method = self.current_payment_method
                    print("[PAYMENT] select=coupon")
                elif command == "next":
                    method = payment_screen.payment_method or self.current_payment_method
                    if method == "cash":
                        if not enabled.get("cash", False):
                            print("[PAYMENT] blocked disabled method=cash")
                            payment_screen.show_notice("해당 결제수단이 비활성화되었습니다", duration_ms=1000)
                            return
                        self.current_payment_method = "cash"
                        self.payment_method = self.current_payment_method
                        self.current_coupon_value = 0
                        self.current_coupon_code = None
                        self.pending_coupon_code = None
                        if self.current_required_amount <= 0:
                            self._refresh_required_amount()
                        print("[PAYMENT] next ok -> pay_cash")
                        self.goto_screen("pay_cash")
                    elif method == "coupon":
                        if not enabled.get("coupon", False):
                            print("[PAYMENT] blocked disabled method=coupon")
                            payment_screen.show_notice("해당 결제수단이 비활성화되었습니다", duration_ms=1000)
                            return
                        coupon_settings = self.get_coupon_settings()
                        if not bool(coupon_settings.get("enabled", True)):
                            print("[PAYMENT] next blocked: coupon disabled")
                            payment_screen.show_notice("쿠폰 사용이 비활성화되었습니다", duration_ms=1000)
                            return
                        self.current_payment_method = "coupon"
                        self.payment_method = self.current_payment_method
                        print("[PAYMENT] next ok -> coupon_input")
                        self.goto_screen("coupon_input")
                    elif method == "card":
                        if not enabled.get("card", False):
                            print("[PAYMENT] blocked disabled method=card")
                            payment_screen.show_notice("해당 결제수단이 비활성화되었습니다", duration_ms=1000)
                            return
                        if self.is_test_mode():
                            self.current_payment_method = "card"
                            self.payment_method = self.current_payment_method
                            print("[PAYMENT] next test bypass card -> payment_complete_success")
                            self.goto_screen("payment_complete_success")
                            return
                        print("[PAYMENT] next blocked: card not supported")
                        payment_screen.show_notice("카드결제는 추후 지원됩니다", duration_ms=1000)
                    else:
                        print("[PAYMENT] next blocked: payment method not selected")
                        payment_screen.show_notice("결제 수단을 선택해주세요", duration_ms=1000)
                else:
                    print(f"[PAYMENT] unknown action: {command}")
                return
            if action.startswith("payment_complete:"):
                command = action.split(":", 1)[1].strip()
                if command == "next":
                    print("[PAYMENT_COMPLETE] tap -> camera")
                    self.handle_payment_complete_success()
                else:
                    print(f"[PAYMENT_COMPLETE] unknown action: {command}")
                return
            if action.startswith("select_photo:"):
                command = action.split(":", 1)[1].strip()
                if command == "back":
                    print("[SELECT_PHOTO] back -> camera")
                    self.goto_screen("camera")
                elif command == "next":
                    self._continue_from_select_photo()
                else:
                    print(f"[SELECT_PHOTO] unknown action: {command}")
                return
            if action.startswith("select_design:"):
                command = action.split(":", 1)[1].strip()
                select_design_screen = self.screens.get("select_design")
                if not isinstance(select_design_screen, SelectDesignScreen):
                    print("[SELECT_DESIGN] screen missing")
                    return
                if command == "back":
                    self.goto_screen("select_photo")
                elif command in {"next", "confirm"}:
                    self._continue_from_select_design()
                elif command == "prev_frame":
                    select_design_screen._advance_frame(-1)
                    self._sync_design_state_from_screen(select_design_screen)
                elif command == "next_frame":
                    select_design_screen._advance_frame(1)
                    self._sync_design_state_from_screen(select_design_screen)
                elif command == "color":
                    select_design_screen.set_gray(False)
                    self._sync_design_state_from_screen(select_design_screen)
                elif command == "gray":
                    select_design_screen.set_gray(True)
                    self._sync_design_state_from_screen(select_design_screen)
                elif command == "flip_toggle":
                    select_design_screen.toggle_flip()
                    self._sync_design_state_from_screen(select_design_screen)
                elif command == "qr_toggle":
                    select_design_screen.toggle_qr()
                    self._sync_design_state_from_screen(select_design_screen)
                else:
                    print(f"[SELECT_DESIGN] unknown action: {command}")
                return
            if action.startswith("preview:"):
                command = action.split(":", 1)[1].strip()
                if command == "back":
                    self.goto_screen("camera")
                elif command == "confirm":
                    self._start_print_from_preview()
                else:
                    print(f"[PREVIEW] unknown action: {command}")
                return
            if action.startswith("thank_you:"):
                command = action.split(":", 1)[1].strip()
                if command == "back":
                    self.go_start_from_thankyou(reason="tap")
                else:
                    print(f"[THANKYOU] unknown action: {command}")
                return
            if action.startswith("goto:"):
                target = action.split(":", 1)[1].strip()
                if target == "admin":
                    self.open_admin()
                    return
                if target == "camera":
                    if not self._prepare_camera_entry():
                        return
                if screen.screen_name == "how_many_prints" and target == "payment_method":
                    if self.is_ai_mode_active() and not self._is_ai_mode_runtime_ready(
                        stage="before_payment",
                        probe_once=True,
                    ):
                        self._block_ai_mode_missing_key(
                            stage="before_payment",
                            notice="AI 서버 키가 없어 결제를 진행할 수 없습니다",
                        )
                        self.goto_screen("frame_select")
                        return
                    self._save_selected_print_count()
                    single_method = self._single_enabled_payment_method()
                    if single_method:
                        print(
                            f"[PAYMENT] single enabled method={single_method} "
                            "-> direct entry from how_many_prints"
                        )
                        if self._enter_single_payment_flow(single_method):
                            return
                if target == "select_photo":
                    self._prepare_select_photo_screen()
                if target == "preview":
                    if not self._set_preview_from_print_job():
                        return
                self.goto_screen(target)
                return
            if action.startswith("select_layout:"):
                self.select_layout(action.split(":", 1)[1].strip())

    def keyPressEvent(self, event: QKeyEvent):  # noqa: N802
        key = event.key()
        if key == KEY_F12:
            self.open_admin()
            return
        current = self.stack.currentWidget()
        if self._is_runtime_locked():
            current_name = getattr(current, "screen_name", None)
            if current_name == "offline_locked" and key in (KEY_ENTER, KEY_RETURN, KEY_SPACE):
                self.retry_offline_unlock()
                return
            if current_name not in {"offline_locked", "admin"}:
                self.goto_screen("offline_locked")
                return
        if getattr(current, "screen_name", None) == "camera":
            camera_screen = self.screens.get("camera")
            if isinstance(camera_screen, CameraScreen):
                if key == KEY_SPACE:
                    print("[CAMERA] shutter requested (space)")
                    camera_screen.request_shutter()
                    return
                if key == KEY_BACKSPACE:
                    camera_screen.undo_last_shot()
                    return
                if key in (KEY_ENTER, KEY_RETURN):
                    self.enter_select_photo_from_camera()
                    return
        if getattr(current, "screen_name", None) == "coupon_input":
            coupon_screen = self.screens.get("coupon_input")
            if isinstance(coupon_screen, CouponInputScreen):
                typed = event.text()
                if typed and typed.isdigit() and len(typed) == 1:
                    coupon_screen._on_digit(typed)
                    return
                if key == KEY_BACKSPACE:
                    coupon_screen._on_backspace()
                    return
                if key in (KEY_ENTER, KEY_RETURN):
                    coupon_screen.submit_coupon()
                    return
                if key == KEY_ESCAPE:
                    coupon_screen._go_back()
                    return
        if getattr(current, "screen_name", None) == "select_photo":
            if key == KEY_ESCAPE:
                self.goto_screen("camera")
                return
            if key in (KEY_ENTER, KEY_RETURN):
                self._continue_from_select_photo()
                return
        if getattr(current, "screen_name", None) == "select_design":
            if key == KEY_ESCAPE:
                self.goto_screen("select_photo")
                return
            if key in (KEY_ENTER, KEY_RETURN):
                self._continue_from_select_design()
                return
        if getattr(current, "screen_name", None) == "admin":
            if key == KEY_ESCAPE:
                self.close_admin()
                return
        if getattr(current, "screen_name", None) == "preview":
            if key == KEY_ESCAPE:
                self.goto_screen("camera")
                return
            if key in (KEY_ENTER, KEY_RETURN):
                self._start_print_from_preview()
                return
        if getattr(current, "screen_name", None) == "error":
            if key in (KEY_ENTER, KEY_RETURN):
                self.goto_screen("start")
                return
        if getattr(current, "screen_name", None) == "qr_generating":
            if key in (KEY_ENTER, KEY_RETURN):
                print("[QR] generating: manual advance ignored (minimum hold)")
                return
        if getattr(current, "screen_name", None) == "qr_code":
            if key in (KEY_ENTER, KEY_RETURN):
                self.goto_screen("thank_you")
                return
        if getattr(current, "screen_name", None) == "payment_complete_success":
            if key == KEY_F9:
                self.goto_screen("payment_complete_failed")
                return
        if key == KEY_F1:
            self.toggle_hotspot_overlay()
            return
        if key == KEY_F2:
            self.toggle_click_logging()
            return
        if key == KEY_F5:
            self.reload_hotspots()
            return
        if key == KEY_R:
            self.toggle_record_mode()
            return
        if key in LAYOUT_KEY_MAP:
            if getattr(current, "screen_name", None) == "frame_select":
                layout_id = LAYOUT_KEY_MAP[key]
                print(f"[KEY] select_layout:{layout_id}")
                self.select_layout(layout_id)
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):  # noqa: N802
        self._heartbeat_timer.stop()
        self._server_lock_probe_timer.stop()
        self._ota_check_timer.stop()
        self._stop_payment_complete_transition_watchdog()
        self._stop_select_photo_preload_worker(wait=True)
        self.stop_bill_acceptor_test(wait_ms=3000)
        camera_screen = self.screens.get("camera")
        if isinstance(camera_screen, CameraScreen):
            camera_screen.cancel_countdown()
            camera_screen.reset_gif_capture_state()
            camera_screen._auto_next_pending = False
            camera_screen._capture_pending_after_liveview_stop = False
            camera_screen._stop_capture_worker(wait=True)
            camera_screen._stop_liveview_worker(wait=True)
        terminate_edsdk_once()
        super().closeEvent(event)


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(terminate_edsdk_once)
    try:
        window = KioskMainWindow()
    except RuntimeError as exc:
        print(f"[BOOT] startup canceled: {exc}")
        return 1
    force_windowed = str(os.environ.get("KIOSK_WINDOWED", "0")).strip().lower() in {"1", "true", "yes", "on"}
    if force_windowed:
        window.show()
        print("[BOOT] windowed mode enabled by KIOSK_WINDOWED")
    else:
        try:
            window.showFullScreen()
            print("[BOOT] fullscreen mode enabled")
        except Exception as exc:
            print(f"[BOOT] fullscreen failed: {exc} -> fallback maximized")
            try:
                window.showMaximized()
            except Exception:
                window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
