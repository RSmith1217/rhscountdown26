#!/usr/bin/env python3
"""Fetch RHS App absences and publish them as absences.json."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


SOURCE_URL = "https://app.ridgewood.k12.nj.us/"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "absences.json"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def split_absence_heading(heading: str) -> dict[str, str]:
    cleaned = re.sub(r"^UPDATE\s+", "", clean_text(heading), flags=re.I)
    separator = re.search(r"\s+-\s+|-\s+(?=\d|AM\b|PM\b|All\b|REPORT\b|Period\b)", cleaned, flags=re.I)

    if not separator:
        return {"name": cleaned, "summary": ""}

    return {
        "name": cleaned[: separator.start()].strip(),
        "summary": cleaned[separator.end() :].strip(),
    }


def normalize_date_label(value: str) -> str:
    date_text = clean_text(value)

    for date_format in ("%b %d, %Y", "%B %d, %Y"):
        try:
            date = datetime.strptime(date_text, date_format)
            return f"{date.strftime('%B')} {date.day}, {date.year}"
        except ValueError:
            continue

    return date_text


class RHSAbsenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[dict[str, object]] = []
        self.today_bars: list[str] = []
        self.absences: list[dict[str, object]] = []
        self.no_absences_today = False

        self._collect_today = False
        self._today_parts: list[str] = []
        self._in_absences = False
        self._current_absence: dict[str, object] | None = None
        self._heading_parts: list[str] = []
        self._collect_heading = False
        self._current_row: list[str] | None = None
        self._current_cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        classes = set(attr_map.get("class", "").split())
        frame = {
            "tag": tag,
            "today": False,
            "absences": False,
            "item": False,
            "strong": False,
            "tr": False,
            "td": False,
            "h1": False,
        }

        if tag == "div" and "flexsubbar" in classes:
            self._collect_today = True
            self._today_parts = []
            frame["today"] = True

        if tag == "div" and attr_map.get("id") == "accordionFlushAbsences":
            self._in_absences = True
            frame["absences"] = True

        if self._in_absences and tag == "div" and "accordion-item" in classes:
            self._current_absence = {"name": "", "summary": "", "details": []}
            self._heading_parts = []
            frame["item"] = True

        if self._current_absence is not None and tag == "strong":
            self._collect_heading = True
            frame["strong"] = True

        if self._current_absence is not None and tag == "tr":
            self._current_row = []
            frame["tr"] = True

        if self._current_row is not None and tag == "td":
            self._current_cell_parts = []
            frame["td"] = True

        if tag == "h1":
            frame["h1"] = True

        self.stack.append(frame)

    def handle_data(self, data: str) -> None:
        if self._collect_today:
            self._today_parts.append(data)

        if self._collect_heading:
            self._heading_parts.append(data)

        if self._current_cell_parts is not None:
            self._current_cell_parts.append(data)

        if self.stack and self.stack[-1].get("h1") and "No Absences Today" in data:
            self.no_absences_today = True

    def handle_endtag(self, tag: str) -> None:
        frame = self._pop_frame(tag)

        if not frame:
            return

        if frame.get("today"):
            text = clean_text(" ".join(self._today_parts))
            if text:
                self.today_bars.append(text)
            self._collect_today = False
            self._today_parts = []

        if frame.get("td") and self._current_row is not None:
            self._current_row.append(clean_text(" ".join(self._current_cell_parts or [])))
            self._current_cell_parts = None

        if frame.get("tr") and self._current_row is not None and self._current_absence is not None:
            if len(self._current_row) >= 2:
                label = self._current_row[0]
                value = self._current_row[1]
                if label or value:
                    self._current_absence["details"].append({"label": label, "value": value})
            self._current_row = None

        if frame.get("strong") and self._current_absence is not None:
            heading = split_absence_heading(" ".join(self._heading_parts))
            self._current_absence.update(heading)
            self._collect_heading = False

        if frame.get("item") and self._current_absence is not None:
            if self._current_absence.get("name"):
                self.absences.append(self._current_absence)
            self._current_absence = None
            self._heading_parts = []

        if frame.get("absences"):
            self._in_absences = False

    def _pop_frame(self, tag: str) -> dict[str, object] | None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                return self.stack.pop(index)
        return None

    @property
    def source_date(self) -> str:
        today_bar = next((text for text in self.today_bars if "Today -" in text), "")
        if not today_bar:
            return ""
        return normalize_date_label(re.sub(r"^.*Today -\s*", "", today_bar))


def fetch_rhs_app() -> str:
    request = Request(
        SOURCE_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; RHSCountdownAbsenceUpdater/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )

    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def build_payload(html: str) -> dict[str, object]:
    parser = RHSAbsenceParser()
    parser.feed(html)

    return {
        "source": SOURCE_URL,
        "updatedFor": parser.source_date,
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "hasNoAbsences": parser.no_absences_today,
        "absences": parser.absences,
    }


def main() -> int:
    try:
        html = fetch_rhs_app()
        payload = build_payload(html)
    except (OSError, URLError) as error:
        print(f"Could not fetch RHS App: {error}", file=sys.stderr)
        return 1

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with {len(payload['absences'])} absence record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
