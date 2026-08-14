# Evidence: 2026-08-14 Grouped-GZIP Workflow Reproduction

Status: Local implementation verification  
Reproduction date: 2026-08-14  
Scope: Manifest schema v2, direct-GZIP Binance audit compatibility, legacy ZIP
compatibility, and installable package

## Method

The workflow was exercised with focused synthetic fixtures for direct GZIP
candidate-date groups and the legacy ZIP layout. The package was also built as
version `0.2.0`, installed into an isolated environment, and invoked through
its installed `tradingbot-data` entry point.

## Observed

- Manifest schema v2 identifies each present raw group member with its path,
  byte size, and SHA-256 checksum.
- Missing source roles remain explicit and do not prevent the narrower Binance
  day-coverage audit from completing when its Binance input is valid.
- Derived CSV GZIP files are recorded as ignored and do not contribute to raw
  group identity.
- The Binance streaming reader accepts direct `.jsonl.gz` input and the legacy
  ZIP sample layout.
- Ten focused workflow tests passed, including direct script invocation.
- The `tradingbot-data` version `0.2.0` wheel built, installed in an isolated
  environment, reported version `0.2.0`, and exposed its CLI help.

## Scope Limit

This reproduction used local fixtures and the existing local ZIP sample. It
did not read, hash, or audit the 10.75 GiB Google Drive collection. A pinned
Colab installation and one-group Drive smoke test remain required.

## Consequence

The local workflow is ready for a committed package checkpoint and remote
one-group validation. It is not evidence that the 30-day collection has valid
UTC coverage or passes the research-readiness gate.
