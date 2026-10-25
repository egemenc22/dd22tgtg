# Crypto Signal Commercial v1.4 — Multi-Strategy

## Upgrade from v1.3
Keep the whole ZIP together. Run `START.bat` on Windows. Dashboard: http://127.0.0.1:8787 . Python 3 required, no pip packages.

## Signal generation
- Binance SPOT REST closed candles for configured symbols, on 5m, 15m and 1h. **MEXC and Gate are not yet connected.**
- EMA_TREND — EMA20 reclaim/rejection with EMA50 trend filter (not ADX).
- DONCHIAN_20 — 20 closed-bar price channel breakout.
- BB_SQUEEZE — volatility compression plus band break.
- RSI_BB_REVERSION — band reentry plus RSI filter.
- ATR_CHANNEL — EMA20 +/- 1.5 ATR channel cross (not exact Supertrend).
- MACD_MOMENTUM — MACD positive/negative crossover.
- Each strategy emits a one-time alert on the most recently **closed** candle; no future candles or post-hoc signals. One signal per symbol per configured cooldown; default 18 total/day, 2h symbol cooldown. First qualifying signal wins if multiple strategies fire at once.
- `strategy_names` and `strategy_timeframes` in `config.json` change enabled strategies / periods. `strategy_mode:false` restores v1.3 volume-activity rule.
- `enable_result_tracking:false` (default) means no post-publication position/TP/SL tracking or closure messages. Entry, target and stop remain **reference levels**, not actual trades.
- `dry_run:true`, publication flags disabled by default; turn on only when channel settings and credentials are ready. `allow_unvalidated_publication:true` is additionally required for live posting.
- Telegram FREE, Telegram VIP, X and VIP join checks from v1.3 remain supported. **X chart images and BTC payment automation are NOT in this build.**

## Limitations
- The engine does not establish the profitability of these familiar technical indicator strategies, and it places no orders.
- Running on one Windows machine needs continuous internet, time synchronization, and bot administrator rights in the Telegram VIP channel.
- `START.bat` starts the service. `TEST_ONCE.bat` runs a single cycle for smoke test. `python -m unittest discover -v` runs automated offline tests.
