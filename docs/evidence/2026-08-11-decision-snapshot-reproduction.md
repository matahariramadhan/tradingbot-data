# Evidence: 2026-07-27 Decision Snapshot Reproduction

Status: Point-in-time reproduction  
Audit date: 2026-08-11  
Scope: One Binance archive and one decision cutoff

## Method

`scripts/build_decision_snapshot.py` scanned the compressed Binance member and
selected only closed klines whose interval end and recorder receipt time were
both at or before the decision cutoff:

```text
decision_time = 2026-07-27T00:00:04.000Z
```

## Observed

- Six closed klines had started by the decision cutoff.
- Five of those intervals had completed by the cutoff.
- Three had been received by the cutoff.
- Three were eligible under both conditions.
- The latest eligible interval started at
  `2026-07-27T00:00:01.000Z` and ended at
  `2026-07-27T00:00:01.999Z`.
- The next interval, starting at `00:00:02.000Z`, was not eligible because its
  receipt time was `00:00:04.402075Z`.
- The latest eligible `return_1s` was valid because its previous eligible
  kline was consecutive.

## Consequence

At a decision cutoff, the newest interval by market time is not necessarily
the newest usable observation. Both interval completion and receipt time must
be enforced before constructing a feature row.
