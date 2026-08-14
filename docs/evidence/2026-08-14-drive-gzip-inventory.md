# Evidence: 2026-08-14 Google Drive GZIP Inventory

Status: User-reported remote inventory  
Inventory date: 2026-08-14  
Scope: Recorder-data directory mounted in Google Colab from Google Drive

## Method

The mounted directory was scanned recursively for `.gz` files. Files were
classified by their names as Binance raw events, Polymarket raw events,
recorder logs, or other compressed outputs. Dates embedded in names were used
only to form candidate groups for inventory; they were not accepted as proof of
actual UTC coverage.

## Observed

- 99 GZIP files totaling approximately 10.75 GiB were found.
- Candidate date range: 2026-06-29 through 2026-07-28.
- 30 Binance raw-event files were present.
- 29 Polymarket raw-event files were present.
- 30 recorder-log files were present.
- 10 other GZIP files were present.
- Twenty-nine candidate dates contained Binance, Polymarket, and recorder-log
  inputs.
- Candidate date 2026-06-29 contained Binance and recorder-log inputs but no
  Polymarket raw-event input.
- The 10 other files were derived CSV exports for June 29 or June 30:
  aggregate trades, book ticker, one-second klines, Polymarket markets, price
  changes, top book, and trades.
- The June 29 Binance raw file and derived files were much smaller than the
  subsequent full-day examples, consistent with a partial recording candidate;
  actual coverage still requires timestamp verification.

## Consequence

The remote collection is not stored in ZIP containers. The current ZIP-only
manifest and readers must not be run against it. The raw `.jsonl.gz` files and
recorder logs should remain unchanged. Derived CSV exports must remain separate
from raw source identities. A revised workflow needs direct-GZIP input support,
logical dated capture groups, explicit missing-member representation, and an
independently verified UTC coverage map.

