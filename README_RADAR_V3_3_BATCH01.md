# EGONIA RADAR v3.3.0 — Batch 01: Market Coverage

This is the **complete** v3.2.0 distribution plus Batch 01 improvements.

## Implemented
- Radar-only concurrent candle retrieval (bounded ThreadPoolExecutor, 8 workers by default; maximum 12).
- Scans all **discovered** pairs within a radar pass (`markets_per_cycle=225`), subject to the configured per-exchange discovery cap (75/exchange by default). This is NOT every exchange listing.
- Per-market scan telemetry persisted in SQLite `scan_coverage`: scan timestamp, last closed candle, API error, request duration.
- `/api/operations` includes `coverage` measuring scan coverage over the previous 5 minutes, error count and p95 candle age.
- Cycle logs now include `COVERAGE 5m=...`.
- Telegram FREE radar daily numerical cap removed (`radar_free_daily_cap=0`). Existing minimum score, per-symbol cooldown and stale-alert expiry remain.
- X and VIP remain disabled. No new prediction/graphics.

## Realistic limits
- Market data remains REST polling for Radar; no full-universe WS coverage yet.
- One pass fetches 5m candles and processes at most 225 configured discovered pairs, and the actual duration depends on API/network/rate limits.
- A coverage percentage is meaningful only after discovery and a completed pass; it does not prove sub-minute alert latency.
- `poll_seconds` sleep occurs **after** finishing the pass; if a pass takes longer than 60 seconds, cycle time exceeds one minute.
- FREE Telegram has no daily *number cap*, but alerts still require a high score, cooldown, freshness and a working bot token.

## Windows
1. Stop previous Egonia instance.
2. Extract this ZIP into a NEW directory.
3. Copy old `CREDENTIALS.cmd` into the new directory; never share its contents.
4. If you want to keep history, copy the old `signal_service.sqlite` ONLY with both processes stopped.
5. Run `START.bat`, open http://127.0.0.1:8787/api/operations.
6. Observe `coverage` values and console `COVERAGE` logs for several cycles.

## Roadmap
Batch 02 global candidate ranking across the entire discovered universe; Batch 03 dedupe, exchange consensus and quality; Batch 04 delivery reliability and FREE/PRO routing; Batch 05 X publishing 4/hour 12/day; Batch 06 performance analytics; Batch 07 subscriptions; Batch 08 production soak tests.
