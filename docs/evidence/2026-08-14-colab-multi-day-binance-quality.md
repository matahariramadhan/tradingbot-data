# Evidence: 2026-08-14 Colab Multi-Day Binance Quality Report

Status: User-reported Colab reproduction
Report date: 2026-08-14
Scope: 30 completed Binance day-audit outputs

## Aggregate measurements

```text
groups = 30
source_complete_groups = 29
records_scanned = 263322186
malformed_json = 0
missing_starts = 89677
duplicate_starts = 0
backward_starts = 0
gap_events = 55
largest_gap_seconds = 645.0
```

The report was saved in Drive at:

```text
/content/drive/MyDrive/tradingbot-data-audit/multi-day-binance-audit-v1.json
```

## Per-day observations

- 2026-06-29 was the only source-incomplete group and had 85,587 missing
  one-second starts, leaving only 813 of the expected 86,400 in-day starts.
- The largest gaps were 645 seconds on 2026-07-09, 486 seconds on 2026-07-27,
  471 seconds on 2026-07-25, and 226 seconds on 2026-07-01.
- The largest missing-start counts after 2026-06-29 were 1,197 on 2026-07-25,
  992 on 2026-07-27, 657 on 2026-07-09, and 607 on 2026-07-01.
- All 30 days had zero malformed JSON records, zero duplicate starts, and zero
  backward starts.

## Consequence

The collection is structurally readable and has reliable manifest/output
provenance, but kline coverage is not uniform. June 29 requires exclusion or
separate treatment because it is source-incomplete and severely under-covered.
The other high-gap days require gap-aware feature validity; a whole-day
exclusion must not be inferred from this report alone. The official target and
Polymarket source completeness remain unresolved.
