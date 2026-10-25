# Egonia Radar v3.3.2 — Telegram BUY/SELL template

- Telegram radar notifications now use `⚡ EGONIA ALERT`, `🟢 BUY` or `🔴 SELL`, with pair, exchange, detected event, price, recent volume multiple, five-minute move, momentum direction, and radar priority score.
- BUY/SELL reflects the direction of the latest fully closed five-minute candle; it does **not** represent a verified profitable trade prediction or a trading execution order.
- Templates use actual recorded radar event values, not fabricated examples. Small token prices display with up to eight decimal places.
- Coverage scanner, thresholds, FREE unlimited count, panel, channel delivery logic, existing strategy functionality retained.
- Move `CREDENTIALS.cmd` from your previous installation into this folder. Do not share the token. If preserving history, move the SQLite database while the bot is stopped.
- Start with `START.bat`; test the next genuine radar alert.
- 114 local unit tests passed. No end-to-end Telegram message was sent from this build environment.
