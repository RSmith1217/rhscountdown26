import unittest
from datetime import datetime, timezone
from scripts.absence_schedule import CALENDAR_PATH, school_day, should_refresh


class AbsenceScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calendar = CALENDAR_PATH.read_text()

    def test_student_days_include_exams_and_minimum_days(self):
        for date in ['2026-10-13', '2026-09-01', '2027-01-20', '2027-06-22']:
            with self.subTest(date=date):
                self.assertTrue(school_day(date, self.calendar))

    def test_closures_pd_and_unlisted_days_skip(self):
        for date in ['2026-10-12', '2026-11-03', '2026-12-25', '2026-10-17', '2027-07-01']:
            with self.subTest(date=date):
                self.assertFalse(school_day(date, self.calendar))

    def test_eastern_date_used_not_utc_date(self):
        # Still the PD-only October 12 in New York.
        now = datetime(2026, 10, 13, 1, tzinfo=timezone.utc)
        self.assertFalse(should_refresh('schedule', now, self.calendar))

    def test_manual_refresh_bypasses_calendar(self):
        now = datetime(2026, 10, 12, 12, tzinfo=timezone.utc)
        self.assertTrue(should_refresh('workflow_dispatch', now, self.calendar))

    def test_delayed_run_still_updates_on_school_day(self):
        now = datetime(2026, 10, 13, 18, tzinfo=timezone.utc)
        self.assertTrue(should_refresh('schedule', now, self.calendar))

    def test_broken_calendar_fails_instead_of_scraping(self):
        with self.assertRaises(ValueError):
            school_day('2026-10-13', 'invalid calendar')
