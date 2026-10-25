# EGONIA v3.7.1 — Crypto-only universe refinement

- Binance, MEXC and Gate spot USDT coin discovery retained, including memecoins and low-volume speculative crypto tokens.
- Traditional equity, ETF, bond, index and wrapped stock tracker descriptions are excluded where exchange metadata identifies them; known symbols and leveraged synthetics are blocked.
- A description containing only “token”, or “tokenized” without an underlying traditional security, is **not** blocked.
- Discovery filter is applied before all model prediction and Telegram publishing; no additional legacy signal strategies are switched on.
- Real-time coverage and ML execution behavior unchanged. START.bat remains the entrypoint.
- Limit: exchange metadata can omit or misclassify instrument type, so an automated classifier cannot guarantee excluding every newly listed stock-like token. A stronger external asset registry would be required for definitive verification.
- No live exchange or Telegram tests performed in the packaging environment.

## Run
Extract the ZIP, copy CREDENTIALS.cmd from the prior installation, then run START.bat. Keep your existing config.json if you have customized it. Run TESTS.bat for local tests.
