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

- One recorder archive is available locally under `data/raw/archives/`.
- Approximately 30 days of recorder data remain in Google Drive.
- Large raw archives and heavy computation should remain remote.
- The local laptop is for code, documentation, tests, small fixtures, and
  compact reports or model artifacts.
- Free Google Colab is a provisional candidate for the Phase 1 audit, not a
  permanent production environment.
- The raw archive must remain unchanged. Invalid observations remain available
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
- The initial manifest generator hashes raw ZIP archives in streaming chunks and
  creates safe `pending` records. The one-archive runner now owns status
  transitions and verified audit-output attachment.
- The one-archive runner and batch orchestrator now exist. They require an
  explicit archive-to-UTC-day coverage map and verify output checksums before
  marking a record `completed`.
- The workflow is now installable as `tradingbot-data`; the Colab execution
  contract is documented in `docs/COLAB_RUNBOOK.md`.

## Immediate Next Checkpoint

Make the remote archive work reproducible:

1. Create the checksum-bearing manifest for all remote archives.
2. Create and verify the archive-to-UTC-day coverage map.
3. Process one archive at a time with the audit runner.
4. Save each archive's audit result to persistent Google Drive storage.
5. Resume unfinished archives if a Colab runtime stops.
6. Run the multi-day data-readiness audit when the archives are accessible.

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
