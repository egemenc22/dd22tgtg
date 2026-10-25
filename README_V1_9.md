# Crypto Signal Commercial v1.9 — Altcoin Futures & X Curation

## Added
- Public, read-only futures contract discovery for Binance, MEXC and Gate. SHORT signals are rejected unless the symbol is present in that same exchange's active USDT perpetual catalog. Discovery failures fail closed for SHORTs; LONG signals continue using spot OHLCV.
- Persisted `observed_markets` table with `first_seen` and `last_seen` timestamps. These mean **first observed by the bot**, NOT a verified first exchange listing date. They cannot be advertised as newly listed without exchange-specific listing data.
- X-specific curation: only select signals (default strength >=75 and one of VOLUME_BREAKOUT, DONCHIAN_20, BB_SQUEEZE). Telegram VIP retains all signals that pass core strategy rules.
- Existing market discovery, charts, Telegram, X sender and member flows preserved.

## Configuration
- `require_futures_for_short`: true. If futures API is unavailable, SHORT signals on that exchange are skipped.
- `x_min_signal_strength`: 75. This is a heuristic indicator score, not a probability or win-rate.
- `x_featured_strategies`: list of strategy labels eligible for X feed.
- No execution of orders. No automated payment yet; USDT payments deferred.

## Caveats
- Spot candles remain the source for strategy signals. A futures listing check confirms instrument existence, **not** executable entry price/spread/orderbook or borrow rate. Venue-specific spot/futures basis may differ.
- Real exchange API and social-media account end-to-end tests have not been run. X and Telegram are disabled by default (`dry_run`: true).
- `first_seen` is not proof of a brand-new exchange listing.

## Run
1. Extract the ZIP on Windows.
2. Run `START.bat`.
3. Visit http://127.0.0.1:8787.
4. For tests run `python -m unittest discover -p "test_*.py" -v`.
