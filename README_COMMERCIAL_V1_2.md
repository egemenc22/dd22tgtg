# X + Telegram Commercial Signal Bot v1.2

Windows 3.10+ / stdlib, local SQLite. No orders. **No automatic payment processing**; manual approval only after confirmed payment. Existing rule-based signal engine is *not proven profitable*. Posts are explicitly labelled PAPER.

## Configure

Set `enable_telegram_free`, `enable_telegram_vip`, and `enable_x` in `config.json` to true to queue posts for each channel (false by default). `free_open_per_day` limits FREE opening alerts; FREE alerts omit detailed entry/target/stop, VIP includes these details. `vip_sales_url` may point to your real landing page; leave empty otherwise. Post closing results for both channels.

Set environment vars `TELEGRAM_BOT_TOKEN`, `TELEGRAM_FREE_CHAT_ID`, `TELEGRAM_VIP_CHAT_ID` (Telegram bot must be admin in the private VIP channel), and the existing four X OAuth credentials. `dry_run=true` prevents actual publication. Real posting additionally requires `allow_unvalidated_publication=true`, explicitly labelling PAPER alerts; note public v1.2 only has Binance data and the unvalidated volume trigger.

## Membership workflow

After **independently verifying a payment**, note the purchaser's numeric Telegram user ID, then execute `VIP_GRANT_30_DAYS.cmd` or `py -3 signal_bot.py --members-action grant --user-id 123456789 --days 30`. You can inspect `py -3 signal_bot.py --members-action list` and cancel `py -3 signal_bot.py --members-action revoke --user-id 123456789`.

Set `enable_vip_member_enforcement=true` ONLY when the VIP bot is admin with invite and ban permissions. `VIP_SYNC.cmd` invokes Telegram API, generates 24h 1-use invite links for approved members, and removes expired/revoked users. Member enforcement also runs hourly when the service is on; API errors are logged and member record stores the error. These invite links use a one-use limit but **are not identity-bound to the purchasing user's Telegram ID**: a customer could share an unused link. Monitor membership accordingly. Do not share invite links or token publicly. Manual access approval must be tied to verified user identity. No auto-payment webhooks, checkout, automatic ID matching, or renewal billing is provided.

Only free/vip *channel-level* access exists; no personalized signals or subscribers' 1:1 delivery. VIP is a private Telegram channel you own, not an encrypted paywall. Creating a fresh release leaves your original SQLite untouched if you copy `signal_service.sqlite` and its `-wal/-shm` files **after stopping** the previous bot. Set environment variables before launch; never store secrets in the ZIP.

## Run/tests

Run `START.bat`, visit `http://127.0.0.1:8787`. Tests: `py -3 -m unittest discover -v`, `py -3 signal_bot.py --self-test`. Check `signal_service.log` and SQLite `delivery` for errors/needs_review. X/Telegram end-to-end live publish requires your credentials and was not run in the build environment.
