# Colab Human Data Overview

Date: 2026-08-15 UTC  
Status: User-reported remote rendering

## Scope

The first human visualization checkpoint in `tradingbot_data.ipynb` reloaded
the verified proxy model-review report and per-day model CSVs from Google
Drive. It rendered without rerunning raw scans or model training.

## Observed

- The daily stacked bars covered the 29 eligible UTC days from 2026-06-30
  through 2026-07-28. Model-ready rows dominated every day, with excluded rows
  retained as small red segments.
- The model-ready proxy-label counts were 4,139 `DOWN` and 4,153 `UP`.
- The latest one-second-return histogram was extremely concentrated around
  zero with sparse tails in both directions.
- The net 60-second-return histogram was centered near zero, broader than the
  latest one-second return, and contained rare tail observations.
- The 60-second-volatility histogram was nonnegative and strongly
  right-skewed: most windows were relatively calm and a small number were much
  more volatile.

## Interpretation Limit

These combined-label histograms describe model-input coverage and marginal
feature shapes. They do not show whether `UP` and `DOWN` outcomes separate on
those features and therefore do not establish predictive signal. The raw
decimal axes and full-range tails also compress the central distributions;
future training-only EDA should use human-scale units, central-range views, and
explicit label/regime comparisons.
