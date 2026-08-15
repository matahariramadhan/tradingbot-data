# Project-Specific Instructor Handoff

Status: Adapter for the reusable instructor prompt  
Last verified: 2026-08-15

## Transfer Note — 2026-08-14

The student has chosen to continue with the previous instructor. The master
instructor review read the complete authoritative documentation, evidence,
implementation, and tests, and made no project-code changes during that review.

The receiving instructor must resume through `README.md`, then use
`docs/STATE.md` for project position and `docs/LEARNING_PROGRESS.md` for the
next teaching checkpoint. Do not restart mastered lessons merely because the
instructor changed. The master-instructor summary remains available in
`docs/MASTER_INSTRUCTOR_REPORT.md`; it is a handoff summary, not a replacement
for the subject-authoritative records.

Use this file together with [`INSTRUCTOR_PROMPT.md`](INSTRUCTOR_PROMPT.md) when
an AI instructor takes over this project or resumes after context compaction.
The prompt defines general teaching behavior; this file supplies project
context. Subject-specific facts remain authoritative in the linked documents.

## How to Resume

1. Read `README.md` first.
2. Follow the required reading sequence in `AGENTS.md` and `README.md`.
3. Read `INSTRUCTOR_PROMPT.md` for the reusable teaching protocol.
4. Read this adapter for the project-specific learner and status snapshot.
5. Read only the evidence and decision records relevant to the next task.

Do not use conversation memory instead of the authoritative project documents.
After compaction, continue from `docs/LEARNING_PROGRESS.md` and
`docs/STATE.md`; do not redo completed work merely because the conversation is
missing.

## Master-to-Mentor Handoff — 2026-08-15

The first Binance-proxy baseline has now been evaluated and is approximately
chance-level. The learner is intentionally returning to the lower-cost mentor
for the next execution and learning slice. Do not rerun the baseline, raw
audits, feature scans, recovery, join, or chronological split while their
persisted identities and checksums remain valid.

The next slice is not “try a more powerful model.” Freeze the observed six-day
evaluation result and use only the 6,586 training-period rows for diagnostic
EDA of the original directional-regime hypothesis. Build human-readable plots
that answer:

1. Does proxy `UP` frequency change across signed `return_1m` quantiles?
2. Does that relationship change between low- and high-`volatility_1m`
   regimes?
3. Does the latest `return_1s` appear to add information beyond the minute
   direction, or is it mostly noise near zero?

Show sample counts with every bin and avoid conclusions from tiny tail groups.
Use no evaluation-period rows while selecting bins, interactions, or candidate
features. If training-only EDA suggests one interpretable nonlinear pattern,
write one explicit hypothesis and validation plan before implementing a second
experiment. If it shows no credible pattern, report that conclusion and propose
the next hypothesis-driven Binance signal or data-coverage improvement. Do not
redirect the learner to Chainlink merely because this three-feature proxy view
is weak: Chainlink is deferred to later Polymarket-faithful validation under
`docs/DATA_QUALITY_POLICY.md` rule 19.

Do not introduce a tree ensemble, neural network, GPU, backtest, or trading
logic at this checkpoint. Ask only two or three interpretation questions, and
handle plotting mechanics for the learner.

## Project Context

The project studies machine-learning predictions for BTC-related Polymarket
five-minute Up/Down markets. The intended system eventually includes data
collection, raw storage, features, probability estimation, market-price/edge
comparison, strategy and risk, and execution. The current work is research and
education, not live trading.

The project is in Phase 1: problem definition, market mechanics, and data
foundations. Phase 1 is not complete. A verified Binance-proxy engineering
baseline now exists, but there is no official research dataset or official
model, backtest, paper-trading system, or live-trading system yet.

## Learner Context

The student wants to be an active learner. Use small batches of related
questions, normally two or three. Explain concepts in plain language, correct
misconceptions directly, and use examples that require reasoning. Do not spend
the student's time on trivial manual CSV writing, formatting, or repetitive
boilerplate; handle those mechanics when they are in scope.

The student currently understands the distinction between:

- decision-time inputs and the later official target;
- interval time and recorder receipt time;
- valid and invalid features across data gaps;
- net return and volatility;
- model probability and market ask price;
- prediction eligibility and supervised-training eligibility;
- Binance predictive data and the official Chainlink-based target.
- chronological training/evaluation separation and why future days must not
  enter training;
- the difference between a successful reproducible pipeline and a model whose
  chance-level evaluation does not demonstrate predictive signal.

## Current Project Snapshot

- One legacy recorder ZIP sample is available locally under
  `data/raw/archives/`.
- The Google Drive collection contains 30 candidate dates as direct GZIP
  inputs: 30 Binance raw files, 29 Polymarket raw files, 30 recorder logs, and
  10 derived CSV exports. Candidate 2026-06-29 lacks Polymarket raw data.
- Large raw inputs and heavy computation should remain remote.
- The local laptop is for code, documentation, tests, small fixtures, and
  compact reports or model artifacts.
- Free Google Colab is a provisional candidate for the Phase 1 audit, not a
  permanent production environment.
- Raw inputs must remain unchanged. Invalid observations remain available
  for audit, while explicit downstream model views may exclude them.
- Missing official Chainlink target data must not be replaced with Binance data;
  the row remains auditable but is not eligible for labeled training until the
  official target is recovered.
- A separate Binance-proxy dataset is now accepted for engineering validation,
  learning, and BTC-direction signal development, but it must carry
  `label_source` and remain separate from official research results.
- Chainlink is a later Polymarket-faithful label-validation requirement, not the
  current learning bottleneck. Polymarket data enters when the project studies
  market-window context, executable prices, liquidity, and Trade versus No
  Trade.
- The first proxy task is a clean five-minute future-window experiment where
  decision time equals window start. The later official task may make its
  decision inside a fixed market window; these evaluations must stay separate.
- The proxy target builder now allows late boundary receipts for offline label
  construction while keeping the receipt cutoff for decision-time features.
- Manifest schema v2 groups the authoritative direct-GZIP files by candidate
  date, hashes every present raw member, preserves missing roles, and records
  derived CSV exports as ignored. Legacy ZIP input remains supported.
- The one-group runner and batch orchestrator require an explicit
  group-to-UTC-day coverage map and verify output checksums before marking the
  configured Binance audit scope `completed`. Group input completeness remains
  separate from that processing status.
- The July 27 direct-GZIP runner path has been reproduced locally against a
  byte-identical Binance member and matches the known ZIP audit. The remote
  Drive-backed audit has now also completed: its output exists and its checksum
  matches the manifest. The full 30-group receipt-date coverage preflight has
  also passed with zero review groups. The full batch then completed with zero
  reported failures, and a separate check verified all 30 outputs and
  checksums. The aggregate report found 89,677 missing starts across 55 gaps,
  with a largest gap of 645 seconds. A local package revision `0.3.0` now
  builds the gap-aware feature view; its July 27 canary produced 284 usable
  rows out of 288 and all 13 local tests passed. The published revision then
  produced the 29-day feature view remotely: 8,316 usable rows out of 8,352,
  with 36 invalid rows preserved for review. Those flags were classified as
  29 `received_after_cutoff` opening-boundary rows and 7 `missing_kline`
  intraday rows. The separate proxy-target batch produced 8,299 valid targets
  out of 8,352; timestamp review found 29 final `23:55:00` windows and 11
  non-final missing-end windows, while the 13 missing-start rows are
  intraday. The cross-archive boundary-recovery scan completed all 30 source
  groups and found 28 of the 29 final boundaries; `2026-07-28` remains
  unrecoverable from the scanned collection. Those 28 observations have now
  been applied in the separate recovered target view.
- The Colab notebook is now a 41-cell Phase 1 runbook pinned to package
  `63cbd647953d203abab23ccd5d27c9a87aec3d4a` (`0.8.1`). It verifies existing
  control artifacts, reuses stage-compatible feature outputs, applies boundary
  recovery, joins and reviews the proxy model view, validates the chronological
  split, runs the first proxy baseline, and renders three human checkpoints for
  the data, split, and evaluation. Its bootstrap verifies the installed
  distribution, module, and visualization environment before derived work runs.
- The workflow is now installable as `tradingbot-data`; the Colab execution
  contract is documented in `docs/COLAB_RUNBOOK.md`.

## Immediate Next Checkpoint

Start a training-period-only proxy EDA report. Reload the training-day list and
per-day hashes from `proxy-split-v1.json`, read only those model-view CSVs, and
persist the report and plots under
`/content/drive/MyDrive/tradingbot-data-audit/proxy-training-eda-v1/`. The first
deliverable is evidence about directional return versus volatility regimes,
not another fitted model.

The completed baseline was correct on 854 of 1,706 later evaluation rows,
versus 845 for the training-majority baseline; ROC-AUC was 0.487225 and
probability losses were essentially coin-flip level. The six evaluation days
have now been observed and must not guide exploratory feature selection while
still being described as untouched.

Do not begin model training or live trading before the Phase 1 conditions in
`docs/STATE.md` are satisfied.

## Canonical Documents

- [`README.md`](../README.md) — onboarding gate
- [`AGENTS.md`](../AGENTS.md) — operating rules and document authority
- [`instruction.md`](../instruction.md) — immutable project charter
- [`LEARNING_CONTRACT.md`](LEARNING_CONTRACT.md) — project learning approach
- [`STATE.md`](STATE.md) — current project status and next work
- [`LEARNING_PROGRESS.md`](LEARNING_PROGRESS.md) — durable lesson checkpoint
- [`MASTER_INSTRUCTOR_REPORT.md`](MASTER_INSTRUCTOR_REPORT.md) — concise learner handoff summary
- [`COLAB_RUNBOOK.md`](COLAB_RUNBOOK.md) — remote package execution instructions
- [`REVIEW_QUESTIONS.md`](REVIEW_QUESTIONS.md) — refresher and retake questions
- [`DECISION_LOG.md`](DECISION_LOG.md) — accepted durable decisions
- [`DATA_QUALITY_POLICY.md`](DATA_QUALITY_POLICY.md) — accepted data rules
- [`evidence/`](evidence/) — exact measurements and reproductions
