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
The workflow runs every 15 minutes from 10:00-16:59 UTC on weekdays and can also be run manually from the GitHub Actions tab.

## Deploy

1. Replace your repo's `index.html` with this file.
2. Commit and push.
3. Refresh your GitHub Pages site.
