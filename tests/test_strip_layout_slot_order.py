from __future__ import annotations

import unittest

from app.main import _resolve_basic_frame_slots_for_canvas


class StripLayoutSlotOrderTests(unittest.TestCase):
    def test_2641_basic_frame_slots_are_grouped_by_copy(self) -> None:
        slots = _resolve_basic_frame_slots_for_canvas(
            layout_id="2641",
            canvas_size=(1200, 1800),
            photo_count=4,
            scope="print",
        )

        self.assertEqual(len(slots), 8)
        first_copy = slots[:4]
        second_copy = slots[4:]
        self.assertTrue(all(x < 600 for x, _y, _w, _h in first_copy))
        self.assertTrue(all(x >= 600 for x, _y, _w, _h in second_copy))

    def test_6241_basic_frame_slots_are_grouped_by_copy(self) -> None:
        slots = _resolve_basic_frame_slots_for_canvas(
            layout_id="6241",
            canvas_size=(1800, 1200),
            photo_count=4,
            scope="print",
        )

        self.assertEqual(len(slots), 8)
        first_copy = slots[:4]
        second_copy = slots[4:]
        self.assertTrue(all(y < 600 for _x, y, _w, _h in first_copy))
        self.assertTrue(all(y >= 600 for _x, y, _w, _h in second_copy))


if __name__ == "__main__":
    unittest.main()
