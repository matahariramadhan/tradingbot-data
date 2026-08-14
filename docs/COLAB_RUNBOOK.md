# Google Colab Runbook

This is the execution handoff for the remote archive audit. Colab runs the
package; Google Drive stores raw archives, manifests, coverage maps, and audit
outputs. The repository must contain code only.

## 1. Clone a pinned revision

Use the repository URL and a reviewed commit or tag supplied by the project
owner:

```python
!git clone https://github.com/<owner>/<repository>.git /content/tradingbot_v2
%cd /content/tradingbot_v2
!git checkout <reviewed-commit>
!pip install .
!tradingbot-data --help
```

For a private repository, authenticate through the approved Colab mechanism.
Do not place GitHub tokens in notebook cells or committed files.

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
  --audit-version "tradingbot-data-0.2.0-<commit>" \
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
covers:

```json
{
  "2026-07-27": "2026-07-27T00:00:00Z"
}
```

The group ID is candidate grouping information, not coverage proof. Verify the
map from timestamps inside the raw inputs. If coverage is ambiguous or spans
multiple days, mark it for review and do not run that group until its scope is
resolved.

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
