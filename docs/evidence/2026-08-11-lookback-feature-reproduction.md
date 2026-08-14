# Evidence: 2026-07-27 Initial Lookback Feature Reproduction

Status: Point-in-time reproduction  
Audit date: 2026-08-11  
Scope: One Binance archive, one decision cutoff, and the initial 60-second lookback

## Method

`scripts/build_decision_snapshot.py` was run with:

```text
decision_time = 2026-07-27T00:00:04.000Z
lookback_seconds = 60
```

The script required all one-second inputs in the lookback to be complete,
received by the cutoff, and consecutive.

## Observed

- Three klines were eligible at the cutoff.
- The latest eligible one-second feature was valid.
- Fewer than the required 61 closes were available for a 60-interval return.
- `return_1m` was therefore missing with
  `return_1m_quality_flag=insufficient_eligible_history`.
- The snapshot was not usable for the initial feature set.

## Consequence

An individually valid short-horizon feature does not imply that a longer
lookback feature is available. Each lookback must satisfy its own completeness,
availability, and consecutiveness requirements.
