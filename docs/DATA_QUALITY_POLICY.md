# Data Quality Policy

Status: Accepted initial policy  
Last updated: 2026-08-15
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
16. For the first feature/proxy dataset view of this collection, exclude
    candidate group `2026-06-29` because it is source-incomplete and severely
    under-covered. Preserve its raw inputs and audit outputs; this exclusion
    applies only to the first downstream dataset view.
17. Do not exclude the other days solely because the aggregate audit reports
    gaps. Preserve their rows and apply feature-specific consecutive-kline and
    receipt-time validity rules at row construction time. A whole-day
    exclusion requires a separate accepted decision based on the resulting
    feature-quality report.
18. A uniquely sourced boundary from a verified cross-archive recovery report
    may repair a missing Binance proxy-target boundary only in a separate
    recovered target view. Keep the original target view unchanged, preserve
    the recovered boundary's interval and receipt provenance, and leave
    ambiguous or unrecoverable boundaries invalid.
19. Binance data may remain the active source for learning, BTC-direction
    signal development, and proxy experiments. Official Chainlink labels are
    deferred until Polymarket-faithful validation, where they are still
    required because they define the outcome that the market pays. Polymarket
    market data is not required for direction-only proxy experiments, but it is
    required when evaluating entry timing, executable prices, liquidity, and
    Trade versus No Trade. Keep these responsibilities behind separate data
    interfaces so changing the target or market-data source does not require
    rebuilding the prediction pipeline.
20. The expanded Binance research track must support separate 5-minute,
    15-minute, and 60-minute direction targets. For a horizon `H`, features use
    only information available at decision time and the label compares the
    verified Binance boundary immediately before the start with the boundary
    immediately before `start + H`. Do not mix horizons into one unlabeled
    result or infer that a longer horizon is easier before measuring it. Begin
    with non-overlapping windows at each horizon, use chronological
    train/validation/final-holdout periods, and report each horizon's sample
    count, class balance, probability metrics, and regime behavior separately.
    Select features, models, and horizons using training and validation data;
    keep the final holdout untouched until the experiment is frozen.
21. Supersede rule 20 as the active learning scope: build only the 15-minute
    Binance direction task for now. Keep the horizon parameter explicit in the
    dataset interface, but do not build or compare 5-minute and 60-minute tasks
    during this learning slice. Use non-overlapping 15-minute windows, with the
    label comparing the verified Binance boundary immediately before the start
    with the boundary immediately before `start + 15 minutes`. Preserve the
    completed five-minute baseline as historical engineering evidence. Revisit
    other horizons only after the learner is comfortable with the complete
    15-minute dataset-to-evaluation loop.
22. For the active beginner 15-minute slice, use historical Binance 1-minute
    klines and make the availability limitation explicit: historical REST
    klines provide interval timestamps and OHLCV values, but not the original
    client receipt time. Treat a completed interval as available under an
    `interval_complete_assumption`; do not describe this dataset as
    receipt-time verified. Preserve the interval timestamps and later validate
    the assumption against recorder data that contains `received_at_utc`.
23. For the active 15-minute regime-feature slice, obtain historical Binance
    data independently of the existing recorder archive. Provide at least 100
    completed daily candles before the target period as warm-up, aggregate the
    same historical 1-minute source into 1-hour, 4-hour, and daily candles, and
    use only the last completed candle at or before each decision time. Summarize
    the 100 daily candles into interpretable regime features rather than placing
    the raw 100-candle sequence directly into the first dataset. Keep all
    horizon-specific target rows and feature summaries chronologically ordered.
24. Supersede rule 23 for the first implementation scope: begin with the
    short-term 15-minute feature block consisting of `return_1m`, `return_5m`,
    `return_15m`, `return_30m`, `volatility_5m`, `volatility_15m`,
    `volume_ratio_5m`, `candle_body`, `high_low_range`, `distance_ma_15`,
    `ma_slope_15`, and `rsi_14`. All are computed from completed historical
    1-minute data before the decision time. Defer the 100-day, 1-hour, and
    4-hour regime block until this short-term dataset-to-evaluation loop is
    complete; this is a staged scope choice, not a claim that long-term regime
    features are unhelpful.
25. For the first 15-minute dataset implementation, use historical Binance
    1-minute klines as the raw source while making one prediction at each fixed
    UTC quarter-hour (`00`, `15`, `30`, `45`). Build non-overlapping targets
    for the following 15-minute window and derive the accepted 5-minute,
    15-minute, and 30-minute context features from that same 1-minute source.
    Prediction cadence and raw-data frequency are intentionally different.

## Initial Output Fields

The first feature inspector should expose:

- `return_1s`: the decimal return, or missing when invalid;
- `feature_valid`: whether the return passed the consecutive-kline rule;
- `quality_flag`: why the feature is valid or unavailable;
- `available_at_utc`: when the source record became observable.

The inspector's default output is the raw/audit view. The `--model-only` view
filters out rows whose required `return_1s` feature is invalid.
