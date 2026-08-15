# Colab Binance Proxy-Target Batch

Status: measured; timestamp classification completed, adjacent-source recovery pending

Run date: 2026-08-14

## Scope

Package version `0.3.0` built separate Binance proxy-target CSVs for the 29
eligible days. June 29 was excluded by the accepted source-completeness
policy. July 27 used the already verified-shape canary output.

## Result

- Windows requested: `8,352`
- Valid targets: `8,299`
- Invalid targets: `53`
- Missing start boundaries: `13`
- Missing end boundaries: `40`
- Duplicate boundaries: `0`
- Valid targets with late start receipts: `8,299`
- Statuses: `28` newly completed, `1` existing valid-shape output skipped,
  `1` excluded by policy
- Batch report:
  `/content/drive/MyDrive/tradingbot-data-audit/proxy-target-batch-v1.json`

Per-day outliers were:

- 2026-06-30: `283 / 288` valid
- 2026-07-01: `283 / 288` valid
- 2026-07-09: `284 / 288` valid
- 2026-07-16: `285 / 288` valid
- 2026-07-25: `280 / 288` valid
- 2026-07-27: `283 / 288` valid

The other eligible days produced `287 / 288` valid targets.

## Timestamp classification

The 40 missing-end rows divide into:

- `29` final `23:55:00` windows, exactly one per eligible day;
- `11` non-final intraday windows: 2026-06-30 at 00:05 and 03:15,
  2026-07-01 at 06:55 and 07:30, 2026-07-09 at 07:40, 2026-07-16 at
  05:55, 2026-07-25 at 07:40, 07:50, and 08:25, and 2026-07-27 at 14:45
  and 16:10.

The 13 missing-start rows are also intraday and cluster around those gap
periods. The 29 final rows are systematic archive-edge candidates rather
than 29 independent intraday gaps. Whether their boundary observations can
be recovered from adjacent-day raw archives is still unresolved.

The invalid target rows must not be treated as the final research count until
the adjacent-day recovery question is resolved.

Late start receipts remain allowed for this offline proxy-label table and do
not make a target-time feature eligible.
