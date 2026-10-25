# Egonia v2.9.4 — Telegram photo HTTP 400 hotfix

The Telegram Bot API `sendPhoto` method requires a multipart file field named `photo`. Earlier builds mistakenly sent the file as `media`, leading to `HTTP 400 Bad Request` on FREE channel posts with attached charts. The field is now `photo` for Telegram, while X image upload continues to use `media`.

## Upgrade
1. Stop the old Egonia `START.bat` process.
2. Extract this ZIP into a fresh folder.
3. Copy your existing `CREDENTIALS.cmd` from the **old local folder** into the new folder (never share the token).
4. If retaining history, copy `signal_service.sqlite` and `charts/` while the bot is stopped; otherwise start fresh.
5. Run `CHECK_REMOTE_CONNECTIONS.bat`, then `SEND_FREE_TEST.bat` (text smoke test), then `START.bat`.

**Important:** Failed live sends may be marked `needs_review`, because the old server response did not include detailed error bodies. Such records are not automatically resent, to prevent duplicates. Newly generated signals use the corrected photo upload. The pre-existing FREE cap of two signals/day remains in effect.

This fix was tested locally with a strict simulated Telegram endpoint. Real sending has to be verified on your own Telegram channel.
