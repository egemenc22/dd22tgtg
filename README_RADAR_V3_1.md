# EGONIA RADAR v3.1.0 — Altcoin Intelligence

## What changed
- New `radar_mode=true`: replaces LONG/SHORT trading-signal publication with factual activity alerts.
- Five closed-candle event classifiers: UNUSUAL_VOLUME, EARLY_MOMENTUM, BREAKOUT, TREND_SHIFT, PUMP_DUMP_REVERSAL.
- One consolidated event per market/candle; cross-exchange, same-symbol 180-minute cooldown.
- Explainable activity priority score 0–100, NOT success probability.
- FREE: 86+ score; maximum 2 alerts per UTC day. VIP: disabled by default.
- All candidates are filtered by 25k USDT 5m turnover plus event-specific conditions; no guaranteed profits.
- Separate `radar_events` and `radar_delivery` SQLite tables; current legacy signal history remains untouched.
- Legacy queued signal deliveries and old 1m early alert publishing are DISABLED in Radar mode. X publishing is disabled.
- `/api/radar` returns the 30 latest radar events and delivery status; operations panel: http://127.0.0.1:8787.
- Real Telegram sending uses `sendMessage` to ensure a reliable baseline; no radar graphic cards yet.

## Installation (Windows)
1. Exit old running Egonia instance first. Extract this ZIP to a NEW directory.
2. Copy ONLY `CREDENTIALS.cmd` from the previous v2.9.4 working directory into this directory; overwrite placeholder. Do NOT share the filled file.
3. Run `CHECK_REMOTE_CONNECTIONS.bat` to confirm bot credentials and administrator permissions.
4. Run `START.bat`. New alerts appear as `RADAR EVENT` and successful Telegram delivery as `RADAR SENT` in console/log.
5. Open http://127.0.0.1:8787/api/radar to view recent events. The main status panel is http://127.0.0.1:8787.

## Configuration
- `radar_mode`: true
- `radar_min_score`: 78, minimum to store event.
- `radar_free_min_score`: 86, FREE publishing cutoff.
- `radar_free_daily_cap`: 2
- `radar_vip_daily_cap`: 16 (VIP route off)
- `radar_symbol_cooldown_minutes`: 180
- `dry_run=false`, `allow_unvalidated_publication=true`: LIVE FREE publishing is enabled after credential check. To test without publishing, set `dry_run=true`.
- `enable_telegram_vip=false`, `enable_x=false`, `enable_early_alerts=false`.

## Limitations and accuracy
- Score means event importance, NOT historical reliability or win probability.
- Live market-data fetch requires working exchange APIs. A fresh, closed 5-minute candle is required.
- FREE daily cap applies to alerts QUEUED for a UTC day, not only successfully sent alerts. Failed sends are marked `needs_review` and not auto-retried to avoid duplicates.
- The latest market discovered first wins cross-exchange duplicate suppression; strongest market across all exchanges is not globally ranked.
- There is no independently validated trading edge or proof of subscriber demand. No backfilled return numbers are claimed.
- For legacy log/database continuity, separately back up your existing `signal_service.sqlite`. Copying it into the new folder is optional; the newer radar tables are created automatically. Do not copy over an active database.
