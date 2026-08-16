# Learning Progress

Status: Authoritative durable lesson record  
Last updated: 2026-08-15

This file records the learner's durable understanding, corrected
misconceptions, and next teaching checkpoint. It does not replace the project
state, review question bank, evidence records, or decision log. Review questions
are maintained in `docs/REVIEW_QUESTIONS.md`.

## Lesson 1 — Prediction, Outcomes, Prices, and Timestamps

### Understanding demonstrated

- A prediction unit is one five-minute BTC Up/Down market at a specified
  decision time.
- The target is the later official result, `UP` or `DOWN`.
- A model probability such as `P(UP) = 0.60` is different from the target.
- A market buy uses the ask; a limit buy placed at the bid may wait. The
  immediate buyer is a taker, while the waiting order is passive/maker-side.
- A return is a relative price change stored as a decimal. Multiplying it by
  100 expresses the same return as a percentage.
- A simple raw trading edge compares model probability with the ask price:
  `P(UP) - ask`. A negative edge means the UP contract is overpriced under
  that model, while a positive edge is favorable expectation rather than a
  guaranteed individual win.
- Zero edge is neutral, not positive. A strategy requiring strictly positive
  edge should not trade at exactly zero, especially because costs would make
  the net edge negative.

### Corrected misconception

A kline may describe a past interval but still be unavailable at the decision
time if it arrived late. Feature eligibility is determined by the observable
receipt/availability time, not only by the interval summarized by the record.
Using a record before its receipt time would create future leakage or
look-ahead bias.

### Current checkpoint

The learner can identify the difference between a kline's measurement interval
and its availability time, can calculate a simple return from consecutive
closes, and can map those values into a CSV feature row.

### Next lesson

Build a small, inspectable feature table from closed Binance klines while
preserving each feature's availability timestamp.

## Lesson 2 — First Streaming Feature Inspector

### Implementation completed

`scripts/inspect_binance_klines.py` now streams the compressed Binance JSONL
member directly from the ZIP archive. It filters closed one-second klines,
computes `return_1s` only when the preceding kline is consecutive, and retains
the recorder receipt time as `available_at_utc`.

### Current checkpoint

The learner has seen the first generated feature rows and can now focus on why
the script rejects non-consecutive returns and preserves receipt timestamps.
The learner understands that a data gap is a missing expected interval, while
the first row is merely missing a predecessor; a return must not be labeled
one-second when the intervening interval is absent.

### Next lesson

Interpret the generated rows, then extend the inspector toward a gap-aware
per-day audit.

## Lesson 3 — Full-Day Coverage and Gap Scope

### Implementation completed

`scripts/audit_binance_klines.py` now scans the complete compressed Binance
member and reports stream counts, closed-kline coverage, duplicate and
backward starts, missing one-second starts, and the largest gap.

### Current checkpoint

The learner understands that a gap is a missing expected interval and that
coverage counts must state their time scope. A file-wide count can differ from
the count whose kline starts fall inside a strict UTC-day interval.
The learner also distinguishes the observed fact of missing starts from a
hypothesis about their cause, and understands that missing market data must not
be silently invented or filled without an explicitly justified method.

The learner understands the purpose of a raw-archive manifest: it records which
data was processed, verifies exact contents with a checksum, and allows a
multi-day job to resume after interruption. Audit reports belong in persistent
Google Drive storage, while the raw ZIP files remain unchanged.

The learner also understands the resumability rules: a completed archive with
the same checksum can be skipped, an interrupted archive must not be trusted as
complete, and a changed checksum requires a new preserved audit result rather
than silently overwriting the old one.

The learner understands that a matching raw checksum is not sufficient when the
audit implementation changes. An audit/code version must identify which logic
produced each result; an old result must not be presented as the output of new
code without rerunning.

The learner also understands that a changed data-quality policy can alter an
audit result even when the raw data and code are unchanged. Results therefore
need a policy version in addition to the raw checksum and audit/code version.

The learner refined the reuse rule: a changed reproducibility identifier
normally requires a new audit result. Reuse is acceptable only when a
backward-compatible change has been deliberately verified and documented as
unable to affect that result.

The learner understands the Data Readiness Gate: it determines whether the
available data is trustworthy, correctly timed, and sufficiently labeled for a
research dataset. The learner also understands that the one-day sample cannot
establish the condition of all 30 days.

The learner understands a proposed two-track approach: a Binance-proxy target
can validate the feature, dataset, training, and evaluation pipeline before
official Chainlink labels are available, but proxy results cannot establish the
final Polymarket research result. Every target must identify its `label_source`
so proxy and official labels cannot be mixed.

The learner accepted the first proxy design: decision time equals the proxy
window start, and the model predicts the next five minutes using only data
available at that start. A later Polymarket-faithful task will keep the fixed
market start/end separate from a decision time that may occur inside the market
window. These evaluations are not interchangeable.

### Next lesson

Specify the proxy boundary-sampling method and target-table schema while
keeping the official target track separate. The learner understands that future
data may construct a historical target but may never be included in decision-
time features.

The learner accepted the proxy boundary rule: use the completed one-second
close immediately before the window start and immediately before the five-minute
end. Both are target-construction inputs, so their receipt times may be later;
the feature cutoff applies when deciding whether a value can be a model input.

The learner corrected an important boundary mistake: the receipt-time cutoff
for decision-time features must not be applied to a boundary value used only
to construct a historical target. A start boundary received after decision
time cannot be a feature at that decision, but it can still be used later to
calculate the proxy label. The target table preserves the receipt timestamp
and keeps the late boundary out of the feature row.

The corrected proxy audit therefore produced 283 valid labels from the local
day, while retaining 5 windows with missing boundaries. The earlier zero-valid
result remains a historical measurement of the overly strict rule rather than
the current target-validity result.

## Lesson 4 — Explicit Feature Validity Rules

### Implementation completed

`docs/DATA_QUALITY_POLICY.md` defines the initial rules for preserving raw
observations, rejecting returns across gaps, preserving receipt timestamps, and
separating observations from causal hypotheses. The feature inspector now
emits `feature_valid` and `quality_flag` alongside `return_1s`.

### Current checkpoint

The learner understands that missing or non-consecutive data should remain
visible and explicitly flagged rather than being silently filled. The learner
accepted the distinction between retaining invalid rows for audit and excluding
them only from the first model-dataset view.

The learner also understands that validity is feature-specific: a dependency
failure invalidates the affected feature, while model eligibility requires all
features used by that model to be valid and available at the decision cutoff.

The learner can distinguish the later target from availability metadata and
understands why an observed raw row remains valuable even when one derived
feature is invalid.

The learner understands that decision-time eligibility requires both the
measurement interval and the receipt time to be at or before the cutoff. If
required data is unavailable, the historical row is unusable and a live
strategy should default to `NO TRADE` rather than produce a prediction.

The inspector now supports `--model-only` without changing the default audit
output.

### Next lesson

Define how per-second observations are aggregated into a decision-time feature
row while respecting the feature cutoff and validity rules.

## Lesson 5 — Decision-Time Snapshot

### Implementation completed

`scripts/build_decision_snapshot.py` builds one as-of BTC feature snapshot. It
requires both the kline interval to be complete and the recorder receipt time
to be at or before the decision cutoff. It now computes `return_1m` and
`volatility_1m` from the same complete 60-second lookback; the reproducible
cutoff comparison is recorded in
`docs/evidence/2026-08-11-volatility-feature-reproduction.md`.

### Current checkpoint

The learner understands that the latest market-time observation may not be the
latest usable observation when collection is delayed. The snapshot must use
the latest observation that is both complete and available.

The learner accepted a 60-second initial lookback and understands that an
aggregated return is invalid when any required one-second input is missing,
late, or invalid.

The initial `volatility_1m` implementation uses population standard deviation
over the same 60 valid one-second returns, with the same dependency and
cutoff requirements as `return_1m`.

The learner now understands deviation as distance from the average and
standard deviation as the typical distance of values from that average. The
learner also distinguishes net direction from volatility: a path can finish
near its starting price while having high volatility.

The learner corrected an important interpretation error: a negative recent BTC
return is evidence about movement before the decision time, not proof of the
future Polymarket label. The official label is determined later by the market's
settlement rule, so a negative feature and an `UP` outcome can coexist.

The learner can now separate a historical training row into decision-time
inputs and a later target: features and market price must be available by the
cutoff, while the official `UP`/`DOWN` label is added afterward for training
and evaluation and must not be used as an input.

The learner also correctly applies the settlement rule: `UP` means the
Chainlink BTC/USD price at the end of the market's title range is greater than
or equal to its beginning price; otherwise the label is `DOWN`. Binance
BTCUSDT may provide predictive features but does not define the official label.

If the official Chainlink data needed for the target is missing, the learner
understands that Binance must not be used as a substitute label. The row should
remain available for audit but must be excluded from labeled training and
evaluation until the official target is recovered.

The learner distinguishes prediction eligibility from training eligibility: a
row can support a live prediction when its decision-time inputs are valid and
available, even though its future label is not known yet. The same row cannot
enter supervised training until its official label is recovered.

### Next lesson

Design a checksum-bearing archive manifest and reason about how a multi-day
audit can resume safely after a remote runtime stops. The learner selected one
complete archive as the resumable work unit and correctly defined `completed`
as a post-verification status: the audit output and metadata must already be
saved and verified.

The learner also understands that manifest status cannot be trusted in
isolation. A missing output for a `completed` entry requires investigation or
reprocessing, and an output beside an `interrupted` or `failed` entry is not
automatically reusable.

The initial manifest generator now hashes raw ZIP archives in streaming chunks,
records input and processing identities, initializes each archive as `pending`,
and refuses to overwrite an existing manifest path. The learner understands
that this generator creates the control record; a later audit runner must own
status transitions and verified output attachment.

The manifest-controlled one-archive runner and batch orchestrator are now
implemented. The next teaching checkpoint is to reason about the explicit
archive-to-UTC-day coverage map before using the workflow on the remote archive
collection.

The learner completed that checkpoint: an upload filename is not evidence of
recording-day scope because it identifies a transfer artifact and can be
renamed. Ambiguous or multi-day coverage must be marked for review rather than
assigned to a guessed UTC day.

### Next checkpoint

The remote inventory revealed that the real collection consists of direct
GZIP source files rather than ZIP archives. The learner accepted a revised
abstraction: one logical candidate-date group contains independently identified
Binance, Polymarket, and recorder-log inputs; derived CSVs do not define raw
identity; missing roles remain explicit; and the candidate date is not proof of
UTC coverage. This is decision D-026.

Install the grouped-GZIP workflow at a pinned revision in Colab, build and
inspect its manifest, verify one group's UTC coverage from event timestamps,
and run that group before starting the full resumable audit.

## Lesson 6 — Multi-Day Data Quality Gate

### Completed checkpoint

The learner completed the full remote data-foundation run: all 30 Binance audit
outputs were persisted and checksum-verified, and the aggregate report found
zero malformed JSON, zero duplicate starts, and zero backward starts. The
collection has 89,677 missing one-second starts across 55 gap events, with a
largest gap of 645 seconds. One group, 2026-06-29, is both source-incomplete
and severely under-covered.

The learner accepted the first downstream inclusion policy: exclude 2026-06-29
from the initial feature/proxy view while preserving its raw and audit rows;
retain other days and determine row validity from each feature's gap and
receipt-time dependencies rather than deleting whole days automatically.

### Next checkpoint

Construct the gap-aware Binance feature/proxy view and measure how many rows
remain valid after the 60-second lookback and receipt-time rules. Keep official
Chainlink labels and Polymarket source completeness as a separate research gate.

## Lesson 7 — Proxy Model-View Quality Gate

### Implementation completed

The corrected proxy pipeline now produces a structurally reviewed model view
with balanced labels, chronological keys, finite features, and explicit
exclusion accounting. The initial review caught a feature-definition defect:
the feature builder had accidentally used the latest one-second return as
`return_1m`. Package `0.6.1` now computes the net return over the complete
60-second lookback, and the remote rerun confirms that `return_1m` has a
distinct range from `return_1s`. Exact measurements are in
`docs/evidence/2026-08-15-colab-proxy-model-review-after-fix.md`.

### Current checkpoint

The Binance proxy engineering-view gate is complete. This is not yet the
official Polymarket research dataset because the Chainlink settlement target
and official outcomes remain unresolved. The next teaching checkpoint is to
define a chronological train/evaluation split without randomizing windows.

## Lesson 8 — Chronological Baseline Split

### Understanding demonstrated

The learner correctly selected earlier eligible days for training and later
eligible days for evaluation, identifying the central leakage risk: training
must not use information from the future period it is supposed to predict. The
learner accepted an initial split of 23 training days and 6 evaluation days so
the baseline has more historical training data while retaining a later unseen
period for evaluation.

### Accepted split

- Training: `2026-06-30` through `2026-07-22`
- Evaluation: `2026-07-23` through `2026-07-28`

This is an engineering/proxy baseline split, not an official Polymarket
research result. The next step is to build a persisted split manifest and
verify the resulting usable-row counts before training.

The persisted split was then executed remotely and verified: 8,292 model rows
were partitioned into 6,586 training rows and 1,706 evaluation rows, with zero
overlap in `window_start_utc` keys. The learner is ready for the first simple
proxy baseline. The training gate will compare that model with a majority-class
baseline before any feature tuning or more complex model is considered.

## Lesson 9 — First Proxy Baseline

### Experiment completed

The standardized three-feature logistic regression completed remotely and its
checksum-bearing Drive artifacts were verified. A subsequent notebook run
safely reused those artifacts instead of retraining. On 1,706 later evaluation
rows, the model was correct on 854 rows versus 845 for the training-majority
baseline. Its ROC-AUC was below 0.5 and its log loss and Brier score remained
essentially at coin-flip levels. Exact measurements are in
`docs/evidence/2026-08-15-colab-proxy-baseline-run.md`.

### Next teaching checkpoint

The notebook now follows its machine gates with three human views: model-ready
data health and feature distributions, the chronological split timeline, and a
baseline dashboard covering metrics, errors, calibration, probability
separation, and coefficients. These cells reload durable Drive artifacts and
do not repeat raw processing or training.

Interpret what each evaluation plot and confusion-matrix cell measures, then
decide whether this result supports a second hypothesis-driven experiment. Do
not treat a nine-row improvement as evidence of trading edge, and do not reuse
the same evaluation period indefinitely while still calling it untouched.

The first data-overview visualization rendered remotely. It confirms high
model-row coverage, balanced proxy labels, returns concentrated near zero, and
right-skewed volatility. The learner correctly redirected the explanation to
the actual graph rather than accepting a repeated feature-definition lesson.

The learner is transferring back to the lower-cost mentor. The next lesson is
training-period-only EDA of whether signed minute direction behaves differently
across volatility regimes. The six observed evaluation days are frozen during
that exploration.

The learner then clarified and accepted the intended abstraction boundary:
Binance is sufficient for the active ML-learning and BTC-direction
signal-development track; Chainlink is required later to validate the exact
Polymarket settlement label; and Polymarket data becomes necessary when moving
from direction prediction to market-window timing, executable prices,
liquidity, and Trade versus No Trade. The learner also recognized that these
sources should be swappable behind interfaces rather than entangled throughout
the pipeline. The canonical project rule is
`docs/DATA_QUALITY_POLICY.md` rule 19.

The learner also proposed testing longer direction windows if five-minute BTC
direction remains difficult. The accepted research response is comparative,
not assumptive: build separate 5-minute, 15-minute, and 60-minute Binance tasks
and measure them under horizon-specific chronological validation and untouched
holdouts. This demonstrates an important experimental principle: target horizon
is a hypothesis to evaluate, not a parameter to choose after inspecting final
test performance. The canonical rule is `docs/DATA_QUALITY_POLICY.md` rule 20.

The learner immediately recognized that simultaneous three-horizon research
would make the learning problem unnecessarily complicated and chose one active
target: 15-minute Binance direction. The five-minute baseline remains useful
engineering history, while 5-versus-15-versus-60-minute comparison is postponed
until the learner understands the full 15-minute loop. This is a deliberate
scope reduction, not a conclusion that 15 minutes is objectively best. The
canonical rule is `docs/DATA_QUALITY_POLICY.md` rule 21.

## Lesson 10 — Historical 15-Minute Direction Dataset

### Accepted scope

The learner accepted a new, simpler Binance-only learning slice. It uses
historical 1-minute klines to construct non-overlapping 15-minute direction
windows. It does not use Polymarket, Chainlink, GPU computation, trading logic,
or the completed five-minute evaluation period.

Historical REST klines contain market interval timestamps and OHLCV values but
not the original client receipt time. The learner accepted an explicit
`interval_complete_assumption`: a completed historical interval is treated as
available after its interval closes, while the dataset is not called
receipt-time verified. Recorder data with `received_at_utc` remains the later
validation source.

The learner rejected limiting the first 15-minute feature set to only immediate
1-minute and 5-minute movement. The accepted regime-aware design obtains
independent Binance history, keeps at least 100 completed daily candles as
warm-up, aggregates the same 1-minute source into 1-hour, 4-hour, and daily
candles, and summarizes the daily history into interpretable regime features.
Each timeframe must use only its last completed candle at or before the decision
time.

The learner then narrowed the first implementation to a 12-feature short-term
block: `return_1m`, `return_5m`, `return_15m`, `return_30m`, `volatility_5m`,
`volatility_15m`, `volume_ratio_5m`, `candle_body`, `high_low_range`,
`distance_ma_15`, `ma_slope_15`, and `rsi_14`. The long-term regime block is
deferred until the short-term dataset-to-evaluation loop is understood.

The learner accepted the V1 timing architecture: use historical Binance
1-minute klines as the raw source, make predictions only at fixed UTC
quarter-hours, create non-overlapping 15-minute targets, and derive the
5-minute, 15-minute, and 30-minute context features from the same 1-minute
source. Prediction cadence and raw-data frequency are intentionally distinct.

### Next checkpoint

Define the exact short-term feature formulas and target-period boundaries, then
implement the chronological train/validation/final-holdout dataset builder.

### Implementation checkpoint — 2026-08-15

The formula and boundary implementation is complete in package `0.9.0` at
commit `91507cf3303bc0a88977091c3601175b3acd21e4`. A separate stateless
Colab notebook now downloads independent historical Binance 1-minute klines,
checkpoints one UTC day at a time on Drive, and builds the audited 15-minute
dataset with model-ready and chronological split reports. Local tests cover
future-feature isolation, missing-boundary preservation, final-output
verification, unique chronological keys, and rerun skipping.

The next learning checkpoint is to run the notebook remotely and interpret its
source coverage and usable-row counts. The notebook proposes 20 training
days, 4 validation days, and 5 final holdout days; this split still needs the
learner's explicit acceptance before it becomes the durable experiment design.

## Lesson 11 — Replace the Active Task with Hourly Direction

### Accepted scope

The learner recognized that the 20/4/5 split belonged only to the small
29-day prototype, not to a multi-year Binance dataset. The active experiment
is now the latest four complete UTC years of BTCUSDT history. The prediction
task is one-hour direction: decide at each `HH:00` and predict the following
non-overlapping 60-minute window. Historical 1-minute klines remain the raw
source.

The 15-minute notebook and implementation remain preserved as prototype
history. The active hourly replacement is implemented in package `0.10.0` at
commit `925e4d9f9a94a7ffb9f777caafbbe7badde337d1`, with a separate stateless
four-year Colab notebook and explicit chronological date boundaries.

### Next checkpoint

Run the hourly notebook remotely. Inspect downloaded-day coverage, feature and
target validity, model-ready row counts, label balance, and the approximately
70/15/15 chronological split before training a baseline.
