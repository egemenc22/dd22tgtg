# EGONIA Radar v3.4.0 — Binance Live WebSocket (Batch 02)

## What changed

- Watches **all discovered eligible Binance USDT spot pairs** via the public combined Binance `kline_1m` WebSocket (not merely the previous 20 symbols).
- Reads **unfinished 1-minute candles**, after at least 15 seconds of the candle, and compares extrapolated 1-minute quote volume with 15–20 already completed 1-minute candles. Also requires material observed price movement and minimum quote turnover.
- Sends qualifying live events to the **existing Radar database / BUY-SELL Telegram FREE queue** immediately via a dedicated worker, without waiting for the 5-minute REST scan.
- Keeps the existing REST coverage of Binance, MEXC and Gate as fallback and longer-term context, including existing Telegram FREE policies and delivery safeguards.
- Prevents duplicate posts from the live thread and REST thread via a serialized publishing lock and existing per-symbol Radar cooldown. Live event message labels say `1m Live Change`, not `5m Change`.
- No trading orders, no X publishing, no VIP payment integration.

## Installation — Windows

1. Stop old Egonia. Extract this FULL ZIP to a new folder.
2. Copy `CREDENTIALS.cmd` from your previous local install to the new folder. Do not paste token into chat. To carry over Radar history, also copy `signal_service.sqlite` **while both bots are closed**.
3. Run `START.bat`. Check for `LIVE Binance universe=...`, `LIVE WebSocket connecting ...`, and `LIVE WebSocket connected ...`.
4. Real-time detected events log as `LIVE RADAR ...` and successful sends as `RADAR SENT telegram_free ...`.
5. `http://127.0.0.1:8787` shows Radar events and delivery statuses.

## Configuration (`config.json`)

- `binance_live_ws`: true (disable to revert to REST-only Radar)
- `live_min_elapsed_seconds`: 15
- `live_min_volume_ratio`: 3.5 (current minute volume projected to 60 seconds relative to completed 1m baseline)
- `live_min_move_pct`: 0.65
- `live_min_quote_volume`: 12000 (actual accumulated USDT quote volume, not extrapolated)
- `radar_free_min_score`: 86 (unchanged)
- `radar_symbol_cooldown_minutes`: 180 (unchanged)

## Limitations / honest status

- Real-time WebSocket is enabled **for Binance only**. MEXC/Gate remain periodic REST until the following batch.
- This is **not a verified 15–30-second movement-detection SLA**. WS update latency, baseline warm-up, exchange connectivity and threshold crossing affect timing. Startup bootstraps 1m history over REST and may take time.
- During WS gaps, existing REST Radar keeps operating. Live signal quality and true end-to-end detection timing still need measurement from Windows logs and actual subscribers.
- Some eligible symbols may not bootstrap when an exchange rejects the requested candle history; those symbols remain in the REST scanner. Check `LIVE bootstrap` warnings.
- `BUY`/`SELL` label indicates direction of the detected price move; it is **not** a verified prediction or an executable trade entry.
