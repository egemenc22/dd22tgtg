# Egonia Signal Engine v2.7 — Live Publishing Setup

This update retains the v2.6 nine-strategy engine, Binance live early alerts, MEXC/Gate scanning, chart generation, publishing queue, and Telegram VIP membership.

## What is new
- `CREDENTIALS_EXAMPLE.cmd` — copy to `CREDENTIALS.cmd` and supply **your own** X OAuth 1.0a user access tokens and Telegram bot token/channel IDs.
- `START.bat` loads `CREDENTIALS.cmd` when present, without storing credentials in JSON.
- `CHECK_PUBLISHING.bat` — local readiness summary; does **not** post or contact providers.
- `CHECK_REMOTE_CONNECTIONS.bat` — read-only `getMe` and `getChatMember` checks for Telegram; read-only `GET /2/users/me` for X. No tweets or Telegram messages sent.
- Live startup refuses missing credentials for enabled routes.
- Publishing remains disabled by default.

## Telegram setup
1. Create two channels: Egonia FREE (public) and Egonia VIP (private).
2. Create a bot using BotFather. Add it as administrator to both channels, with **Post messages** permission. For VIP join-request approvals, also grant **Invite users**.
3. Set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_FREE_CHAT_ID`, `TELEGRAM_VIP_CHAT_ID` in `CREDENTIALS.cmd`. Channel IDs are typically negative `-100...` IDs; public channel usernames may also work.
4. In `config.json` set `enable_telegram_free` and/or `enable_telegram_vip` to `true`.
5. Run `CHECK_REMOTE_CONNECTIONS.bat` and check authorization.

## X setup
1. Use the developer account associated with @EgoniaSignals to obtain API credentials and **user context** access token + secret with write permissions.
2. Enter `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` in `CREDENTIALS.cmd`.
3. Set `enable_x: true` and run `CHECK_REMOTE_CONNECTIONS.bat` to check the identity. Ensure the returned username is the intended account; the script does not force the handle.
4. Current X image uploader lives in `chart_media.py`; X API access, media upload permissions and actual publishing need a real end-to-end validation. X may charge API fees.

## Switching from preview to live
Keep `dry_run: true` initially. A read-only connection check is **not** a live publishing test. When ready to publish, set BOTH `dry_run: false` and `allow_unvalidated_publication: true`. Only enabled channels are targeted. You are responsible for the account API setup and channel permissions.

## Safety and operational details
- Live sends are marked in-flight before calling external providers; ambiguous timeouts are left for review to avoid duplicates.
- Never share or upload `CREDENTIALS.cmd`. Do not hardcode bot tokens in public repositories. The archive deliberately includes **only** a blank example.
- This release does not implement USDT billing or claim that end-to-end X/Telegram publishing was tested.
- For CLI alternative, run `python signal_bot.py --check-publishing` or `python signal_bot.py --check-remote`.
