# Project-Specific Instructor Handoff

Status: Adapter for the reusable instructor prompt  
Last verified: 2026-08-14

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
  rows out of 288 and all 13 local tests passed. The revision is not yet
  published to Colab; the remaining remote task is the 29-group feature run.
- The workflow is now installable as `tradingbot-data`; the Colab execution
  contract is documented in `docs/COLAB_RUNBOOK.md`.

## Immediate Next Checkpoint

Make the remote grouped-GZIP work reproducible:

1. Publish the tested local package revision `0.3.0` and install that exact
   revision in Colab; the currently pinned remote version is `0.2.0`.
2. Treat the inspected 30-record Drive manifest as the control record: it has
   89 raw members, one incomplete group, 10 ignored derived files, and all
   records initially `pending`.
3. July 27 has now passed the persistent Drive audit: its output exists and its
   checksum matches the manifest.
4. Apply the accepted policy: exclude June 29 from the first feature/proxy view
   while preserving raw/audit rows; retain other days for row-level validity.
5. Build the gap-aware Binance feature view remotely for the 29 eligible
   groups and measure valid rows.
6. Keep official label recovery separate from the Binance engineering track.

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
