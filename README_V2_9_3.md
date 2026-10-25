# EGONIA 2.9.3 – Telegram FREE LIVE

- Telegram FREE channel: `@EgoniaSignalsFree`
- Bot: `@EgoniaSignalsBot`
- `dry_run=false`, `allow_unvalidated_publication=true`, `enable_telegram_free=true`
- X and Telegram VIP disabled; early alert X posting disabled. Only selected normal signal posts are sent to FREE, up to 2/day (UTC). Bot can continue to scan markets and generate more signals independently.

## Windows setup (important)
1. Exit the old Egonia process (port 8787). Extract this ZIP to a **new** directory.
2. **Copy the existing `CREDENTIALS.cmd` from your working v2.9.2 directory** into the new directory, replacing the blank template. This preserves the valid token on your PC. Never send this file to anyone or upload it anywhere.
3. Run `CHECK_REMOTE_CONNECTIONS.bat` and confirm `telegram.ok=true`.
4. Run `SEND_FREE_TEST.bat` to send **one** labelled TEST message to the FREE channel. This test is deliberate and is not a trade signal.
5. Run `START.bat` to enable live Telegram FREE publishing. No X or VIP posts will be made.

**History:** If you want to keep old signals and database, copy `signal_service.sqlite` from the old folder while both instances are stopped. Do not run both against the same Telegram bot/channel simultaneously.

**Secret handling:** Telegram token is read from the local `CREDENTIALS.cmd` environment file, excluded from distribution. Never paste it into public logs or this chat.
