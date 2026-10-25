# EGONIA Signal Engine v2.5 — Market Intelligence

Upgrade from v2.4: an optional microstructure scoring/gating layer is applied to consolidated 9-strategy alerts. This is not a trained ML model, a probability of profit, or a backtest.

## Added
- Relative quote-volume regime from the last five *completed* bars versus the prior forty; requires consistent market bars as checked by the strategy engine.
- Volatility expansion proxy comparing candle-range percentage in recent five bars to earlier forty.
- Binance **spot order book** near-touch ±0.5% depth and top-of-book bid/ask spread filter. Fetched only for Binance signals, not every symbol. Data are a transient snapshot, not actual trade executions or futures depth.
- Reject Binance candidate when available book spread is above `intelligence_max_spread_pct` or near-touch quote liquidity is below `intelligence_min_depth_usdt`.
- If order book is inaccessible, the signal explicitly says ORDERBOOK_UNAVAILABLE; optional `require_orderbook=true` suppresses it. Non-Binance exchanges are not claimed to have depth confirmation.
- All historical v2.4 feature modules, Telegram, X, VIP, and product exclusions retained.

## Defaults
`enable_orderbook_filter=true`; `require_orderbook=false`; `intelligence_max_spread_pct=0.35`; `intelligence_min_depth_usdt=10000`; `intelligence_require_activity=false`.

## Limitations
No live provider credentials or network-based tests in this package. Binance spot depth is not evidence that a specific futures short is executable. Static target/stop are not strategy-calibrated; previous v5 target-touch statistics must not be represented as live hit rate. No USDT payment integration. Dry run and public publication disabled by default.
