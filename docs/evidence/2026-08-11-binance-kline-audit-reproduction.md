# Evidence: 2026-07-27 Binance Kline Audit Reproduction

Status: Point-in-time reproduction  
Audit date: 2026-08-11  
Scope: One local daily archive, with a strict UTC-day filter

## Method

The audit streamed the compressed Binance JSONL member directly from the ZIP
archive without extracting it using
`scripts/audit_binance_klines.py`.

The target interval was `[2026-07-27T00:00:00Z,
2026-07-28T00:00:00Z)`. A closed one-second kline was counted in the target
interval only when its kline start timestamp fell inside that half-open range.

## Observed

- 10,092,865 Binance records were scanned.
- Stream counts were 9,257,161 `bookTicker`, 750,295 `aggTrade`, and 85,409
  `kline_1s` records.
- All 85,409 kline records were closed and all JSON records were valid.
- 85,408 unique closed kline starts fell inside the strict target day.
- 992 expected one-second starts were missing from the strict target day.
- There were zero duplicate starts and zero backward starts inside the target
  day.
- The six gap episodes had a largest missing span of 486 seconds between
  consecutive observed starts.
- One additional closed kline started at `2026-07-26T23:59:59Z`, immediately
  before the target day. This accounts for the difference between the file-wide
  total of 85,409 closed starts and the strict in-day count of 85,408.

## Consequence

Coverage measurements must state whether they count all closed kline records in
the file or only starts inside the requested UTC interval. The earlier sample
audit's 85,409 figure is the file-wide closed-kline total; this reproduction
provides the strict in-day count separately without rewriting the historical
evidence.
