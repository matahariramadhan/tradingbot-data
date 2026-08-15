# Evidence: 2026-08-14 Colab Grouped-GZIP Manifest Inspection

Status: User-reported remote reproduction
Reproduction date: 2026-08-14
Scope: Structural inspection of the persistent Drive manifest

## Observed

- Manifest schema version: `2`.
- Physical layout: `grouped-gzip`.
- Configured audit scope: `binance_day_coverage`.
- Group count and candidate range: 30 groups from 2026-06-29 through
  2026-07-28.
- Source-role counts: 30 `binance_raw`, 30 `recorder_log`, and 29
  `polymarket_raw` members.
- All 30 processing statuses were `pending`.
- Present authoritative raw members represented 10.706 GiB.
- Candidate 2026-06-29 was the only incomplete group; it contained Binance raw
  and recorder-log inputs and explicitly lacked `polymarket_raw`.
- Ten derived CSV GZIP files were classified as
  `not_an_authoritative_raw_group_member`.
- No input descriptor had a malformed SHA-256-length value.

## Inference

The manifest structure matches the earlier independent 99-file Drive
inventory: 89 authoritative raw members plus 10 derived exports. This supports
the grouping and identity implementation; it does not establish timestamp
coverage or data quality inside any member.

## Consequence

The next checkpoint is a read-only timestamp and Binance day-coverage scan of
one complete candidate group before the manifest-controlled audit writes any
status or output.
