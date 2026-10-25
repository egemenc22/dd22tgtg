# EGONIA SIGNAL ENGINE v2.2 — Windows

Builds on v2.1 without adding USDT payment processing.

## Changes
- Dashboard brand: EGONIA; text notifications use EGONIA.
- /api/operations: last scanner cycle, age, cumulative signal count, markets observed, active VIPs, statuses and last 20 deliveries needing review.
- /health: scanner freshness (boolean) and last cycle age. It is not an exchange connectivity guarantee.
- Original X/Telegram delivery ambiguity handling is preserved. Needs-review posts MUST be reconciled against X/Telegram before any manual requeue.
- X profile reference: https://x.com/EgoniaSignals (not an API credential).

## Start
1. Extract zip to its own folder, then START.bat. Python + matplotlib required.
2. Panel: http://127.0.0.1:8787 ; JSON: /api/operations and /health.
3. Keep dry_run=true for first validation. Set publishing options and environment variables only when ready.
4. Run TESTS.bat for local automated tests.

## Limits
No live exchange or social network end-to-end tests were run here. No automatic retry for ambiguous social API timeouts. No USDT payments.

NOTE: use a persistent folder between restarts so the SQLite history remains intact.
