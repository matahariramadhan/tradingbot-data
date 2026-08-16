# Historical hourly Binance dataset implementation

Date: 2026-08-16 UTC

## Scope

The active historical direction task has been replaced with an hourly task.
The earlier 15-minute package and notebook remain preserved as prototype
history. This record covers the local hourly implementation; it does not claim
that the four-year remote download or dataset build has completed.

Package version `0.10.0` is implemented at commit
`925e4d9f9a94a7ffb9f777caafbbe7badde337d1` and exposes:

```text
tradingbot-data historical-download
tradingbot-data historical-hourly
```

The separate runbook is `historical_binance_hourly_4y.ipynb`.

## Dataset contract

- Raw source: independent BTCUSDT historical 1-minute klines.
- Decision cadence: once per UTC hour at `HH:00`.
- Target: direction from the last completed close before the decision to the
  last completed close before the next hour.
- Feature inputs: completed 1-minute data only, including 1/5/15/30/60-minute
  returns, 5/15/60-minute volatility, recent volume ratio, 5-minute candle
  shape, moving-average context, and RSI.
- Target prices and target return are audit-only fields, never model columns.
- Target date range: `2022-08-16` through `2026-08-15` inclusive, with one
  short-term warm-up day.
- Split: explicit date boundaries for 1,023 training days, 219 validation
  days, and 219 holdout days, approximately 70/15/15.

## Local verification

Command:

```text
python3 -m unittest discover -s tests
```

Result: 44 tests passed. The focused hourly synthetic test verifies that future
bar changes alter the target but not features, preserves missing target
boundaries, creates 24 rows per day, verifies the explicit date split, and
skips verified daily outputs on rerun. Both Colab notebooks compile, and
`git diff --check` passes.

## Not established yet

No remote four-year row count, usable-row count, label balance, or final split
measurement has been established. Those values must come from the Drive-backed
hourly notebook run.
