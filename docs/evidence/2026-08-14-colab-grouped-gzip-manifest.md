# Evidence: 2026-08-14 Colab Grouped-GZIP Manifest

Status: User-reported remote reproduction
Reproduction date: 2026-08-14
Scope: Manifest creation for the Google Drive direct-GZIP collection

## Method

The pinned `tradingbot-data` version `0.2.0` manifest command scanned the raw
Google Drive directory recursively using the explicit `grouped-gzip` layout.
It wrote the control artifact outside the raw-data directory.

## Observed

- The command completed successfully and reported `archive_count: 30`.
- The manifest was written to
  `/content/drive/MyDrive/tradingbot-data-audit/manifest-v2-03abbb7.json`.
- No detailed manifest-content inspection or source-data audit was included in
  the reported output.

## Consequence

The collection now has a persistent checksum-bearing control manifest. Its
schema identity, source-role counts, incomplete group, ignored derived files,
and initial statuses must be inspected before any group audit begins.
