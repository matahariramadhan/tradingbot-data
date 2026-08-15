# Historical 15-minute dataset implementation

Date: 2026-08-15 UTC

## Scope

This record covers the local implementation of the separate historical Binance
15-minute learning slice. It does not claim that the remote Binance download
or dataset build has completed.

The implementation is package `0.9.0` at commit
`91507cf3303bc0a88977091c3601175b3acd21e4` and is exposed through:

- `tradingbot-data historical-download`
- `tradingbot-data historical-15m`

The separate Colab runbook is `historical_binance_15m.ipynb`. The existing
recorder/proxy notebook is unchanged.

## Durable behavior

- Historical BTCUSDT 1-minute klines are downloaded as one UTC-day CSV per
  work unit.
- The download checkpoint and verified per-day output hashes are stored in the
  caller-provided durable directory.
- The dataset builder creates 96 fixed UTC quarter-hour rows per target day.
- Features use only completed 1-minute bars before the decision time.
- Target prices and labels are retained in the audit view but omitted from the
  model-ready feature columns.
- Missing feature or target boundaries remain invalid instead of being
  synthesized.
- The final report verifies audit/model output shape, unique model keys,
  chronological ordering, and disjoint train/validation/holdout partitions.

## Local verification

Command:

```text
python3 -m unittest discover -s tests
```

Result: 34 tests passed. The focused synthetic test also reran the builder
after its first completion and observed verified per-day outputs being
skipped. All notebook code cells compile, and `git diff --check` passes.

## Not established yet

No remote historical source row count, usable-row count, label balance, or
split count has been measured yet. Those values must come from the Drive-backed
run of `historical_binance_15m.ipynb`.
