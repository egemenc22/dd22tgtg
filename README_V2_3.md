# Egonia Signal Engine v2.3 — Altcoin Product Filter + Historical Research Reference

## What changed
- Excludes common leveraged spot derivative names (3L/3S, 5L/5S, 2L/2S, UP/DOWN/BULL/BEAR).
- Explicitly excludes false positives observed in the first live discovery: SPCX5S, NEAR5S, SNDK5S, SKHYNIX5S and SOXLB, with a narrow equity-style token filter.
- Applies exclusions during market discovery on Binance, MEXC and Gate AND in the altcoin ranking function.
- Added regression tests for all three exchange discovery formats.
- Preserved nine current technical strategies, chart posting plumbing, Telegram FREE/VIP membership and local operations UI.
- Bundled `historical_research_reference.json`: old v5 classifier's historical TARGET-TOUCH results only. The trained models are not contained in this ZIP and are NOT linked to the live signal engine. Do not report those percentages as realized trade wins or model-derived live confidence.

## What the previous research showed
For 12h SHORT target -5%, target-touch precision was 79.08% on the historical test; LONG +5% was 74.074%. This is a retrospective target-touch test, NOT executable trade profitability. The separate v6 execution audit did not validate a profitable live strategy; no imported trade model claims.

## Run
Extract ZIP to a fresh directory. Edit config.json for credentials. Run `START.bat`. Open http://127.0.0.1:8787. Default dry_run is enabled, external posting disabled. Run `TESTS.bat` to execute regression tests.

## Known limitations
- Name-pattern filter cannot classify every synthetic/tokenized security. Explicit exchange asset metadata or curated symbol classification is still required for full coverage.
- Requires actual credentials for live X/Telegram. Does not contain USDT payment collection.
- Existing signal history in local SQLite is not purged automatically (historical synthetic signals remain records). New discoveries will be filtered.
- Current signal targets and stops are static defaults, not outputs of the prior machine-learning model.
