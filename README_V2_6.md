# Egonia v2.6 — Early Activity Radar

Continues v2.5. Existing 9 trading-signal strategies, Binance/MEXC/Gate REST scanner, chart rendering, X and Telegram routes, and VIP membership remain intact.

## New
- Optional Binance **public** WebSocket, 1-minute closed candles, 20 top-ranked Binance altcoin markets by default.
- Seeds the prior 1m candle baseline from Binance REST, automatically reconnects socket, and refreshes subscriptions at roughly four-minute intervals.
- Detects unusual **1-minute activity**, with default volume >=3x average previous 20 minutes, absolute 1m price move >=0.7%, minimum 12,000 USDT minute quote volume.
- EARLY ALERT events are **separate** from LONG/SHORT trading signals. They do not claim an entry, stop, profit target or a verified prediction.
- Duplicate suppression / per-symbol cooldown 45 minutes, overall 12 daily alerts, persistent `early_alerts` SQLite table.
- New read-only JSON endpoint: http://127.0.0.1:8787/api/early-alerts and `early_alerts_total` + `early_alerts_recent` in `/api/operations`.
- Telegram VIP early alerts are opt-in to publication via `enable_telegram_vip`; X early posting additionally requires `early_publish_x=true` plus configured live X permissions. `dry_run=true` remains the default.

## Installation
Extract the ZIP to its own folder; run `START.bat`, which installs missing chart and WebSocket dependencies. Review `config.json`. No keys are needed for public market streams. Keep the Windows command window open.

For migrating data, shut down old bot and copy its `signal_service.sqlite` (and SQLite WAL/SHM sidecars if present) and your existing secret/config settings to the new folder. Never run two versions against the same database path concurrently.

## Scope limits
- **WebSocket early alerts cover Binance Spot only** at present. The regular scanning engine still scans all configured Binance/MEXC/Gate spot markets.
- WebSocket traffic is not independently live-tested in the build environment. Verify `Early radar WebSocket watching ...`, `EARLY ALERT ...` and `/api/early-alerts` on your Windows host.
- The 1-minute stream triggers on **completed candles**, not every trade tick. This is an early activity detector, not guaranteed advance prediction of a pump or dump.
- USDT payment and new VIP checkout are intentionally postponed.
