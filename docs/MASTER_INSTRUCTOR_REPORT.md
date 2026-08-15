# Master Instructor Learning Report

Status: Handoff summary, not a new authority source  
Report date: 2026-08-15
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
- the need for chronological time-series evaluation: earlier days train the
  model, later days evaluate it, and train/evaluation keys must not overlap;
- the current verified split totals: 6,586 training rows and 1,706 later
  evaluation rows from 8,292 model-ready rows;
- why this small three-feature baseline should run on CPU rather than a GPU;
- per-input checksums, audit/code versions, policy versions, resumable capture
  groups, verified completion, and manifest/output consistency.

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
- use one logical candidate-date raw-source group as the resumable audit unit;
- identify each present source member independently and preserve missing roles;
- keep filename dates separate from verified UTC coverage;
- mark a group `completed` for its configured audit scope only after output and
  metadata are saved and verified;
- never trust status without checking the corresponding output;
- require an explicit UTC coverage start instead of inferring the recording day
  from an upload filename.
- use the first 23 eligible UTC days for proxy training and the final 6 days
  for proxy evaluation, without randomization or key overlap.

## Implementation Completed

The project now contains:

- streaming Binance feature inspection and as-of snapshot builders;
- gap-aware full-day Binance audits;
- proxy-target construction with receipt provenance;
- checksum-bearing manifests for direct-GZIP groups and the legacy ZIP sample;
- one-group audit execution with safe status transitions;
- multi-group batch orchestration with explicit coverage-map validation;
- an installable `tradingbot-data` package and Colab execution runbook;
- atomic writes, output checksums, stale-run recovery, and focused unit tests.
- a `proxy-baseline` command that fits a standardized logistic regression on
  training rows only and persists its model, evaluation predictions, and
  checksum-bearing metrics report;
- human-readable notebook checkpoints for model-view health, chronological
  separation, classification errors, calibration, probability separation, and
  standardized coefficients.

The local end-to-end reproduction completed the legacy sample, verified its
output, and safely skipped it on a subsequent run. Exact measurements are in the
2026-08-14 archive-runner evidence report.

The package was installed and its CLI was verified outside the repository. Git
origin is configured, and the reviewed project checkpoint has been pinned for
Colab at `03abbb745cc7919087b2e56607bb6bdf4d582a23`. A local byte-identical
reproduction of the July 27 direct-GZIP member passed the grouped runner and
matched the established ZIP baseline. Raw inputs and audit outputs remain
correctly outside the code package in Google Drive; the actual Drive-backed
persistent July 27 smoke test has now passed with an existing output and
matching checksum.

## Current Phase Status

Phase 1 is not complete. The 30-group Binance audit, proxy engineering view,
chronological split, and first proxy-baseline gates are complete. The baseline
evaluation was approximately chance-level and does not demonstrate useful
predictive signal. The official research-readiness gate still requires:

- recorder source-code review or an intentional replacement;
- recovery and verification of official Chainlink values and Polymarket
  outcomes;
- the synchronized, documented official research dataset and Phase 1
  visualizations.

The completed training run is explicitly proxy engineering only. It must not
be presented as the final Polymarket result. Official-target training,
backtesting, paper trading, and live trading remain deferred.

## Recommended Next Lesson

The completed baseline was correct on 854 of 1,706 evaluation rows, only nine
more than the training-majority baseline; ROC-AUC was 0.487225 and probability
losses were essentially coin-flip level. The learner is returning to the
lower-cost mentor for a training-period-only diagnostic EDA of the original
directional-regime hypothesis. Use signed minute-return bins, volatility
regimes, and explicit bin counts; do not inspect the six evaluation days while
selecting a second feature or model. Approve at most one explicit second
experiment after the EDA, or stop proxy iteration if no credible pattern
appears. Do not claim trading performance.

## Resume Instructions

After context compaction, read:

1. `README.md` and `AGENTS.md`;
2. immutable `instruction.md`;
3. `docs/LEARNING_CONTRACT.md`;
4. `docs/STATE.md`;
5. this report, then the specific evidence and review records for the next
   checkpoint.

Do not restart the completed lessons unless the learner requests a refresher
or demonstrates uncertainty. Do not rerun the expensive raw feature scans
unless their feature implementation or raw-source hash changes. A GPU is not
needed for the current three-feature, 8,292-row baseline.
