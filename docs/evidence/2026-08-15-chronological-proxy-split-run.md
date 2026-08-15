# Chronological Proxy Split Run

Date: 2026-08-15 UTC

## Scope

The remote Colab run executed the pinned chronological proxy split against the
29 eligible model-view days. The split used the accepted first 23 days for
training and final 6 days for evaluation. It did not randomize rows or copy
the model CSVs.

## Observed result

Drive artifact: `/content/drive/MyDrive/tradingbot-data-audit/proxy-split-v1.json`

- model rows: 8,292
- training rows: 6,586
- evaluation rows: 1,706
- train/evaluation overlap keys: 0
- training days: 2026-06-30 through 2026-07-22
- evaluation days: 2026-07-23 through 2026-07-28

The row totals sum to the model-view total, and the output printed zero key
overlap. This is evidence that the accepted chronological partition was
materialized successfully; it is not evidence of model performance.
