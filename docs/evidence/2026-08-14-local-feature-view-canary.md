# Local Feature-View Canary

Status: completed local engineering check

Run date: 2026-08-14

## Scope

The new local feature-view builder at
`scripts/build_binance_feature_view.py` was run against the locally available
July 27 legacy ZIP sample. This is a canary of the feature construction logic,
not the full multi-day research-dataset run.

The working-tree package revision was version `0.3.0`. The builder creates one
row per five-minute decision window and applies the decision-time receipt
cutoff. It selects the latest completed kline that was actually available by
the cutoff, then requires the consecutive one-second history needed for the
60-second return and volatility features.

## Measured result

- Archive records scanned: `10,092,865`
- Malformed JSON records: `0`
- Closed kline records: `85,409`
- Duplicate closed-kline starts: `0`
- Five-minute windows requested: `288`
- Fully usable feature rows: `284`
- Valid `return_1s` rows: `287`
- Valid `return_1m` rows: `284`
- Valid `volatility_1m` rows: `284`
- Quality flags: `284` `valid_all_initial_features`, `3` `missing_kline`, and
  `1` `received_after_cutoff`

## Interpretation

The canary confirms that the builder does not blindly use the newest market-
time interval. A kline can be complete in market time but unavailable at the
decision cutoff, so the feature view may use the latest earlier observation
that satisfies both completion and receipt-time rules. The longer one-minute
features remain invalid unless their full consecutive lookback is eligible.

The local test suite passed all 13 tests, including missing-lookback,
decision-cutoff, and late-latest-kline cases.

## Limitation

This result was produced locally and has not yet been published or installed
in Colab. The full feature-view generation for the 29 eligible remote groups,
with June 29 excluded from the first derived view, remains a remote
storage/compute task.
