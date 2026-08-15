# Colab Proxy-Target Recovery Result

Date: 2026-08-15

## Scope

The pinned `tradingbot-data` `0.4.1` recovery command processed the 29 eligible
proxy-target CSVs using the completed boundary report
`proxy-boundary-recovery-v1.json`. It resumed from the Drive-backed recovery
report and wrote the separate recovered view under
`proxy-targets-recovered-v1`.

## Verified result

- Input days: `29`.
- Completed days: `29`.
- Recovered rows: `28`.
- Used recovered boundaries: `28`.
- Unused recoverable boundaries: `0`.
- Recovery review rows: `0`.
- Total target rows: `8,352`.
- Valid target rows after recovery: `8,327`.
- Invalid target rows after recovery: `25`.
- Remaining quality flags: `12` `missing_end_boundary` and `13`
  `missing_start_boundary`.

The 2026-07-28 source remains validly incomplete for one unrecoverable final
boundary; its output contains 287 valid rows. The 28 recovered rows are
Binance-proxy labels with preserved boundary provenance. They are not official
Chainlink/Polymarket outcomes.

The original `proxy-targets` directory was not modified. The recovered view
passed the notebook's shape and quality checks and is eligible for a later
feature/target join, subject to keeping invalid rows out of the model-ready
view and preserving `label_source=binance_proxy`.
