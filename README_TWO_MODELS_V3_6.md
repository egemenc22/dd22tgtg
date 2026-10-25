# Egonia — LONG/SHORT Scalp Models

- Only **Extra Trees SHORT `extra:8`** and **Random Forest LONG `forest:8`** from the supplied Candle Discovery v5 research source can generate new alerts.
- Exact raw 48 x 7 input channels using completed 5m bars.
- Product version `scalp_2h_v1`: 2-hour horizon, 1.2% target and 0.7% stop.
- Training labels walk future candles in order. A win requires the target before
  the stop; when both occur in the same OHLC candle, the conservative stop-first
  result is used.
- Old breakout/volume/momentum/WS early alerts **disabled**. REST scans all discovered Binance/MEXC/Gate assets.
- No trained `.joblib` files were provided. **Train once using your historical 5m SQLite** (`scalp_research.sqlite` containing `candles`). Launch `TRAIN_TWO_MODELS.bat`, supply its full file path. It creates `two_models/*.joblib` and `calibration.json`.
- Until two models are trained, **zero alerts are generated**; no fake predictions. Scans and panel still run.
- Threshold is `ml_probability_threshold=0.65` and opposing forecasts must differ by at least 0.08.
- Older 12h model artifacts are rejected and automatically retrained by `START.bat`.
- Live Telegram publication is enabled in `config.json`: FREE 2/day, VIP 6/day,
  with a 360-minute cross-exchange cooldown for the same symbol.
- `SETUP_ADMIN_TWEET.bat`: first send `/start` directly to @EgoniaSignalsBot, then run the file to save your numeric private chat ID to `CREDENTIALS.cmd`. Bot sends you a **private** copy after every successfully delivered FREE signal, with X intent **Tweetle** button. Public FREE channel never displays the button.
- X intent opens draft, not automatic tweet. X API remains disabled.
- Training needs `numpy`, `scikit-learn`, `joblib` (installed by TRAIN_TWO_MODELS). `START.bat` auto-installs if missing.
- Training writes the actual holdout first-touch result and market breadth to
  `two_models/calibration.json`. It is a historical estimate, not guaranteed PnL.

## Update
Stop previous version, unpack new ZIP, copy your old `CREDENTIALS.cmd`, optionally copy `signal_service.sqlite`. Run training with historical candles DB, set up private admin, then `START.bat`.
