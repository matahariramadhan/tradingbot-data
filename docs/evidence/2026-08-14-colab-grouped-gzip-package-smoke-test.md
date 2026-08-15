# Evidence: 2026-08-14 Colab Grouped-GZIP Package Smoke Test

Status: User-reported remote reproduction
Reproduction date: 2026-08-14
Scope: Pinned grouped-GZIP revision, package upgrade, and CLI discovery in
Google Colab

## Method

The existing Colab checkout fetched GitHub, checked out revision
`03abbb745cc7919087b2e56607bb6bdf4d582a23`, force-reinstalled the repository,
printed the installed package version, and invoked `tradingbot-data --help`.

## Observed

- Git resolved the detached checkout to the requested revision with subject
  `feat: support grouped gzip data audits`.
- The wheel built successfully and package version `0.1.0` was replaced by
  version `0.2.0`.
- The installed module reported version `0.2.0`.
- The CLI exposed `manifest`, `audit`, `batch`, `day-audit`, `proxy-targets`,
  `snapshot`, and `inspect`, using the revised group-oriented descriptions.
- No manifest creation or raw-data audit occurred in this checkpoint.

## Consequence

The pushed grouped-GZIP package revision can be installed and invoked in
Colab. The next remote checkpoint is manifest creation followed by inspection
and one timestamp-verified group audit.
