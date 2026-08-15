# Evidence: 2026-07-27 Direct-GZIP Audit Reproduction

Status: Point-in-time local reproduction of the grouped-GZIP path
Reproduction date: 2026-08-14
Scope: Binance input for candidate group `2026-07-27`

## Method

The local July 27 ZIP contains the Binance member recorded in the remote
grouped-GZIP manifest. The compressed member was copied into a temporary
directory without changing the project or the remote manifest. Its size and
SHA-256 were checked against the manifest before running the schema-v2 archive
runner:

```text
input = binance_raw_events_2026-07-27.jsonl.gz
size_bytes = 153970117
sha256 = dec79c7df55575bf7a8d08b252def320ea3f66279b49631089d87b18a0ca6dbc
day_start = 2026-07-27T00:00:00Z
duration_seconds = 86400
audit_version = tradingbot-data-0.2.0-03abbb7
policy_version = data-quality-2026-08-14
```

The temporary manifest was a copy of the inspected Drive manifest. The run
used the direct `.jsonl.gz` input path and `binance_raw` role, then wrote an
isolated output and recorded its checksum. The remote Drive manifest was not
modified.

## Observed

- The direct-GZIP input identity matched the remote manifest exactly.
- The runner completed the July 27 Binance audit and verified its temporary
  output before marking the copied record `completed`.
- The temporary audit output checksum recorded by the copied manifest was
  `366cc67d4ef74abbdeda566768e98e6b056d4970a200d4a14ded70e16ca191f3`.
- The result had schema version `2`, input layout `direct_gzip_group`, and
  member `binance_raw_events_2026-07-27.jsonl.gz`.
- Receipt coverage was `2026-07-27T00:00:00.045186Z` through
  `2026-07-27T23:59:59.974235Z`.
- The first closed kline in the requested interval started at
  `2026-07-27T00:00:00.000Z`; the last started at
  `2026-07-27T23:59:58.000Z`.
- The result contained 10,092,865 scanned records, zero malformed JSON
  records, and 85,409 closed klines in total.
- The strict in-day result contained 85,408 closed klines, 992 missing starts,
  zero duplicate starts, zero backward starts, and 6 gap events. The largest
  missing gap was 486 seconds.
- Stream counts were 9,257,161 `btcusdt@bookTicker`, 750,295
  `btcusdt@aggTrade`, and 85,409 `btcusdt@kline_1s` records.

## Comparison

All measured summary values match the earlier July 27 legacy-ZIP audit in
`docs/evidence/2026-08-14-archive-audit-runner-reproduction.md` and the source
audit in `docs/evidence/2026-07-27-sample-data-audit.md`. This confirms that the
direct-GZIP reader and grouped schema-v2 runner preserve the known audit result
for a byte-identical Binance member.

## Limitation and Consequence

This is not yet a Drive-backed persistent smoke test: the remote manifest still
has group `2026-07-27` in `pending` status, and no output was saved to Drive.
The remaining remote step is to run the same pinned package against the Drive
path, verify the internal timestamp coverage there, and confirm the persistent
output/checksum before starting the multi-day batch.
