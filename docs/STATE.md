# Current Project State

Status: Authoritative current-state handoff  
Last updated: 2026-08-15

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

The checksum-bearing manifest generator at
`scripts/build_archive_manifest.py` supports both the legacy ZIP sample and the
actual direct-GZIP Drive layout. For direct GZIP, it forms candidate-date
groups, hashes each raw source member independently, records missing roles, and
excludes derived CSV exports from raw identity. It records groups as `pending`
and refuses to overwrite an existing manifest. The audit runner owns status
transitions after verified output exists.

The initial pinned Colab package smoke test passed at revision `43405c9`: the
repository cloned, `tradingbot-data` version `0.1.0` installed, and the
expected CLI commands were available. That earlier reproduction is recorded in
`docs/evidence/2026-08-14-colab-package-smoke-test.md`; the later grouped-GZIP
revision completed the first persistent Drive-backed audit.

The grouped-GZIP revision is now pushed and its pinned Colab upgrade has also
passed at revision `03abbb745cc7919087b2e56607bb6bdf4d582a23`: package version
`0.2.0` replaced `0.1.0` and exposed the revised group-oriented CLI. The Drive
manifest was then created successfully with 30 records and its structural
inspection matched the Drive inventory. A local byte-identical reproduction of
the July 27 direct-GZIP group matched the known ZIP baseline, and the actual
Drive-backed July 27 smoke test has now completed with a persistent output and
matching checksum. Exact evidence is in the 2026-08-14 Colab grouped-GZIP
package, manifest, manifest-inspection, and direct-GZIP reproduction records
under `docs/evidence/`.

Package version `0.2.0` has also been built and installed in an isolated local
environment. Ten focused tests verify schema-v1 compatibility, grouped-GZIP
manifest behavior, direct-GZIP and legacy-ZIP reading, scoped completion, and
coverage-map lookup. Exact scope is recorded in
`docs/evidence/2026-08-14-grouped-gzip-workflow-reproduction.md`.

The one-group runner at `scripts/run_archive_audit.py` and batch orchestrator at
`scripts/run_archive_batch.py` now process these records safely. The batch
runner requires an explicit group-to-UTC-day coverage map and refuses to guess
missing timestamps. Outputs are versioned and checksummed before a record can
become `completed` for its configured audit scope.

The workflow is installable as package `tradingbot-data` through
`pyproject.toml`. Its `tradingbot-data` command exposes the manifest, audit,
batch, proxy-target, snapshot, inspection, and day-audit workflows. The Colab
execution contract is documented in `docs/COLAB_RUNBOOK.md`.

The earlier coverage preflight scanned internal Binance receipt timestamps,
wrote a review report, and produced the current coverage map only after all 30
groups passed. The rewritten `tradingbot_data.ipynb` validates that existing
map and report before derived work runs. Exact preflight scope is in
`docs/evidence/2026-08-14-colab-coverage-map.md`; the rewrite scope is in
`docs/evidence/2026-08-15-colab-notebook-rewrite.md`.

## Available Artifacts

- Git origin is configured. Local `main` includes the proxy quality-review
  implementation; its code commit is `f2bcd78` and the notebook is being
  repinned to package `0.6.0` at that commit.
- A one-day recorder sample for 2026-07-27 is available locally as
  `data/raw/archives/drive-download-20260810T091218Z-1-001.zip`.
- The user has approximately 30 days of recorder data stored in Google Drive;
  it is not currently available in this workspace. A Colab inventory found 99
  direct GZIP files totaling about 10.75 GiB across 30 candidate dates. Twenty-nine
  candidates have Binance, Polymarket, and recorder-log inputs; 2026-06-29 lacks
  a Polymarket raw input and appears partial. Exact inventory evidence is in
  `docs/evidence/2026-08-14-drive-gzip-inventory.md`.
- A checksum-bearing manifest for the remote collection now exists at
  `/content/drive/MyDrive/tradingbot-data-audit/manifest-v2-03abbb7.json` and
  reports 30 completed records, with 89 authoritative raw members totaling 10.706 GiB,
  and 10 ignored derived files. Candidate 2026-06-29 is the sole incomplete
  group because `polymarket_raw` is absent. Every recorded member hash has the
  expected SHA-256 length. Exact inspection evidence is in
  `docs/evidence/2026-08-14-colab-grouped-gzip-manifest-inspection.md`.
- The local July 27 ZIP contains a Binance member with the exact size and
  SHA-256 recorded for the remote direct-GZIP group. The direct-GZIP runner
  reproduced the known July 27 audit summary, but its temporary output did not
  change the remote manifest. Exact scope is in
  `docs/evidence/2026-08-14-july27-direct-gzip-audit-reproduction.md`.
- The first persistent Drive-backed audit completed for group `2026-07-27`.
  Its output exists and its recorded checksum matches the output. Exact
  measurements are in
  `docs/evidence/2026-08-14-colab-july27-direct-gzip-audit.md`.
- The full 30-group Binance batch completed with zero reported failures. July
  27 was skipped only after its existing output was verified; the other 29
  groups produced persistent outputs. Exact run scope is in
  `docs/evidence/2026-08-14-colab-batch-audit.md`.
- A separate post-batch check verified all 30 manifest records are
  `completed`, every output exists, and every recorded output checksum matches;
  zero problems were found.
- The aggregate multi-day Binance report scanned 263,322,186 records with zero
  malformed JSON, zero duplicate starts, and zero backward starts. It found
  89,677 missing one-second starts across 55 gap events; the largest gap was
  645 seconds. June 29 is source-incomplete and severely under-covered; other
  high-gap days require gap-aware feature validity. Exact measurements are in
  `docs/evidence/2026-08-14-colab-multi-day-binance-quality.md`.
- The published package revision `0.3.0` contains a gap-aware Binance
  feature-view builder that emits one row per five-minute decision window and
  applies completion, receipt-time, and consecutive-lookback rules. Its July
  27 local canary produced 284 fully usable rows out of 288 requested windows;
  all 13 local tests passed. Exact scope and measurements are in
  `docs/evidence/2026-08-14-local-feature-view-canary.md`.
- The package `0.4.0` recovery implementation is committed at
  `6f5a0873b28024d62a72eb9f2411e79e9b299612`. Its `proxy-recover` command
  consumes the verified boundary report, writes a separate recovered target
  directory, checkpoints after each day, verifies output checksums, and leaves
  the original proxy-target CSVs untouched. Exact implementation scope is in
  `docs/evidence/2026-08-15-proxy-boundary-recovery-implementation.md`.
- A follow-up commit addresses a legacy derived-target bug exposed by
  the first Colab recovery attempt: invalid rows had discarded an otherwise
  valid boundary. The proxy builder now preserves partial boundaries, and
  recovery can repair legacy final-window rows only from an exact adjacent
  boundary. Package version `0.4.1` is committed at
  `41fdff5619d4c00389628eb526f9f66ac19f3650`; the commits are pushed, but the
  recovery has not yet been rerun remotely. Exact diagnosis and validation are
  in
  `docs/evidence/2026-08-15-proxy-recovery-legacy-row-fix.md`.
- The published `0.3.0` package has now run remotely across the first derived
  feature view: 29 eligible days produced 8,352 rows, of which 8,316 are fully
  usable and 36 retain invalidity flags. Twenty-eight days were processed and
  the verified-shape July 27 output was skipped; June 29 was excluded by
  policy. Exact scope is in
  `docs/evidence/2026-08-14-colab-feature-view-batch.md`.
- The first quality review classified those 36 rows as 29
  `received_after_cutoff` rows and 7 `missing_kline` rows. The 29-to-29-day
  pattern was confirmed as exactly one `00:00:00Z` opening-boundary row per
  eligible day. The 7 missing-lookback rows are isolated intraday gaps on July
  1, July 25, July 26, and July 27; they remain preserved for row-level
  review. Exact counts and timestamps are in
  `docs/evidence/2026-08-14-colab-feature-quality-review.md`.
- The separate Binance proxy-target canary also passed remotely for July 27:
  283 valid targets out of 288 windows, 2 missing start boundaries, and 3
  missing end boundaries. All 283 valid targets had late start receipts, which
  is allowed for offline target construction and is not feature leakage. Exact
  scope is in `docs/evidence/2026-08-14-colab-proxy-target-canary.md`.
- The 29-day proxy-target batch produced 8,299 valid targets out of 8,352
  windows, with 13 missing start boundaries, 40 missing end boundaries, and no
  duplicates. Timestamp review found 29 final `23:55:00` windows and 11
  non-final missing-end windows; the 13 missing-start rows are also intraday.
  The boundary-recovery scan then found 28 of the 29 final boundaries in the
  scanned raw collection; only the `2026-07-28` final boundary remains absent.
  The proxy-target count is not yet regenerated with the recovered provenance.
  Exact batch measurements are in
  `docs/evidence/2026-08-14-colab-proxy-target-batch.md`.
- The completed boundary-recovery report is at
  `/content/drive/MyDrive/tradingbot-data-audit/proxy-boundary-recovery-v1.json`.
  It searched all 30 source groups, found 28 of 29 requested final boundaries,
  and left `2026-07-28` unrecoverable from the scanned collection. Exact scope
  and consequence are in `docs/evidence/2026-08-15-colab-boundary-recovery.md`.
- The pinned recovery run has now applied all 28 uniquely sourced boundaries
  into the separate recovered view. All 29 eligible days completed with zero
  review rows and zero unused recoverable boundaries. The recovered view has
  8,327 valid rows and 25 invalid rows out of 8,352; the original target view
  remains unchanged. Exact measurements are in
  `docs/evidence/2026-08-15-colab-proxy-target-recovery.md`.
- The Colab notebook is now a 31-cell Phase 1 runbook being repinned to package
  commit `f2bcd784f3a54331069f088d5d182a407c51f7bf` (`0.6.0`). It verifies control
  artifacts, runs feature and proxy views separately, applies the verified
  boundary recovery into a separate view, and stops before any model-ready
  join and quality-review cells have not yet run remotely. Exact rewrite history is in
  `docs/evidence/2026-08-15-colab-notebook-rewrite.md` and the recovery update
  is in `docs/evidence/2026-08-15-colab-recovery-notebook-update.md`.
- The package `0.6.0` implementation now provides the next proxy dataset-quality
  gate. It matches by `window_start_utc`, stops on duplicate keys, preserves
  all source keys in an audit join, and emits a filtered per-day model-ready
  proxy view using only `return_1s`, `return_1m`, and `volatility_1m` as initial
  model features, canonicalizes equivalent UTC timestamp text before matching,
  invalidates stale checkpoints when the implementation changes, and reviews
  label balance, finite numeric features, chronology, and exclusions. Its
  21-test local suite passes; the repinned notebook has not yet run the review
  in Colab. Exact design is in
  `docs/evidence/2026-08-15-proxy-join-implementation.md`.
- The corrected proxy join has now run remotely. It produced 8,352 audit rows
  and 8,292 leakage-safe model-ready rows across the 29 eligible days; 60 rows
  remain excluded by feature/target validity. The model view contains only the
  three initial Binance features plus identifiers, label, and proxy-source
  metadata. Exact measurements and Drive paths are in
  `docs/evidence/2026-08-15-colab-proxy-join.md`.
- Its boundary-recovery scan checkpoints after each completed raw source
  archive, so an interrupted Drive scan resumes at archive granularity rather
  than restarting the full collection. The remote run completed all 30 source
  groups and published a review report with 28 recoverable boundaries and one
  unresolved July 28 boundary.
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

The direct-GZIP collection uses one logical candidate-date capture group as its
resumable work unit. A group can contain `binance_raw`, `polymarket_raw`, and
`recorder_log` members. Each present raw member has its own path, size, and
checksum. Derived CSV exports do not define raw input identity. A missing role
is retained explicitly; it is never silently filled or treated as present.

The candidate date groups physical files but is not proof of UTC coverage. An
explicit coverage map, verified from timestamps inside the inputs, controls the
UTC interval audited.

Group input completeness and audit processing status are different. The
current runner's scope is Binance day coverage, so it may complete that audit
for a group whose Polymarket member is missing. Such a group remains incomplete
for the later three-source research-readiness gate.

A group may be marked `completed` for its configured audit scope only after its
audit output and processing metadata have been saved and verified. A scan that
finished in memory but did not produce verified persistent outputs is not
complete.

Manifest status and filesystem state must agree. A `completed` status without
the expected verified output is an inconsistency and must not cause the archive
to be skipped. An output found beside an `interrupted` or `failed` status is
untrusted until its provenance and contents are verified or the archive is
reprocessed.

Audit scope is also explicit: the runner must receive a UTC day start for each
group through its command line or the batch coverage map. Group IDs and input
filenames are not treated as proof of recording-day coverage.

Exact measurements, scope, and supporting sources are owned by
`docs/evidence/2026-07-27-sample-data-audit.md`.

## Constraints and Open Questions

- It is unknown whether the same collection defects affect all 30 recorded days.
- The July 27 persistent Drive smoke test passed. The full collection's
  coverage mapping also passed; the remaining workflow risk is per-day audit
  data quality and source completeness.
- Historical resolved outcomes may be recoverable from Polymarket, but recovery
  has not been implemented or verified for the full dataset.
- The exact availability of historical Chainlink reference values for the
  recorded period still needs verification.
- Recorder corrections cannot be implemented until its source code is supplied
  or a replacement recorder is intentionally built.

## Recommended Next Work

1. Review the proxy model-ready view's label balance, feature numeric quality,
   chronological ordering, and per-row exclusion reasons. Then define a
   chronological baseline train/evaluation split; do not randomize windows.
2. Preserve the unresolved July 28 boundary and the intraday missing-boundary
   rows as invalid unless separately verified source evidence is found.
3. Determine which historical Chainlink labels and reference values can be
   recovered.
4. Correct or replace the recorder before collecting additional research data.
5. Define and evaluate the official in-window dataset separately from the
   proxy dataset.

No model training should begin from the sample archive alone.
