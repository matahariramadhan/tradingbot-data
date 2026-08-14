# Evidence: 2026-08-11 One-Minute Volatility Reproduction

Status: Point-in-time reproduction  
Audit date: 2026-08-11  
Scope: One Binance archive, two decision cutoffs, and the initial one-minute feature set

## Method

`scripts/build_decision_snapshot.py` was run against:

```text
archive = data/raw/archives/drive-download-20260810T091218Z-1-001.zip
lookback_seconds = 60
```

The snapshot builder required each input kline to be complete and received by
the decision cutoff. It required 61 consecutive eligible closes for the
60-interval lookback. It computed `volatility_1m` as the population standard
deviation of the 60 consecutive one-second returns.

## Observed: early cutoff

At `2026-07-27T00:00:04.000Z`:

- Three klines were eligible.
- `return_1s` for the latest eligible kline was valid.
- `return_1m` and `volatility_1m` were both missing with
  `insufficient_eligible_history`.
- `snapshot_usable` was `false`.

## Observed: later cutoff

At `2026-07-27T00:02:00.000Z`:

- 120 klines were eligible.
- `return_1m = -0.0004031567` and was valid.
- `volatility_1m = 0.0000529796` and was valid.
- `snapshot_usable` was `true`.

## Consequence

The same decision-time dependency rules apply to both direction and movement
features. A valid one-second return is not enough for a one-minute snapshot;
the full lookback must be available, consecutive, and valid. The one-minute
return describes net movement, while the one-minute volatility describes the
typical size of the intermediate one-second movements.
