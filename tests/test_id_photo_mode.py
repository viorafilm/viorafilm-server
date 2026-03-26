from __future__ import annotations

import unittest

import app.main as kiosk_main


class _ModeClickStub:
    def __init__(self, enabled: bool) -> None:
        self.mode_settings = {"id_photo_enabled": bool(enabled)}
        self._suppress_nav_sound_until = 0.0
        self.notice_messages: list[str] = []
        self.goto_targets: list[str] = []

        class _Sound:
            def play(self, _name: str) -> None:
                return None

        self.ui_sound = _Sound()

    def _show_runtime_notice(self, message: str, duration_ms: int = 0) -> None:
        _ = duration_ms
        self.notice_messages.append(str(message))

    def goto_screen(self, target: str) -> None:
        self.goto_targets.append(str(target))


class IdPhotoModeTests(unittest.TestCase):
    def test_normalize_modes_settings_includes_id_photo(self) -> None:
        normalized = kiosk_main.KioskMainWindow._normalize_modes_settings({"id_photo_enabled": True})
        self.assertTrue(normalized["id_photo_enabled"])

    def test_id_photo_mode_click_enters_placeholder_when_enabled(self) -> None:
        stub = _ModeClickStub(enabled=True)
        kiosk_main.KioskMainWindow._on_frame_select_mode_id_photo_clicked(stub)
        self.assertEqual(stub.goto_targets, ["id_photo_mode"])
        self.assertEqual(stub.notice_messages, [])

    def test_id_photo_mode_click_shows_notice_when_disabled(self) -> None:
        stub = _ModeClickStub(enabled=False)
        kiosk_main.KioskMainWindow._on_frame_select_mode_id_photo_clicked(stub)
        self.assertEqual(stub.goto_targets, [])
        self.assertTrue(stub.notice_messages)


if __name__ == "__main__":
    unittest.main()
