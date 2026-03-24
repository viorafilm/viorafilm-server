from __future__ import annotations

import unittest

from app.main import _normalize_printer_form_name_for_job


class PrinterFormResolutionTests(unittest.TestCase):
    def test_4x6_jobs_reject_envelope_forms(self) -> None:
        self.assertEqual(
            _normalize_printer_form_name_for_job("4x6", "6 3/4 Envelope"),
            "4x6",
        )

    def test_4x6_jobs_preserve_common_photo_aliases(self) -> None:
        self.assertEqual(
            _normalize_printer_form_name_for_job("4x6", "North America 4x6"),
            "North America 4x6",
        )
        self.assertEqual(
            _normalize_printer_form_name_for_job("4x6", "10×15in"),
            "10×15in",
        )

    def test_2x6_jobs_preserve_common_aliases(self) -> None:
        self.assertEqual(
            _normalize_printer_form_name_for_job("2x6", "2×6"),
            "2×6",
        )


if __name__ == "__main__":
    unittest.main()
