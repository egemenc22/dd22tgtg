# EGONIA RADAR v3.5.0 — market integrity and Gate live

## Changes
- Discovery cap raised from 75 to 150 per exchange; up to 450 markets total. Actual count depends on volume, eligibility and exchange APIs; this is NOT total market coverage.
- Minimum 24h USDT volume moved from $120,000 to $50,000, so lower-liquidity speculative tokens can enter the universe. Low volume is not market cap.
- Exchange-balanced discovery (Binance / MEXC / Gate). A market from each exchange gets considered before its next-ranked market, rather than crowding out smaller exchanges in the global list.
- Known tokenized-stock symbols, leveraged equities and recognizable ETF tickers blocked. Exchange metadata checked if available. This is NOT a complete guarantee: a newly listed tokenized stock can evade name filters. Review unknown tickers before public promotion.
- Gate `spot.candlesticks` 1m live WebSocket enabled, with per-symbol bootstrap of previous completed 1m quote-volume candles, ongoing partial-candle detection, reconnection and queue metrics. Gate may throttle connection/subscription counts; verify real Windows logs.
- Binance WebSocket, MEXC REST, Gate REST and Telegram alerts retained.
- Panel operations now includes `live_gate` in addition to `live_binance`.

## Limitations
- MEXC remains REST-based for radar. MEXC's current spot WebSocket sends protobuf binary payloads and has subscription limitations; it is not implemented here. Don't represent this version as realtime across all three exchanges.
- No external live Windows/exchange validation has been performed in this coding environment; automated mocked tests do not guarantee connection success.
- The broader 450-market scan may be slower and can trigger exchange rate limits; watch `/api/operations` coverage and failures. Reduce `max_pairs_per_exchange` to 100 if needed.
- Performance results and trading accuracy remain unproven. BUY/SELL is observed price direction rather than a validated profitable trade recommendation.

## Setup
1. Stop old bot. Extract ZIP into a new folder.
2. Copy CREDENTIALS.cmd from prior Egonia folder (never share the token).
3. Optionally copy signal_service.sqlite while stopped.
4. Run START.bat. Check `LIVE Gate connected`/`LIVE Gate subscribed` and `live_gate` at http://127.0.0.1:8787/api/operations.
5. FREE Telegram remains uncapped, quality threshold and repetition controls remain on.
