# Evidence: 2026-08-13 Strict Binance Proxy Target Audit

Status: Point-in-time reproduction  
Audit date: 2026-08-13  
Scope: One Binance archive and the first clean five-minute proxy target rule

## Method

`scripts/build_binance_proxy_targets.py` was run against:

```text
archive = data/raw/archives/drive-download-20260810T091218Z-1-001.zip
window_start = 2026-07-27T00:00:00Z
window_end = 2026-07-28T00:00:00Z
```

The strict proxy rule set decision time equal to each five-minute window start.
It used the completed one-second close immediately before the window start and
the completed one-second close immediately before the five-minute end. The
start observation had to be received by the decision time. The end observation
was used only offline to construct the target.

## Observed

- 288 five-minute windows were examined.
- 283 windows had a start boundary, but its receipt was after the exact
  decision time and were flagged `late_start_boundary`.
- 2 windows were missing a start boundary.
- 3 windows were missing an end boundary.
- 0 windows were valid proxy targets under the strict rule.
- The archive scan contained 10,092,865 records, 85,409 closed one-second
  klines, and 0 malformed JSON records.

The first window illustrates the timing issue: its start close was
`65399.99000000` from the interval beginning at
`2026-07-26T23:59:59.000Z`, but the recorder receipt was
`2026-07-27T00:00:00.073849Z`, after the `2026-07-27T00:00:00Z` decision.

## Consequence

The strict clean proxy definition is leakage-safe, but this recorder cannot
support decisions at the exact five-minute boundary for this sample. This does
not justify using late data. It creates a design choice: retain the strict
experiment as an explicit zero-validity result, or define a separate delayed-
decision proxy with its own decision-time contract and label metadata.
