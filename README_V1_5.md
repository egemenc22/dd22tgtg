# v1.5 — Candlestick PNG + X / Telegram image posts

This is the complete v1.4 project plus a new image publishing layer.

## Run on Windows

1. Extract ZIP **directly** into one folder (no extra parent folder inside).
2. Install Python 3.10+; launch `START.bat`. It installs matplotlib when missing.
3. `config.json`: `enable_charts=true` (default); live channels remain disabled and `dry_run=true` by default.
4. Configure environment variables (do not hardcode secrets): `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`; `TELEGRAM_BOT_TOKEN`, `TELEGRAM_FREE_CHAT_ID`, `TELEGRAM_VIP_CHAT_ID`.
5. For actual remote posting set `dry_run=false`, `allow_unvalidated_publication=true`, `enable_x=true`, `enable_telegram_free=true`, `enable_telegram_vip=true` **only when ready**. `TEST_ONCE.bat` can test data collection without 24/7 operation.

## What images show

- Matplotlib renders **real closed Binance spot OHLC candles** used to generate the signal, capped at origin timestamp. No candles after detection appear.
- Entry, target, stop overlays, signal number, LONG/SHORT label. Saved as `charts/signal_<id>.png`.
- Telegram sendPhoto multipart; X API v2 INIT / APPEND / FINALIZE and tweet with media ID.
- If PNG is unavailable, old text-only publishing remains available; image generation errors are logged.
- Tweet publishing requires sufficient official X API permissions/credits. No third-party automation or scraped credentials.
- An API timeout may mean the post succeeded; live delivery is marked `needs_review`, not blindly reposted.

## Important implementation limits

- v1.5 continues using Binance Spot only; MEXC/Gate not implemented.
- No live accounts configured or tested; images and API calls checked with mocks only.
- No BTC billing yet. VIP membership management remains manual.
- No automatic post-publication TP/SL monitoring, per request.
- Current strategy selection / target / stop defaults are not established profitable trading signals.
