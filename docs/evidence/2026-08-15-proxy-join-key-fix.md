# Proxy-Join Timestamp-Key Fix

Date: 2026-08-15

## Observed failure

The first remote proxy join produced 576 audit rows for
`2026-06-30` instead of the expected 288 and failed the notebook shape check.
The feature and target tables each contained 288 semantically matching
windows, but their timestamp text used different fractional precision, such
as:

```text
2026-06-30T00:00:00.000000Z
2026-06-30T00:00:00.000Z
```

The join compared raw strings and therefore treated equivalent UTC instants as
different keys.

## Correction

Package `0.5.1` canonicalizes every `window_start_utc` to UTC with millisecond
precision before duplicate detection and joining. A regression test covers
the six-decimal-versus-three-decimal case. Duplicate canonical keys still stop
the join for review.

The fix is committed at
`6c9c9bfaba3cf2ed9cab4a3590ffa4bb3447f200` and the notebook is being repinned
to it. The corrected join has not yet run remotely.
