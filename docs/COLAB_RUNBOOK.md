# Google Colab Runbook

This is the execution handoff for the remote archive and derived-view workflow.
The ordered `tradingbot_data.ipynb` is the maintained completed-pipeline
runbook. The separate `historical_binance_15m.ipynb` is the active simple
historical Binance direction-data lesson. Colab runs the package; Google Drive
stores raw archives, manifests, coverage maps, checkpoints, and derived
outputs. The repository must contain code and runbook documentation, not raw
data.

## Stateless Colab contract

Colab is a disposable compute session. A runtime restart may erase all Python
variables, local files under `/content`, execution counts, and displayed cell
outputs. The notebook must therefore treat them as caches, never as the source
of truth.

Durable ownership is split as follows:

| Information | Durable location |
| --- | --- |
| Source code and package revision | Git repository |
| Raw archives | Google Drive raw-data directory |
| Manifest and coverage map | Google Drive control directory |
| Audit outputs and checksums | Google Drive audit directory |
| Derived feature/proxy outputs | Google Drive derived-view directories |
| Batch checkpoints and review reports | Google Drive control directory |

The notebook is an ordered runbook. After a fresh runtime, rerun its bootstrap
and control-gate cells in order before running a downstream cell. A downstream
cell may require those explicit prerequisites, but it must fail clearly when
they are missing rather than silently using stale or guessed state.

Every notebook cell must be safe under these conditions once its documented
prerequisites are present:

- A fresh runtime has no prior in-memory variables.
- A cell is rerun after an interruption.
- A long scan stops halfway through one work unit.
- An output already exists from a verified earlier run.

Long-running cells must checkpoint after each meaningful work unit, such as one
archive or one UTC day. On rerun they must reload the checkpoint or inspect
verified per-unit outputs, skip completed verified units, and repeat at most
the unit that was interrupted. A final output is published only after the unit
completes and its shape or checksum is verified. Temporary files must not be
mistaken for completed outputs.

Short summary cells may rerun from persisted outputs without checkpoints. They
must still reload their input files instead of relying on variables created by
earlier cells. If required durable state is missing, the cell must stop with a
clear message rather than silently rebuilding or guessing it.

## 1. Clone a pinned revision

Use the repository URL and the reviewed baseline-training commit
`63cbd647953d203abab23ccd5d27c9a87aec3d4a`:

```python
!git clone https://github.com/<owner>/<repository>.git /content/tradingbot_v2
%cd /content/tradingbot_v2
!git checkout <reviewed-commit>
!pip install ".[training]"
!tradingbot-data --help
```

After setup, execute `tradingbot_data.ipynb` from top to bottom. It verifies
the existing manifest, coverage map, and checksum-bearing audit outputs before
running the derived feature and proxy views. It stops at the cross-archive
recovery gate until that target policy is explicitly accepted.

The human-readable baseline package revision is `0.8.1`. Do not run recovery,
joining, or review from an unpinned working tree. After commit
`63cbd647953d203abab23ccd5d27c9a87aec3d4a` is available from the repository,
run:

```python
!tradingbot-data proxy-recover \
  --input-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-targets" \
  --output-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-targets-recovered-v1" \
  --boundary-report "/content/drive/MyDrive/tradingbot-data-audit/proxy-boundary-recovery-v1.json" \
  --output-report "/content/drive/MyDrive/tradingbot-data-audit/proxy-target-recovery-v1.json"
```

It checkpoints one UTC-day CSV at a time, skips verified recovered outputs on
rerun, and leaves the original `proxy-targets` directory unchanged. A
successful report must show all uniquely sourced recoveries used and no unused
recoverable boundaries before the recovered view is eligible for a later join.

After the recovered view passes its quality check, run the resumable join:

```python
!tradingbot-data proxy-join \
  --feature-dir "/content/drive/MyDrive/tradingbot-data-audit/feature-views" \
  --target-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-targets-recovered-v1" \
  --audit-output-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-join-audit-v1" \
  --model-output-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-model-view-v1" \
  --output-report "/content/drive/MyDrive/tradingbot-data-audit/proxy-join-v1.json"
```

The join checkpoints one day at a time, stops on duplicate
`window_start_utc` keys, preserves invalid/unmatched rows in the audit view,
and writes only eligible rows to the model view. The initial model columns are
`return_1s`, `return_1m`, `volatility_1m`, plus the label and proxy-source
metadata; target prices and target receipt times are not model columns.

Then run the proxy model-view quality review:

```python
!tradingbot-data proxy-review \
  --audit-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-join-audit-v1" \
  --model-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-model-view-v1" \
  --output-report "/content/drive/MyDrive/tradingbot-data-audit/proxy-model-review-v1.json" \
  --excluded-output "/content/drive/MyDrive/tradingbot-data-audit/proxy-model-excluded-v1.csv"
```

This read-only review reports label balance, finite numeric feature statistics,
chronological key validity, proxy-label provenance, and row-level exclusion
reasons. It does not train a model.

Then build the durable chronological proxy split report:

```python
!tradingbot-data proxy-split \
  --model-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-model-view-v1" \
  --review-report "/content/drive/MyDrive/tradingbot-data-audit/proxy-model-review-v1.json" \
  --output-report "/content/drive/MyDrive/tradingbot-data-audit/proxy-split-v1.json" \
  --train-day-count 23
```

The report records per-day row counts and source hashes and verifies that all
training keys precede evaluation keys, with zero train/evaluation key overlap.
It does not copy rows or train a model.

Then run the first proxy baseline:

```python
!tradingbot-data proxy-baseline \
  --model-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-model-view-v1" \
  --split-report "/content/drive/MyDrive/tradingbot-data-audit/proxy-split-v1.json" \
  --review-report "/content/drive/MyDrive/tradingbot-data-audit/proxy-model-review-v1.json" \
  --output-dir "/content/drive/MyDrive/tradingbot-data-audit/proxy-baseline-v1"
```

The command fits a standardized logistic regression on training rows only and
evaluates once on the later evaluation days. It uses only
`return_1s`, `return_1m`, and `volatility_1m`; target prices, target receipt
times, labels, and other future-only fields are not model inputs. It writes a
joblib model, evaluation predictions, and a checksum-bearing JSON report. On a
rerun, it skips only when those outputs still match the same split report.
This is a Binance-proxy engineering result and must not be presented as the
final Polymarket research result.

The notebook then reloads the verified Drive artifacts into three human
checkpoints: a model-view data overview, a chronological split timeline, and a
baseline dashboard covering metrics, probability errors, the confusion matrix,
calibration, probability separation, and standardized coefficients. These
summary cells do not retrain the model or rescan raw data.

Feature CSV reuse is controlled by the feature implementation identity and each
day's raw-source SHA-256, not the global package version. A package-only change
for split/report work therefore reuses compatible feature outputs; a changed
raw archive rebuilds only that day; a feature algorithm or policy change must
publish a new feature identity and regenerate affected outputs.

For a private repository, authenticate through the approved Colab mechanism.
Do not place GitHub tokens in notebook cells or committed files.

## Historical 15-minute Binance direction slice

This slice deliberately does not rerun the completed recorder/archive workflow.
It uses package `0.9.0`, pinned at commit
`91507cf3303bc0a88977091c3601175b3acd21e4`, and is run through
`historical_binance_15m.ipynb`.

The notebook downloads independent BTCUSDT 1-minute klines for
`2026-06-29` through `2026-07-28` inclusive. The extra June 29 day supplies
lookback history; target rows cover June 30 through July 28 inclusive. The
downloader writes one CSV per UTC day and checkpoints after each day. The
dataset builder writes one 96-row audit CSV per target day and checkpoints
after each day. Both rerun safely from Google Drive after a Colab interruption.

The model-ready view contains the twelve accepted short-term features and label
metadata. It excludes target prices and target returns. The audit view retains
target details and invalid rows for review. The builder also writes a
chronological train/validation/holdout report and verifies unique, disjoint,
chronological model keys before publishing it.

The notebook currently proposes 20 training days, 4 validation days, and 5
final holdout days for the 29 target days. Treat those counts as a reviewable
experiment choice until the learner accepts them; they are not an official
Polymarket evaluation split. Do not train or trade from this notebook yet.

Run the notebook from top to bottom after a runtime reset. Its only durable
inputs and outputs are the Git revision and the Drive paths defined in its
cells. If the raw download or dataset build is interrupted, rerun the same
cell; do not delete checkpoints or start a second output directory.

## 2. Mount Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')
```

Keep these artifacts in Drive, not in the GitHub checkout:

```text
raw archives/
manifest.json
coverage_map.json
audit outputs/
```

## 3. Create the grouped-GZIP manifest

Run this once for a new archive collection. The output path should be in Drive.
The audit and policy versions should identify the reviewed package revision and
data-quality rules.

```python
!tradingbot-data manifest \
  --archive-dir "/content/drive/MyDrive/<project>/raw-archives" \
  --output "/content/drive/MyDrive/<project>/manifest.json" \
  --audit-version "tradingbot-data-0.4.1-<commit>" \
  --policy-version "data-quality-2026-08-14" \
  --layout grouped-gzip \
  --recursive
```

The command recognizes only authoritative raw Binance JSONL, Polymarket JSONL,
and recorder-log GZIP names as group members. Other GZIP files, such as derived
CSV exports, are recorded as ignored instead of becoming raw inputs. Missing
source roles remain explicit.

The command refuses to overwrite an existing manifest. Preserve the old one if
the input collection or processing identity changes.

## 4. Verify the coverage map

The map must explicitly identify the UTC midnight that each logical group
covers. For the current collection, the map and report have already been
created and verified. The maintained notebook validates their group identities
and UTC-midnight alignment before any derived work runs:

```json
{
  "2026-07-27": "2026-07-27T00:00:00Z"
}
```

The group ID is candidate grouping information, not coverage proof. The
coverage report must have compared observed receipt dates with candidate dates.
If coverage is ambiguous, malformed, missing, or spans multiple days, do not
run the batch until the scope is resolved. For a new collection, generate a
new report and map with a dedicated preflight before using this notebook; never
infer the day from an upload filename.

## 5. Run one group smoke test

Before the batch, process one timestamp-verified full-day candidate and persist
its output in Drive:

```python
!tradingbot-data audit \
  --manifest "/content/drive/MyDrive/<project>/manifest.json" \
  --archive "<group-id>" \
  --day-start "<verified-UTC-midnight>" \
  --archive-root "/content/drive/MyDrive/<project>/raw-archives" \
  --output-dir "/content/drive/MyDrive/<project>/audit-outputs"
```

`--archive` retains its legacy option name but accepts a schema-v2 group ID.
Verify the manifest status, output existence, and output checksum before
starting the batch.

## 6. Run the resumable batch audit

```python
!tradingbot-data batch \
  --manifest "/content/drive/MyDrive/<project>/manifest.json" \
  --coverage-map "/content/drive/MyDrive/<project>/coverage_map.json" \
  --archive-root "/content/drive/MyDrive/<project>/raw-archives" \
  --output-dir "/content/drive/MyDrive/<project>/audit-outputs"
```

The runner processes one group at a time. It checks the selected Binance raw
checksum, writes
the audit output, verifies the output checksum, and only then marks the record
`completed`. If Colab stops, rerun the same command. Use `--retry-failed` only
after reviewing the recorded error. Use `--recover-running` only after
confirming that no other runner is active.

## Safety Rules

- Never commit raw archives, credentials, manifests containing sensitive paths,
  or large audit outputs to GitHub.
- Never silently overwrite a manifest or prior audit result.
- Never infer a recording day from an upload filename.
- A verified `completed` record may be skipped; any inconsistent status/output
  pair requires review or reprocessing.
- Keep proxy targets separate from official Chainlink-labeled research data.
