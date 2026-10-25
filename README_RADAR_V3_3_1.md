# Egonia Radar v3.3.1 — Panel visibility hotfix

- Dashboard `/` now displays recent radar events with Telegram delivery status, rather than only the legacy LONG/SHORT signal table.
- `/api/radar` adds coverage, total count, Telegram status and errors per event.
- `not_queued` means the event did not pass publication policy, not a delivery failure.
- No changes to detection rules, publishing thresholds, token handling, or FREE daily cap.
- Copy `CREDENTIALS.cmd` from previous installation. To retain historical Radar events also copy the SQLite database while both bots are stopped (see existing documentation).
