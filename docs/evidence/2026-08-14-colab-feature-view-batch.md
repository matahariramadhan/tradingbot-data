# Colab Feature-View Batch

Status: user-reported remote reproduction

Run date: 2026-08-14

## Scope

Package version `0.3.0` was run in Google Colab against the Drive-backed
Binance direct-GZIP collection. The batch used the manifest and verified
coverage map, excluded source-incomplete 2026-06-29 according to the accepted
policy, and wrote one 288-row CSV feature view per eligible UTC day.

## Result

- Eligible days: `29`
- Excluded days: `1` (`2026-06-29`)
- Newly processed days: `28`
- Existing valid-shape output skipped: `1` (`2026-07-27`)
- Rows requested: `8,352` (`29 * 288`)
- Fully usable feature rows: `8,316`
- Rows not fully usable: `36`
- Batch report:
  `/content/drive/MyDrive/tradingbot-data-audit/feature-view-batch-v1.json`

Usable rows by day:

| Day range | Usable rows |
| --- | ---: |
| 2026-06-30 | 287 / 288 |
| 2026-07-01 | 285 / 288 |
| 2026-07-02 through 2026-07-24 | 287 / 288 each |
| 2026-07-25 | 286 / 288 |
| 2026-07-26 | 286 / 288 |
| 2026-07-27 | 284 / 288 |
| 2026-07-28 | 287 / 288 |

## Consequence

The feature-view pipeline now covers every eligible day with a fixed,
five-minute row grid and preserves unusable rows instead of silently dropping
them. The 36 invalid rows must next be classified by their recorded quality
flags. Only after that review should the Binance proxy targets be joined to
the feature view.

This batch result verifies output shape and usable-row counts. It is not yet a
checksum-bearing derived-dataset release, and it does not establish official
Chainlink or Polymarket labels.
