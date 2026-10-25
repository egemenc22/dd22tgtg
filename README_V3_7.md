# EGONIA v3.7 — Coin-Only Two-Model Live Bot

* START.bat is the sole normal launch step after copying CREDENTIALS.cmd.
* Only Random Forest LONG and Extra Trees SHORT can generate public signals. No legacy radar strategies publish.
* On the first run, if trained model files are missing, the system fetches recent exchange 5-minute historical candles and automatically fits these two specific algorithms. Later launches reuse cached model files. This is mathematically necessary for Random Forest and Extra Trees; it does not require a pre-existing local database or manual TRAIN batch.
* Binance, MEXC and Gate spot USDT coin markets with lower 24h volume floor (15k USDT), 500 eligible symbols per venue max, 180 candidate scans per cycle. These are *not* all coins on every venue; cap and exchange uptime still apply.
* Tokenized-equity stock/ETF symbol list and available exchange metadata filtered; no string-only filter can promise perfect coin classification. Gold-backed commodities and stablecoins excluded.
* One click still requires Internet access and Python dependencies. Model bootstrap can take substantial runtime and may fail if public exchanges throttle historic candle requests; honest failure, never invented BUY/SELL outputs.
* Existing public Telegram delivery and private admin Tweetle button preserved. Admin setup requires the previously configured admin chat id in CREDENTIALS.cmd.
* New coins on DEXs such as Raydium, Uniswap and PancakeSwap are NOT covered. These would need an independent DEX market and onchain-token vetting pipeline.
