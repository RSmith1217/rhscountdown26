# RHS Countdown Timer v3.2

Self-contained GitHub Pages widget with:
- Auto-hiding past dates
- Today-aware schedule highlight
- Rotation day counts
- Period meeting counts
- Count-today toggle
- Days until finals count
- Finals and milestones
- Random inspirational/quirky header message on each load
- Date-based fun holiday message
- Scheduled RHS absence snapshot
- Expandable AP Testing schedule details
- Collapsible bell schedule
- Collapsible upcoming schedule/calendar
- Actual calendar days until June 24

## Absence Updates

Teacher absences are written to `absences.json` by `.github/workflows/update-absences.yml`.
Scheduled attempts run every 10 minutes from 7:03 AM through 8:53 AM in America/New_York, automatically following daylight saving time. Before contacting the RHS App, the workflow reads the student-day calendar in `2026-27.html` and skips holidays, weekends, PD-only days, and dates outside the listed school year. Exam and minimum days are included. Calendar changes (including emergency closures) must be reflected in that existing calendar.

Manual runs from GitHub Actions bypass the calendar check for troubleshooting. Refresh jobs are serialized to avoid competing commits. GitHub scheduled jobs can still be delayed or dropped; this schedule is not an uptime guarantee. Skipped school days use a small workflow run but make no request to the RHS App.

## Deploy

1. Replace your repo's `index.html` with this file.
2. Commit and push.
3. Refresh your GitHub Pages site.
