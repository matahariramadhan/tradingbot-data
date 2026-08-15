# Evidence: 2026-08-14 Colab Batch Binance Audit

Status: User-reported Colab reproduction
Run date: 2026-08-14
Scope: All 30 manifest groups, Binance day-coverage audit

## Observed

The pinned `tradingbot-data` `0.2.0` batch ran against the verified coverage
map and persistent Google Drive output directory.

```text
processed = 30
failures = 0
new completed groups = 29
already-completed groups skipped after output verification = 1
```

The skipped group was `2026-07-27`. Its existing output was verified before it
was skipped. The other groups, from `2026-06-29` through `2026-07-28`, produced
audit outputs under:

```text
/content/drive/MyDrive/tradingbot-data-audit/audit-outputs/
```

A separate read-only verification then inspected the manifest and every output:

```text
total groups = 30
statuses = {'completed': 30}
problems = 0
```

The verification checked output existence and recalculated every recorded
output SHA-256 checksum.

## Consequence

The full Binance day-coverage audit workflow completed without reported
failures for all 30 candidate groups. This establishes per-day Binance audit
outputs and processing provenance. It does not yet establish research
readiness, official Polymarket outcomes, Chainlink labels, or feature validity
across all gaps.

The next checkpoint is an aggregate report of the multi-day gap and coverage
summaries.
