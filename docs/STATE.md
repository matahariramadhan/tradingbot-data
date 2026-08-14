# Current Project State

Status: Authoritative current-state handoff  
Last updated: 2026-08-14

This file describes the present, not project history or detailed evidence.

## Current Position

The project is in data foundations and data-quality assessment. No research
dataset, model, backtest, or trading system has been implemented in this
workspace yet.

`instruction.md` is the immutable project charter. The teaching approach is
defined separately in `docs/LEARNING_CONTRACT.md`.

A first educational Binance kline inspector now exists at
`scripts/inspect_binance_klines.py`. It streams the compressed archive member,
computes a simple one-second return, and preserves feature availability time;
it is not yet a research dataset pipeline. Its default output retains invalid
rows for audit, while `--model-only` provides the initial filtered view.

The initial data-quality rules for that feature are defined in
`docs/DATA_QUALITY_POLICY.md`.

An as-of decision snapshot builder now exists at
`scripts/build_decision_snapshot.py`; it applies both interval-completion and
receipt-time cutoffs, but it does not yet create a labeled research dataset.

The Binance proxy target builder now creates an offline target table while
preserving the receipt time of each target boundary observation. Late target
boundaries do not invalidate a historical label, but they remain ineligible as
decision-time features.

The initial checksum-bearing manifest generator now exists at
`scripts/build_archive_manifest.py`. It hashes archives in streaming chunks,
records them as `pending`, and refuses to overwrite an existing manifest. It
does not mark archives completed; a later audit runner must update status only
after verified output exists.

The one-archive runner at `scripts/run_archive_audit.py` and batch orchestrator
at `scripts/run_archive_batch.py` now process these records safely. The batch
runner requires an explicit archive-to-UTC-day coverage map and refuses to guess
missing timestamps. Outputs are versioned and checksummed before a record can
become `completed`.

The workflow is installable as package `tradingbot-data` through
`pyproject.toml`. Its `tradingbot-data` command exposes the manifest, audit,
batch, proxy-target, snapshot, inspection, and day-audit workflows. The Colab
execution contract is documented in `docs/COLAB_RUNBOOK.md`.

## Available Artifacts

- Git origin is configured and the reviewed project checkpoint is committed
  locally. It has not been pushed as part of this workspace session.
- A one-day recorder sample for 2026-07-27 is available locally as
  `data/raw/archives/drive-download-20260810T091218Z-1-001.zip`.
- The user has approximately 30 days of recorder data stored in Google Drive;
  it is not currently available in this workspace.
- Recorder source code is not currently present in this workspace.

The accepted working architecture keeps the large raw archives in remote
storage and runs multi-day audits, feature generation, training, and evaluation
in a remote compute environment. The local laptop is reserved for code,
documentation, tests, small fixtures, and compact reports or model artifacts.
The specific remote compute/storage provider has not yet been selected.

The accepted target architecture has two separate tracks. A Binance-derived
proxy target may be used now to build and validate the engineering pipeline. The
official Chainlink target remains mandatory for final Polymarket research
claims. Target records must identify `label_source` so proxy and official
results cannot be mixed.

The first proxy experiment is now defined as a clean future-window task:
decision time equals the proxy window start and the target ends five minutes
later. A later Polymarket-faithful task will keep fixed market start/end times
separate from a decision time that may occur inside the market window. These are
different prediction problems and their evaluations must remain separate.

The proxy boundary rule is also accepted: use the completed one-second close
immediately before the window start and immediately before the five-minute end.
Both are target-construction inputs, so their receipt times may be after the
decision time; the receipt-time feature cutoff still applies to model inputs.

The earlier strict proxy run found zero valid targets because it applied the
feature cutoff to the start boundary used only for target construction. That
historical measurement remains in
`docs/evidence/2026-08-13-binance-proxy-target-audit.md`. Under the corrected
rule, the local day contains 283 valid proxy targets and 5 windows with missing
boundaries. The corrected reproduction is in
`docs/evidence/2026-08-14-binance-proxy-target-reinterpretation.md`.

## Verified Current Assessment

The one-day raw sample is valuable but not research-ready as a complete trading
dataset. Binance events can support feature research after gap-aware cleaning.
Polymarket coverage does not span the complete active five-minute windows. The
official Chainlink settlement/reference stream and explicit winning outcomes are
absent.

The focused full-day Binance audit clarifies that file-wide closed-kline counts
and strict in-day coverage counts must be kept separate; the reproduction and
scope difference are documented in
`docs/evidence/2026-08-11-binance-kline-audit-reproduction.md`.

The decision-snapshot reproduction confirms that the latest market-time kline
may be unusable at a cutoff because it arrived late; the exact example is
documented in `docs/evidence/2026-08-11-decision-snapshot-reproduction.md`.

The initial 60-second lookback reproduction confirms that a valid `return_1s`
does not imply a usable `return_1m` when insufficient eligible history exists;
the exact result is documented in
`docs/evidence/2026-08-11-lookback-feature-reproduction.md`.

The snapshot builder now also computes the initial `volatility_1m` from the
same 60 consecutive eligible one-second returns. An early cutoff leaves both
one-minute features unusable, while a later complete lookback makes both valid;
the reproduction is documented in
`docs/evidence/2026-08-11-volatility-feature-reproduction.md`.

The corrected proxy audit separates target availability from feature
availability: the target table can use a boundary received after decision time,
while the decision-time snapshot cannot.

## Archive Processing Contract

The initial multi-day audit uses one complete archive as its resumable work
unit. An archive may be marked `completed` only after its audit output and
processing metadata have been saved and verified. A scan that finished in
memory but did not produce verified persistent outputs is not complete.

Manifest status and filesystem state must agree. A `completed` status without
the expected verified output is an inconsistency and must not cause the archive
to be skipped. An output found beside an `interrupted` or `failed` status is
untrusted until its provenance and contents are verified or the archive is
reprocessed.

Audit scope is also explicit: the runner must receive a UTC day start for each
archive through its command line or the batch coverage map. Archive filenames
are not treated as proof of recording-day coverage.

Exact measurements, scope, and supporting sources are owned by
`docs/evidence/2026-07-27-sample-data-audit.md`.

## Constraints and Open Questions

- It is unknown whether the same collection defects affect all 30 recorded days.
- Historical resolved outcomes may be recoverable from Polymarket, but recovery
  has not been implemented or verified for the full dataset.
- The exact availability of historical Chainlink reference values for the
  recorded period still needs verification.
- Recorder corrections cannot be implemented until its source code is supplied
  or a replacement recorder is intentionally built.

## Recommended Next Work

1. Obtain the recorder source code and build the checksum-bearing manifest for
   the 30 daily archives in remote storage.
2. Build and verify the archive-to-UTC-day coverage map without guessing from
   upload filenames.
3. Review the focused per-day audit and extend it into a multi-day coverage and
   integrity report without loading entire archives into memory.
4. Determine which historical Chainlink labels and reference values can be
   recovered.
5. Correct or replace the recorder before collecting additional research data.
6. Define and evaluate the official in-window dataset separately from the proxy
   dataset.

No model training should begin from the sample archive alone.
