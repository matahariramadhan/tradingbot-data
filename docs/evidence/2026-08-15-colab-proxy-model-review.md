# Colab Proxy Model-View Review

Date: 2026-08-15

The pinned Colab run executed the read-only `proxy-review` step against the
recovered Binance proxy target join.

## Remote scope and outputs

- Review report: `/content/drive/MyDrive/tradingbot-data-audit/proxy-model-review-v1.json`
- Excluded-row review: `/content/drive/MyDrive/tradingbot-data-audit/proxy-model-excluded-v1.csv`
- Eligible days: `29`
- Audit rows: `8,352`
- Model-ready rows: `8,292`
- Excluded rows: `60`
- Label counts: `DOWN=4,139`, `UP=4,153`
- Chronological model keys: `true`

The review also reported finite numeric values for all three initial model
fields:

| Field | Count | Minimum | Maximum |
| --- | ---: | ---: | ---: |
| `return_1s` | 8,292 | -0.000510818 | 0.0005045565 |
| `return_1m` | 8,292 | -0.000510818 | 0.0005045565 |
| `volatility_1m` | 8,292 | 0.0000000656 | 0.0005920084 |

## Consequence

The structural quality review passed: keys, labels, provenance, chronology,
numeric parsing, and exclusion accounting were valid. However, inspection of
the feature builder at the reviewed package revision found that it assigns
`return_1m = returns[-1]`. That is the latest one-second return in the
lookback, which duplicates `return_1s`; it is not the intended net return over
the 60-second lookback.

The accepted feature policy defines `return_1m` as the net change from the
first to the last close in the complete 60-second lookback. Therefore this
review is retained as evidence of the structural gate, but the proxy model
view must not be used for training or evaluation until the feature computation
is corrected and the affected remote derived views are regenerated and
reviewed.
