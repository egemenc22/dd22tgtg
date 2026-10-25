# v1.6 — Binance + MEXC + Gate Multi-Exchange Spot Market Feeds

Same v1.5 bot and media publisher, with read-only candle ingestion from the official public Spot endpoints of three exchanges. Nothing places orders.

## Run
- Extract ZIP into one Windows folder, start via `START.bat`; localhost dashboard: http://127.0.0.1:8787.
- In `config.json`, `exchanges` selects `Binance`, `MEXC`, and/or `Gate`; default all three. `symbols` contains Binance-format tickers (`BTCUSDT`).
- MEXC `1h` is requested as `60m`; Gate `BTCUSDT` is requested as `BTC_USDT`.
- Defaults: 10 tokens x 3 exchanges x 3 timeframes = 90 public OHLC requests per polling cycle. Be mindful of rate limits and local ISP access. Each request failure is logged; other symbols/exchanges continue.
- Closed candles only. Strategies, visual tweet cards, Telegram Free/VIP, membership management unchanged.
- A global per-symbol cooldown blocks near-simultaneous signals for the same token across exchanges. First encountered exchange in `exchanges` order takes precedence. `max_signals_per_day` is also shared.
- Graph captions and posted signals show the exchange where the trigger was observed, not necessarily the venue on which an end user should place an order.
- `enable_result_tracking=false` remains default. Do not enable legacy outcome tracking across venues; multi-exchange outcome accounting is not supported in v1.6.
- No live account API credentials were available; public market API access from your Windows PC and live X/Telegram posting still need integration verification.
- BTC auto billing is not integrated. Manual VIP grant remains in place.

Run tests using `python -m unittest discover -p "test_*.py" -q`.
