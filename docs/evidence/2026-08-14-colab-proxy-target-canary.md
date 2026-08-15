# Colab Binance Proxy-Target Canary

Status: user-reported remote reproduction

Run date: 2026-08-14

## Scope

Package version `0.3.0` built the separate Binance proxy-target table for the
July 27 direct-GZIP archive. The target task uses one five-minute future
window, with the completed one-second close immediately before the window
start and immediately before the window end.

## Result

- Records scanned: `10,092,865`
- Malformed JSON: `0`
- Closed klines: `85,409`
- Duplicate closed-kline starts: `0`
- Windows requested: `288`
- Valid targets: `283`
- Missing start boundaries: `2`
- Missing end boundaries: `3`
- Duplicate boundaries: `0`
- Valid targets with a late start receipt: `283`

## Interpretation

The remote result matches the corrected local proxy reproduction. The
`late_start` count does not invalidate these historical labels: the target is
constructed offline from the future window boundaries. The receipt-time
cutoff applies to decision-time features, not to the later target-construction
inputs. The target table identifies this track with `label_source=binance_proxy`
and must remain separate from the official Chainlink-labeled research table.

The 5 missing-boundary windows remain invalid and must not be filled with
invented prices or silently removed from the audit view.
