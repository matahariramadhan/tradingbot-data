# Master Instructor Learning Report

Status: Handoff summary, not a new authority source  
Report date: 2026-08-14  
Project: BTC/Polymarket five-minute Up/Down research

This report summarizes the learner's progress for a master instructor. The
authoritative detailed records remain [`LEARNING_PROGRESS.md`](LEARNING_PROGRESS.md),
the review bank, the learning contract, the state file, and the decision log.

## Learner Profile

The learner is active and wants to reason about the system rather than copy
boilerplate. Teach from the whole system downward:

1. show the current end-to-end slice and why it matters;
2. identify inputs, outputs, assumptions, and the gate it supports;
3. ask only two or three meaningful questions;
4. implement trivial mechanics for the learner;
5. revisit a concept only for a new decision, a mistake, uncertainty, or
   requested review.

The learner strongly prefers plain-language explanations, concrete timelines,
small question batches, and durable lesson records written in coherent batches.
Do not spend lesson time on manual CSV transcription or obvious formatting.

## Current Understanding

The learner can explain and apply:

- the prediction unit: one BTC five-minute Up/Down market at a specified
  decision time;
- the difference between model probability, market ask price, raw edge, and
  realized `UP`/`DOWN` outcome;
- taker behavior versus passive bid-side orders;
- decimal returns, percentage representation, net direction, and volatility;
- the difference between a kline's measurement interval and its recorder
  receipt/availability time;
- data gaps, consecutive-kline requirements, invalid-row preservation, and
  feature-specific validity;
- decision-time feature eligibility and the initial 60-second lookback;
- standard deviation as typical distance from the mean and its distinction
  from directional return;
- live prediction eligibility versus later supervised-training eligibility;
- Binance as predictive data and Chainlink as the official settlement source;
- the separation between a Binance engineering proxy and the official
  Polymarket research target;
- archive checksums, audit/code versions, policy versions, resumable archive
  units, verified completion, and manifest/output consistency.

The review bank currently records RQ-001 through RQ-049 as mastered or
mastered-after-correction.

## Important Corrections Achieved

1. A complete kline is not automatically usable at decision time. Its receipt
   must also be at or before the decision cutoff.

2. A negative recent return does not prove that the future Polymarket label is
   `DOWN`; it describes past movement, not the future settlement outcome.

3. Equal start and end prices imply zero net return, not zero volatility.

4. The initial strict proxy audit incorrectly applied the feature receipt cutoff
   to target construction. A target-boundary value received after decision time
   may still be used later to build the historical label, provided it is never
   included in the decision-time feature row.

5. The strict proxy result of zero valid rows was therefore a valid measurement
   of the old strict rule, not proof that the historical target boundaries were
   unusable. The corrected local result is 283 valid proxy targets out of 288
   windows, with 5 windows missing a boundary.

## Accepted Project Decisions

The learner accepted these durable design choices:

- use a separate Binance proxy for engineering validation and reserve
  Chainlink-based labels for final research claims;
- start with a clean five-minute future-window proxy where decision time equals
  window start;
- use the completed one-second closes immediately before the proxy start and
  end boundaries;
- apply receipt cutoffs to features, not to offline target construction;
- use one complete archive as the resumable audit unit;
- mark an archive `completed` only after output and metadata are saved and
  verified;
- never trust status without checking the corresponding output;
- require an explicit UTC coverage start instead of inferring the recording day
  from an upload filename.

## Implementation Completed

The project now contains:

- streaming Binance feature inspection and as-of snapshot builders;
- gap-aware full-day Binance audits;
- proxy-target construction with receipt provenance;
- checksum-bearing archive manifest creation;
- one-archive audit execution with safe status transitions;
- multi-archive batch orchestration with explicit coverage-map validation;
- an installable `tradingbot-data` package and Colab execution runbook;
- atomic writes, output checksums, stale-run recovery, and focused unit tests.

The local end-to-end reproduction completed one archive, verified its output,
and safely skipped it on a subsequent run. Exact measurements are in the
2026-08-14 archive-runner evidence report.

The package was installed and its CLI was verified outside the repository. Git
origin is configured and the reviewed project checkpoint is committed locally;
it has not been pushed as part of this workspace session. Raw archives and audit
outputs remain correctly outside the code package in Google Drive.

## Current Phase Status

Phase 1 is not complete. The local engineering workflow is functional, but the
research readiness gate still requires:

- the approximately 30 remote archive files to be manifested and audited;
- a verified archive-to-UTC-day coverage map;
- multi-day coverage and integrity results;
- recorder source-code review or an intentional replacement;
- recovery and verification of official Chainlink values and Polymarket
  outcomes;
- the synchronized, documented research dataset and Phase 1 visualizations.

Model training, backtesting, paper trading, and live trading have not started
and should remain deferred until the data-readiness gate passes.

## Recommended Next Lesson

Run the remote smoke test: clone a pinned package revision in Colab, install
`tradingbot-data`, mount Google Drive, process one archive, and verify that the
manifest and audit output persist in Drive. Then run the full multi-day audit
and inspect the readiness report before discussing models.

## Resume Instructions

After context compaction, read:

1. `README.md` and `AGENTS.md`;
2. immutable `instruction.md`;
3. `docs/LEARNING_CONTRACT.md`;
4. `docs/STATE.md`;
5. this report, then the specific evidence and review records for the next
   checkpoint.

Do not restart the completed lessons unless the learner requests a refresher
or demonstrates uncertainty.
