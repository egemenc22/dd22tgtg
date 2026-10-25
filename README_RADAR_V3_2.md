# EGONIA RADAR v3.2.0 — Signal relevance, not graphics

- Prioritizes stronger events **inside each scanner cycle** by score and turnover before daily FREE slots are assigned.
- Rejects stale queued alerts older than 12 minutes after the close of the 5-minute signal candle (`radar_max_alert_age_seconds`). Status: `expired`.
- Preserves the original Radar, legacy code, local Telegram configuration and text-only delivery.
- No prediction/edge guarantee, no new payments, VIP or X automations.
- **Limit:** Sorting happens within each 18-market scan cycle, not across the complete 225-market universe. The first cycles of a UTC day can still fill a 2-alert daily quota. Prioritization is better, not optimal.
- **Limit:** Failed/expired queued jobs still consume daily capacity. Conservative anti-spam default.
- When updating, close old program; extract ZIP to new folder; copy old `CREDENTIALS.cmd` (contains your bot token) and optionally old `signal_service.sqlite` when stopped. Run `CHECK_REMOTE_CONNECTIONS.bat` then `START.bat`.
- Startup still does not guarantee live alert delivery; verify console `RADAR SENT` and Telegram channel.
