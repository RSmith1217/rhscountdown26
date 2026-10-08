import unittest
from scripts.update_absences import build_payload


class AbsenceDateTests(unittest.TestCase):
    def test_current_date_picker(self):
        data = build_payload('<input id="datePicker" value="2026-10-08"><h1>No Absences Today</h1>')
        self.assertEqual(data['updatedFor'], 'October 8, 2026')
        self.assertTrue(data['hasNoAbsences'])

    def test_legacy_date(self):
        data = build_payload('<div class="flexsubbar">Today - Oct 07, 2026</div><h1>No Absences Today</h1>')
        self.assertEqual(data['updatedFor'], 'October 7, 2026')

    def test_missing_date_is_rejected(self):
        with self.assertRaises(ValueError):
            build_payload('<h1>No Absences Today</h1>')

    def test_missing_list_is_rejected(self):
        with self.assertRaises(ValueError):
            build_payload('<input id="datePicker" value="2026-10-08">')

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            build_payload('<input id="datePicker" value="2026-99-08"><h1>No Absences Today</h1>')
