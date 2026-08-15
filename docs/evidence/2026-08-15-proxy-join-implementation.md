# Proxy-Feature Join Implementation

Date: 2026-08-15

## Design

The next workflow slice is a separate join-integrity gate between the
gap-aware Binance feature view and the recovered Binance proxy-target view.
Rows are matched by the exact `window_start_utc` prediction-window key. A
duplicate key in either source stops that day's join for review; the command
never silently chooses one duplicate.

The command produces two per-day outputs:

1. an audit join containing the union of source keys, both source rows with
   explicit prefixes, and `eligible_for_model` plus an eligibility reason;
2. a model-ready proxy view containing only rows where both source flags are
   valid.

The initial model feature columns are deliberately limited to
`return_1s`, `return_1m`, and `volatility_1m`. Target-side values such as the
proxy end price, target receipt time, and label are not placed in the feature
columns. The model view retains only the label and its proxy-source metadata
alongside the three feature values.

## Local implementation

- New command: `tradingbot-data proxy-join`.
- Package version in the working tree: `0.5.0`.
- Per-day outputs are atomic and checkpointed in a JSON report with input and
  output SHA-256 values; verified days are skipped on rerun.
- The complete local unittest suite passed: `19` tests.
- Notebook and remote execution have not yet been updated for this command.
