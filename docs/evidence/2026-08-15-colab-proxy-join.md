# Colab Proxy-Feature Join Result

Date: 2026-08-15

The repinned `tradingbot-data` `0.5.2` notebook reran the proxy join after
canonicalizing UTC timestamp keys and invalidating stale join checkpoints.

## Verified result

- Audit join rows: `8,352`.
- Model-ready rows: `8,292`.
- Excluded rows: `60`.
- Audit output: `/content/drive/MyDrive/tradingbot-data-audit/proxy-join-audit-v1`.
- Model output: `/content/drive/MyDrive/tradingbot-data-audit/proxy-model-view-v1`.
- The notebook verified 288 audit rows per eligible day, matching model-row
  counts to `eligible_for_model`, and `label_source=binance_proxy`.
- Model columns are exactly `window_start_utc`, `decision_time_utc`,
  `return_1s`, `return_1m`, `volatility_1m`, `label`, `label_source`, and
  `label_definition`.

Target prices and target receipt times are absent from the model columns. The
model-ready view is therefore an engineering/proxy dataset, not an official
Chainlink-labeled research dataset.

Using the previously verified feature and target counts, the 60 excluded rows
are consistent with 36 invalid feature rows, 25 invalid target rows, and one
row invalid on both sides. This is a derived consistency check; the join
report remains the authoritative output for exact per-row reasons.
