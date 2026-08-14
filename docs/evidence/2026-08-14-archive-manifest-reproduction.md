# Evidence: 2026-08-14 Archive Manifest Reproduction

Status: Point-in-time local reproduction  
Audit date: 2026-08-14  
Scope: Initial checksum-bearing archive manifest generator

## Method

The command was run from the repository root:

```text
python3 scripts/build_archive_manifest.py \
  --archive-dir data/raw/archives \
  --output /tmp/tradingbot_manifest.json \
  --audit-version binance-audit-v1 \
  --policy-version data-quality-2026-08-14
```

The generator hashes each ZIP in streaming chunks and writes the manifest
atomically. It refuses to overwrite an existing manifest path.

## Observed

- One archive was found and recorded with status `pending`.
- Archive filename:
  `drive-download-20260810T091218Z-1-001.zip`
- Archive size: `449175273` bytes.
- Archive SHA-256:
  `a0e3500f4f08a5f43fe7236f4defaca98ef552fce12d77dc1b5024fe3868dd9c`
- Audit version: `binance-audit-v1`.
- Policy version: `data-quality-2026-08-14`.
- A second run using the same output path exited with an overwrite refusal.

## Consequence

The project now has a safe initial manifest generator at
`scripts/build_archive_manifest.py`. Updating processing status and attaching
verified audit outputs remains a separate runner responsibility; the generator
does not mark an archive completed.
