# Evidence: 2026-07-27 Drive-Backed Direct-GZIP Audit

Status: User-reported Colab reproduction
Reproduction date: 2026-08-14
Scope: Persistent Binance audit for candidate group `2026-07-27`

## Method

The pinned `tradingbot-data` `0.2.0` package at revision
`03abbb745cc7919087b2e56607bb6bdf4d582a23` was run in Colab against the
mounted Google Drive input:

```text
input = /content/drive/MyDrive/RecorderBackup/binance-polymarket-recorder/binance_raw_events_2026-07-27.jsonl.gz
manifest = /content/drive/MyDrive/tradingbot-data-audit/manifest-v2-03abbb7.json
day_start = 2026-07-27T00:00:00Z
duration_seconds = 86400
```

The result was written to persistent Drive storage and the manifest-controlled
completion check was run afterward.

## Observed

- Manifest status: `completed`.
- Persistent audit output exists: `True`.
- Recorded output checksum matches the actual output: `True`.
- Receipt coverage: `2026-07-27T00:00:00.045186Z` through
  `2026-07-27T23:59:59.974235Z`.
- Scanned records: 10,092,865; malformed JSON records: 0.
- Stream counts: 750,295 `btcusdt@aggTrade`, 9,257,161
  `btcusdt@bookTicker`, and 85,409 `btcusdt@kline_1s`.
- Closed klines: 85,409 total and 85,408 inside the requested UTC day.
- Expected in-day starts: 86,400; missing starts: 992.
- Duplicate starts: 0; backward starts: 0.
- Gap events: 6; largest missing gap: 486 seconds.
- First in-day closed start: `2026-07-27T00:00:00.000Z`.
- Last in-day closed start: `2026-07-27T23:59:58.000Z`.

## Consequence

The first persistent Drive-backed grouped-GZIP audit passed. July 27 is now
completed for the configured Binance day-coverage scope. This does not make the
group complete for later research readiness: source-role completeness remains
separate, and the wider collection still needs an explicit UTC coverage map
and multi-day audit.
