# v1.8 — Altcoin & Shitcoin Focus

## New
- Altcoin-first automatic USDT market discovery on Binance/MEXC/Gate.
- Majors are excluded from the default **focused** discovery ranking; there is no market-cap data, so the engine does NOT claim to classify coins as small-cap by capitalization.
- Select eligible markets based on 24h quote volume, reported price change and reported high-low range when available.
- New VOLUME_BREAKOUT rule: last completed bar breaks the previous 20-bar high/low on >=3x prior 20-bar quote volume, minimum 15,000 USDT candle quote volume, and 0.8%-15% candle close movement.
- Strategy works on 5m, 15m and 1h where candle feeds are available.
- Free/VIP Telegram delivery, image/chart support and X delivery remain unchanged.

## Defaults
- altcoin_focus: true
- min_daily_quote_volume_usdt: 120,000
- max_daily_quote_volume_usdt: 150,000,000
- max_pairs_per_exchange: 75
- markets_per_cycle: 18
- discovery_refresh_seconds: 1800
- max_signals_per_day: 24
- Volume-breakout added to strategy_names.

## Operational caveats
- No guarantee or probability of hitting a target. Prices can reverse quickly; low-cap tokens are especially risky.
- Exchange discovery uses spot USDT pairs. A SHORT alert does **not** establish that the symbol can be shorted on that exchange; confirm separately before presenting as tradable short opportunity.
- X/Telegram live sending needs valid credentials. Test locally; dry_run defaults to true.
- Future changes: exchange-specific listing age and perpetual availability filters, measured live signal volume and messaging QA.
- Payments (USDT) are deferred.

## Start
Run `START.bat` on Windows, then visit http://127.0.0.1:8787.
`TEST_ONCE.bat` performs a single cycle. No Windows .bat scripts are executable in this Linux-based test environment.
