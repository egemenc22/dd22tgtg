# v2.0 — Altcoin Early-Move Alerts

Adds two deterministic strategies to the existing 7, for **9** strategy families total.

- `VOLUME_ACCELERATION`: sustained 3-bar quote-volume acceleration, minimum activity and price approaching prior 20-bar range boundary without breaking it yet.
- `MOMENTUM_IGNITION`: three sequential directional closes with rising candle-range activity and restrained 3-bar price change.
- Both use *closed, consecutive OHLCV candles*. No future-bar data or target-hit tracking is needed.
- Both publish into the same Telegram VIP queue and can be selected for X; the existing per-coin cooldown, futures eligibility for shorts, and daily cap remain in effect.
- All scores are heuristic strength scores, not calibrated probabilities.
- USDT payment remains deferred. Live exchange/social tests not performed; `dry_run` remains enabled.

## Run
Extract ZIP, run `START.bat`; dashboard: http://127.0.0.1:8787. Tests: `python -m unittest discover -p "test_*.py" -v`.
