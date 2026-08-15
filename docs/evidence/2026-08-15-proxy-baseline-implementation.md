# Proxy Baseline Training Implementation

Date: 2026-08-15 UTC

## Scope

Package commit `c02f801c45f43853c7aecd9e7a627da63ffa7325` (`0.8.0`) adds the
`proxy-baseline` command and the Colab runbook adds the corresponding training
cell. This implementation follows the verified proxy split and is not an
official Polymarket research model.

## Contract

- The model is a standardized logistic regression.
- `StandardScaler` and the classifier are fit on training rows only.
- Model inputs are `return_1s`, `return_1m`, and `volatility_1m`.
- Labels are `UP`/`DOWN` from `label_source=binance_proxy`.
- Evaluation runs once on the later evaluation days.
- Drive receives a joblib model, evaluation prediction CSV, and a JSON report
  containing metrics, source hashes, model parameters, and output hashes.
- A rerun skips only when the completed report and both outputs still match the
  current split report and their recorded checksums.
