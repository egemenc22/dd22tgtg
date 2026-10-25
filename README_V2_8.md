# Egonia v2.8 — Optional X Post Management localhost adapter

Third-party project: https://github.com/LoicMeyerFrance/X-Post-Management (MIT license). The third-party app is NOT bundled, audited or installed by Egonia.

What was verified: XPM current `server/app.py` exposes `POST /api/posts` (multipart `text`, optional `image`, `status=draft`); `POST /api/posts/{id}/post-now` queues a publication task. These are *local* app endpoints, not X APIs. Creating a draft or queueing a task does not verify a tweet appeared on X.

1. Install/run X Post Management **separately**, using its official release/source. Its app defaults to port 5000, but check the actual port in its UI/logs.
2. In `config.json`, change `x_backend` to `local_xpm` and `xpm_origin` to its loopback origin. Leave `xpm_auto_publish: false` to **create drafts only** for the first test.
3. To process X deliveries, `enable_x: true`, `dry_run: false`, `allow_unvalidated_publication: true` must already be configured. Telegram routes are independent. Keep `x_open_per_day: 2`.
4. Once XPM draft creation works, if you knowingly choose hands-free queueing set `xpm_auto_publish: true`; the local manager then attempts posting through browser automation. X may prohibit non-API web automation and may restrict the account.
5. Never copy X password into Egonia. XPM manages its own browser session. Be aware its local HTTP service should be trusted; do not expose it on a public interface.

**Limits:** No claims of end-to-end success. XPM local `/post-now` returns an asynchronous queue acknowledgement, not a real X tweet ID. Egonia stores `xpm-draft:N` or `xpm-queued:N` and does not retry uncertain requests automatically. Confirm successful publication inside XPM/X. Existing Egonia `status='sent'` means the local handoff succeeded, not that X accepted the tweet.

To use the official X API instead, leave `x_backend: official` (default). USDT billing untouched.
