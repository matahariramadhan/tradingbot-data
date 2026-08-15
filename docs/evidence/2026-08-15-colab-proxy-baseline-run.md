# Colab Proxy Baseline Run

Date: 2026-08-15 UTC  
Status: User-reported verified remote output

## Scope

The pinned notebook loaded the persisted proxy-baseline report, model artifact,
and evaluation predictions from
`/content/drive/MyDrive/tradingbot-data-audit/proxy-baseline-v1/`. The runner
verified the existing artifacts against the current split and their recorded
checksums, then skipped retraining as designed.

The model is the standardized logistic regression using `return_1s`,
`return_1m`, and `volatility_1m`. It was trained on 6,586 earlier rows and
evaluated on 1,706 later rows using Binance-proxy labels.

## Observed Evaluation Metrics

- Accuracy: `0.5005861664712778`.
- Balanced accuracy: `0.5035441106735665`.
- ROC-AUC: `0.48722484519857884`.
- Log loss: `0.6931774311684306`.
- Brier score: `0.2500155499379533`.
- Confusion matrix, with true labels as rows and predicted labels as columns
  in `DOWN`, `UP` order: `[[162, 699], [153, 692]]`.

The training-majority baseline predicted `UP` for every evaluation row and
reported:

- Accuracy: `0.49531066822977726`.
- Balanced accuracy: `0.5`.
- ROC-AUC: `0.5`.
- Log loss: `0.6932002764170382`.
- Brier score: `0.2500265477269916`.
- Confusion matrix: `[[0, 861], [0, 845]]`.

## Derived Comparison

The logistic regression made 854 correct predictions, compared with 845 for
the training-majority baseline: nine additional correct rows, or approximately
0.53 percentage points of accuracy. It correctly identified 162 of 861 `DOWN`
rows and 692 of 845 `UP` rows, so its average class recall remained close to
chance despite predicting some `DOWN` cases.

## Inference and Limit

The result validates the training, persistence, and evaluation pipeline, but it
does not provide meaningful evidence that these three features predict the
proxy target. ROC-AUC is below random ranking and both probability-loss metrics
are effectively at the coin-flip reference. No uncertainty interval or
day-level stability analysis was included, so this record does not make a
formal statistical-significance claim. It is not an official Polymarket model
or evidence of trading profitability.
