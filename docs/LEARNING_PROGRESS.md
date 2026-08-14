# Learning Progress

Status: Authoritative durable lesson record  
Last updated: 2026-08-14

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

Apply the verified coverage map to the remote archive collection and run the
multi-day data-readiness audit one archive at a time.
