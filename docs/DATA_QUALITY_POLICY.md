# Data Quality Policy

Status: Accepted initial policy  
Last updated: 2026-08-14
Scope: First BTC feature pipeline

## Rules

1. Preserve raw observations. Do not silently modify, interpolate, or invent
   missing market data.
2. A `return_1s` feature is valid only when the current closed one-second
   kline starts exactly 1,000 milliseconds after the previous closed kline.
3. If there is no previous kline, or the previous kline is non-consecutive,
   `return_1s` must be missing and the row must carry a quality flag.
4. Preserve the recorder receipt time. A feature is usable for a decision only
   when its receipt time is at or before the decision time.
5. Keep observed data defects separate from explanations of their cause. A
   suspected interruption is not evidence of an interruption until verified.
6. Retain invalid rows in the raw/audit view with their quality flags. Exclude
   them only from the first model-dataset view; never delete them from the
   evidence used to diagnose collection quality.
7. Validate features independently according to their own dependencies. A
   model row is eligible only when every feature required by that model is
   valid and available at the decision cutoff.
8. The initial aggregated-return lookback is 60 consecutive one-second
   intervals. If any required interval is missing, late, or invalid,
   `return_1m` must be missing and flagged.
9. The initial `volatility_1m` is the population standard deviation of those
   same 60 valid one-second returns. If the lookback is invalid,
   `volatility_1m` must also be missing and flagged.
10. The supervised target must use the official Chainlink BTC/USD settlement
    result. If Chainlink data needed to establish that result is missing, do
    not substitute Binance data; retain the row for audit but exclude it from
    labeled training and evaluation until the official target is recovered.
11. A separate engineering/proxy dataset may use a Binance-derived target
    before official labels are available, but every target must identify its
    `label_source` and label definition. Proxy data must remain separate from
    the official research dataset and must not support final Polymarket claims.
12. The first Binance proxy experiment uses a clean future-window task: the
    decision time equals the proxy window start, and the target window ends five
    minutes later. Features use only information available by the start; the
    proxy label compares the Binance boundary values and uses `UP` when the end
    is greater than or equal to the beginning, otherwise `DOWN`.
13. The later Polymarket-faithful task keeps the market's fixed start and end
    separate from the decision time, which may occur inside the market window.
    Its official label must compare the Chainlink boundary values. Results from
    the two tasks must not be presented as evaluations of the same prediction
    problem.
14. For the first proxy window beginning at `s`, use the close of the completed
   one-second interval immediately before `s` as `proxy_start_price`, and the
   close of the completed one-second interval immediately before `s+5 minutes`
   as `proxy_end_price`. These boundary observations are target-construction
   inputs, not decision-time features. Their receipt times may be after `s`
   because the target is constructed offline after the window; preserve those
   receipt times and make the target available only after both boundaries have
   been observed. If either boundary value is unavailable, the proxy label is
   missing and must not be invented.
15. The receipt-time cutoff applies to model features: a feature is eligible
   for a decision at `t` only when its source observation was available by
   `t`. It does not invalidate a historical target merely because a boundary
   value used only to construct that target arrived after `t`. A late target
   boundary must never be included in the feature row for that decision.

## Initial Output Fields

The first feature inspector should expose:

- `return_1s`: the decimal return, or missing when invalid;
- `feature_valid`: whether the return passed the consecutive-kline rule;
- `quality_flag`: why the feature is valid or unavailable;
- `available_at_utc`: when the source record became observable.

The inspector's default output is the raw/audit view. The `--model-only` view
filters out rows whose required `return_1s` feature is invalid.
