# Evidence: 2026-08-14 Colab Coverage Map

Status: User-reported Colab reproduction
Reproduction date: 2026-08-14
Scope: Binance receipt-date coverage for all manifest groups

## Observed

The streaming coverage scan ran against the manifest-selected Binance GZIP
inputs in Google Drive.

```text
verified groups = 30
review groups = 0
coverage map = /content/drive/MyDrive/tradingbot-data-audit/coverage-map-v1.json
coverage report = /content/drive/MyDrive/tradingbot-data-audit/coverage-report-v1.json
```

Every group had receipt timestamps that were unambiguous, usable, and confined
to the candidate UTC date. The map was written only after all 30 groups passed
that check.

## Consequence

The explicit group-to-UTC-day coverage gate passed for the full collection. The
next operation is the resumable batch Binance audit, using the saved map and
persistent Drive output directory. Source-role completeness remains separate:
the June 29 group still lacks its Polymarket raw input.
