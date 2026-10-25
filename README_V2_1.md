# Crypto Signal Commercial v2.1 — Signal Priority & Channel Quotas

## New
- Consolidates all signals for each exchange/symbol scanned across 5m, 15m and 1h into one candidate, using deterministic strategy weights.
- If both LONG and SHORT strategies trigger in a single scan, no signal is published for that symbol on that scan.
- Multiple same-direction strategies appear in the signal reason; small bounded scoring bonus is a prioritization heuristic, **not** a predictive confidence or success probability.
- Channel-specific configurable daily *open message* quotas: `x_open_per_day` (5), `free_open_per_day` (2), `vip_open_per_day` (24).
- FREE minimum strength: `free_min_signal_strength` (65); X minimum remains `x_min_signal_strength` (75) and uses chosen featured strategies.
- VIP remains eligible for all generated signals; the global `max_signals_per_day` still caps total generation.

## Behavior, limitations
- 9 strategy families, 3 exchanges, dynamic altcoin market discovery and derivative eligibility retained.
- LIVE credentials and permissions still required. Default is dry run, and there have been no end-to-end social account publication tests.
- USDT billing is not included. Signals aren't trades and no profitable performance is established.
- Runtime can reuse existing v2.0 sqlite database; back it up before updating.

## Windows
1. Extract ZIP contents directly to a folder.
2. Keep config.json and .sqlite backup when upgrading.
3. Run START.bat (requires Python 3); check `http://127.0.0.1:8787`.
4. Run `python -m unittest discover -p "test_*.py"` for 56 tests.
