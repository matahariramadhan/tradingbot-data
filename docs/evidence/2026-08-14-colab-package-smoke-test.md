# Evidence: 2026-08-14 Colab Package Smoke Test

Status: User-reported remote reproduction  
Reproduction date: 2026-08-14  
Scope: Fresh Google Colab runtime, pinned Git revision, package installation,
and CLI discovery

## Method

The repository was cloned from GitHub into a fresh Colab runtime, checked out
at revision `43405c9`, installed with `pip install .`, and invoked through
`tradingbot-data --help`.

## Observed

- Git checkout resolved to
  `43405c960c8fbc719cc67b6003731b0b38d2af47`.
- The checkout entered detached-HEAD state at the requested revision.
- The `tradingbot-data` wheel built and version `0.1.0` installed successfully.
- The CLI exposed the expected commands: `manifest`, `audit`, `batch`,
  `day-audit`, `proxy-targets`, `snapshot`, and `inspect`.
- No archive processing or Google Drive mutation occurred in this checkpoint.

## Consequence

The reviewed package revision can be cloned, installed, and invoked in Colab.
The next remote checkpoint is to mount Google Drive, identify the archive and
persistent-output directories, and perform the manifest/single-archive smoke
test without modifying raw archives.

