# EGONIA v2.9.2 - Telegram credential setup fix

- New `SETUP_TELEGRAM.bat` securely prompts for BotFather token and writes correct Windows `set "NAME=value"` syntax into local `CREDENTIALS.cmd`.
- Immediately runs `CHECK_REMOTE_CONNECTIONS.bat` to check Telegram bot identity and posting rights in `@EgoniaSignalsFree`.
- Does not embed any token in the distribution ZIP. `dry_run=true` and public publication disabled by default.
- Prior v2.9 functionality and X local bridge remain unchanged.
- Telegram setup guide: `TELEGRAM_SETUP_TR.txt`.
