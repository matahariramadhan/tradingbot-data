# Colab Boundary-Recovery Result

Date: 2026-08-15

## Scope

The resumable boundary-recovery cell in `tradingbot_data.ipynb` scanned all 30
candidate-date raw source groups. June 29 was scanned as a source archive but
was excluded from the requested derived-view boundary set, leaving 29 requested
final-window boundaries. The scan searched for each day's completed
`btcusdt@kline_1s` interval beginning at `23:59:59` UTC and preserved the source
archive and receipt provenance in its Drive report.

Durable report:

`/content/drive/MyDrive/tradingbot-data-audit/proxy-boundary-recovery-v1.json`

## Result

- Requested boundaries: `29`
- Recoverable from the scanned raw archives: `28`
- Unrecoverable from the scanned raw archives: `1`
- Unrecoverable target day: `2026-07-28`
- All 30 source groups completed and checkpointed.

## Consequence

The archive-edge hypothesis is supported for 28 of the 29 final missing-end
rows: the required boundary can be found somewhere in the scanned raw source
collection. This does not yet regenerate the proxy-target CSVs; the source
provenance must first be applied through an explicit recovery step and then
the target outputs must be shape- and quality-verified again.

The `2026-07-28` final boundary was not found in the scanned source collection.
It remains an invalid target boundary unless a separately identified source is
verified. The 11 non-final missing-end rows and 13 missing-start rows remain
separate intraday data-quality problems.
