# Post-Fix Colab Proxy Model-View Review

Date: 2026-08-15

The pinned package `0.6.1` regenerated the affected feature view, rebuilt the
proxy join, and reran the model-view review.

## Remote scope and outputs

- Review report: `/content/drive/MyDrive/tradingbot-data-audit/proxy-model-review-v1.json`
- Excluded-row review: `/content/drive/MyDrive/tradingbot-data-audit/proxy-model-excluded-v1.csv`
- Eligible days: `29`
- Audit rows: `8,352`
- Model-ready rows: `8,292`
- Excluded rows: `60`
- Label counts: `DOWN=4,139`, `UP=4,153`
- Chronological model keys: `true`

Corrected feature ranges:

| Field | Count | Minimum | Maximum |
| --- | ---: | ---: | ---: |
| `return_1s` | 8,292 | -0.000510818 | 0.0005045565 |
| `return_1m` | 8,292 | -0.0029595776 | 0.0071434727 |
| `volatility_1m` | 8,292 | 0.0000000656 | 0.0005920084 |

The corrected `return_1m` range differs from `return_1s`, confirming that the
net 60-second lookback calculation is now being used. Row counts, exclusions,
label counts, and chronological ordering remained unchanged, as expected: the
fix changed feature values, not the source rows, target policy, or validity
requirements.

This completes the structural and feature-semantic gate for the Binance proxy
engineering view. It does not establish final Polymarket research validity;
the official Chainlink-based target remains a separate unresolved requirement.
