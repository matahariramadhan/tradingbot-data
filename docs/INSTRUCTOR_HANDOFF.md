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

## Project Context

The project studies machine-learning predictions for BTC-related Polymarket
five-minute Up/Down markets. The intended system eventually includes data
collection, raw storage, features, probability estimation, market-price/edge
comparison, strategy and risk, and execution. The current work is research and
education, not live trading.

The project is in Phase 1: problem definition, market mechanics, and data
foundations. Phase 1 is not complete. There is no research dataset, trained
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
  but it must carry `label_source` and remain separate from official research
  results.
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
  unrecoverable from the scanned collection. The next checkpoint is applying the 28 recovered
  observations explicitly before any target/feature join.
- The Colab notebook is now a 29-cell Phase 1 runbook being repinned to package
  `6c9c9bfaba3cf2ed9cab4a3590ffa4bb3447f200` (`0.5.1`). It verifies existing
  control artifacts, separates feature and proxy generation, applies boundary
  recovery into a separate target view, and adds a resumable model-ready join.
  Its boundary scan checkpoints after each source archive, so interruption does
  not restart completed archive scans. Local structural and resumability tests
  passed; the join step has not yet run remotely.
- The workflow is now installable as `tradingbot-data`; the Colab execution
  contract is documented in `docs/COLAB_RUNBOOK.md`.

## Immediate Next Checkpoint

The fix is pushed in commit
`41fdff5619d4c00389628eb526f9f66ac19f3650` (`tradingbot-data` `0.4.1`). Run
the repinned notebook and rerun the failed recovery cell. That recovery now
completed: 28 boundaries were applied, zero rows require review, and the
separate view contains 8,327 valid and 25 invalid rows. The next checkpoint is
to run the separate model-ready Binance-feature/proxy-target join. Preserve the
unresolved July 28 boundary and all intraday invalid rows; keep the proxy
`label_source` separate from official label recovery.

The published next-slice implementation matches by canonicalized
`window_start_utc`, stops on
duplicate keys, preserves invalid rows in an audit view, and exposes only the
three initial feature columns. It is package `0.5.1` at commit
`6c9c9bfaba3cf2ed9cab4a3590ffa4bb3447f200`, has passed 19 local tests, and the
join is ready for its remote rerun.

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
