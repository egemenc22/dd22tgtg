# Egonia Signal Engine v2.4 — Bugfix

This version includes the complete v2.3 package and adds the following fixes:

- Scanner panel reports `SCANNING` while the first scan is in progress rather than incorrectly displaying `STALE / NOT STARTED`.
- Last cycle scanned-market count and per-market error count are stored in SQLite and shown in the operations dashboard/JSON.
- A periodic market-discovery refresh attempts to resume the round-robin scanner from the next market rather than restarting at the first market each time.
- VIP manually revoked memberships remain `revoked` after enforcement, rather than being overwritten as `expired`.
- v2.4 regression tests for active scanner, stale scanner and scanned/error metrics.

## Startup

Run `START.bat`, open `http://127.0.0.1:8787`. Keep the console open. Run `TESTS.bat` for local tests.

**Existing SQLite data:** Copy `signal_service.sqlite` from your old folder to this version's folder with the bot stopped if you want historical signals, membership records and delivery states retained. Also copy your real `config.json` and any local `.env`/credentials setup if applicable; never share API secrets.

**Limitations:** Local tests use mocked/synthetic API responses. No live X/Telegram posting, no real brokerage order execution, no independently validated profitability. Historical target-touch research results are not interchangeable with realized trade returns. USDT payments are intentionally not implemented.
