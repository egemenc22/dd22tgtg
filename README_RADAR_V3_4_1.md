# EGONIA Radar v3.4.1 — Reliability & Telemetry

Based on v3.4.0. No live trading, no orders, X and VIP remain disabled by config.

- Closed 1-minute Binance candle is evaluated against previous candles before its volume is appended to the rolling baseline. Prevents the current candle diluting its own anomaly measurement.
- Rejects NaN/infinite/invalid pricing or volume inputs in early detection.
- Binance live WebSocket health snapshot now appears in `/api/operations` as `live_binance` and on the local panel: connected, symbols, baseline-seeded pairs, last message age, message count, event queue length, queue drops, recorded events and latest socket error.
- Existing Binance WebSocket, REST fallback, MEXC/Gate REST coverage, Telegram BUY/SELL template and free channel configuration preserved.
- Does not claim all markets are truly live or guarantee an alert latency; check metrics on the Windows machine after deployment.

## Update
1. Stop previous version.
2. Unzip in a new directory.
3. Copy **your own** `CREDENTIALS.cmd` from the last folder (the distributed credentials template has no secret token).
4. If you want prior Radar history, copy `signal_service.sqlite` while both bots are stopped.
5. Run `START.bat`, open `http://127.0.0.1:8787/api/operations` to inspect `live_binance`.

No need to send the Telegram bot token to anyone. Beware that a previous package may include a blank local credentials stub which must be overwritten.
