"""Decide whether a scheduled absence refresh falls on a student school day."""
from __future__ import annotations
import json
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CALENDAR_PATH = Path(__file__).resolve().parents[1] / '2026-27.html'


def school_day(date_key: str, calendar_html: str) -> bool:
    match = re.search(r'const calendarItems\s*=\s*(\[.*?\])\.map\(', calendar_html, re.S)
    if not match:
        raise ValueError('Countdown school calendar could not be read')
    rows = json.loads(re.sub(r',\s*\]', ']', match[1]))
    for date, label, _note in rows:
        if date == date_key:
            # Match the countdown's isStudentDay rule, including exam/minimum days.
            return bool(re.search(r'^Day [1-4]$|first day|midterm|final exams|last day', label, re.I))
    return False


def should_refresh(event: str, now: datetime, calendar_html: str) -> bool:
    if event != 'schedule':
        return True  # Manual refresh remains available on any day.
    local_date = now.astimezone(ZoneInfo('America/New_York')).date()
    return local_date.weekday() < 5 and school_day(local_date.isoformat(), calendar_html)


if __name__ == '__main__':
    refresh = should_refresh(os.environ.get('GITHUB_EVENT_NAME', 'workflow_dispatch'),
                             datetime.now(ZoneInfo('America/New_York')),
                             CALENDAR_PATH.read_text(encoding='utf-8'))
    result = 'true' if refresh else 'false'
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        output.write(f'refresh={result}\n')
    print('School-day refresh approved.' if refresh else 'Skipping: no student school day in the countdown calendar.')
