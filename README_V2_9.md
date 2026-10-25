# Egonia v2.9 — Local X Publisher Verification

Changes from v2.8:
- X Post Management draft creation is recorded as `draft`, NOT `sent`.
- Background publish request accepted by X Post Management is `queued_external`, NOT confirmed posted.
- A read-only `CHECK_X_LOCAL.bat` checks the local app health endpoint.
- When local_xpm is configured, setup validation no longer requires X official API keys.
- EARLY ALERT X routing obeys the local_xpm backend selection.

To use: start X Post Management separately, then run `CHECK_X_LOCAL.bat`. Keep `dry_run=true` initially. To enable local drafts, configure `x_backend=local_xpm`, `enable_x=true`, `dry_run=false`, `allow_unvalidated_publication=true`, `xpm_auto_publish=false`. Set `xpm_auto_publish=true` only when ready to request automatic publishing in XPM. Its queue confirmation is not proof of publication; check XPM history. The third-party tool depends on browser automation and may violate X terms.

No actual X post has been tested here. No XPM app is bundled.
