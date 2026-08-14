# Evidence: 2026-08-14 Binance Proxy Target Reinterpretation

Status: Point-in-time reproduction of the corrected target rule  
Audit date: 2026-08-14  
Scope: One Binance archive and the first clean five-minute proxy target rule

## Method

`scripts/build_binance_proxy_targets.py` was rerun against:

```text
archive = data/raw/archives/drive-download-20260810T091218Z-1-001.zip
window_start = 2026-07-27T00:00:00Z
window_end = 2026-07-28T00:00:00Z
```

The target window still begins at the decision time. It uses the completed
one-second close immediately before the window start and the completed
one-second close immediately before the five-minute end. The corrected rule
does not reject a target when the start boundary's recorder receipt arrives
after the decision time. Receipt times are retained, and the target becomes
available only after both boundary observations have been received.

The receipt-time cutoff remains enforced for model features. Neither target
boundary value is permitted to enter the decision-time feature row merely
because it is available later.

## Observed

- 288 five-minute windows were examined.
- 283 windows had both boundary observations and therefore valid proxy labels.
- Of those 283 valid targets, all 283 had a start boundary received after the
  exact decision time.
- 2 windows were missing a start boundary.
- 3 windows were missing an end boundary.
- The labels were 135 `UP` and 148 `DOWN`.
- The first window's start close was `65399.99000000`, received at
  `2026-07-27T00:00:00.073849Z`, after its decision time of
  `2026-07-27T00:00:00Z`; it was retained as a valid historical target
  boundary and was not treated as a decision-time feature.

## Interpretation

The earlier zero-validity result measured a strict rule that incorrectly
applied the feature availability cutoff to target construction. It remains a
valid historical measurement of that strict rule and is preserved in
`docs/evidence/2026-08-13-binance-proxy-target-audit.md`.

The corrected result supports offline proxy-label construction for 283 windows,
while preserving the separate rule that late observations cannot be used as
decision-time features.
