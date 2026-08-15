# Colab Feature-View Quality Review

Status: completed row-level quality review

Run date: 2026-08-14

## Observed counts

The persisted 29-day feature view contains `8,352` rows. `8,316` rows are
fully usable and `36` are invalid but preserved in
`invalid-feature-rows-v1.csv`.

Feature-level flags:

- `received_after_cutoff`: `29`
- `missing_kline`: `7`

Component-level flags:

- `return_1s_quality_flag=received_after_cutoff`: `29`
- `return_1m_quality_flag=received_after_cutoff`: `29`
- `volatility_1m_quality_flag=received_after_cutoff`: `29`
- `return_1m_quality_flag=missing_kline`: `7`
- `volatility_1m_quality_flag=missing_kline`: `7`

## Timestamp review

All 29 `received_after_cutoff` rows have decision time `00:00:00Z`, exactly
one at the opening of each eligible UTC day. They are the expected boundary
effect: the prior completed observation was not available at the exact opening
cutoff.

The 7 `missing_kline` rows are isolated intraday lookback gaps:

- 2026-07-01 at 04:15, 07:05
- 2026-07-25 at 07:50
- 2026-07-26 at 17:05
- 2026-07-27 at 14:15, 14:20, and 15:45

They must remain preserved and must not be repaired by inventing prices or by
excluding an entire day automatically.

## Consequence

The model-only feature view can later exclude rows where
`feature_row_usable=false`, while the audit view retains all 8,352 rows and
their quality flags. The feature-quality gate is now understood; the next
step is to build the separate Binance proxy targets.
