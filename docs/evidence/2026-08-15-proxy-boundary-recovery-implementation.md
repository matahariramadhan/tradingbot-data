# Proxy Boundary-Recovery Implementation

Date: 2026-08-15

## Scope

The project now has a separate `proxy-recover` implementation for applying
uniquely sourced observations from
`proxy-boundary-recovery-v1.json`. It reads the existing proxy-target CSVs,
writes a separate recovered-view directory, preserves the original inputs, and
checkpoints after each UTC-day CSV with an output SHA-256 checksum.

The unresolved July 28 boundary is not synthesized. Ambiguous source entries
also stop the recovery report in review status.

## Local validation

- The complete local unittest suite passed: `15` tests.
- The recovery-specific test verifies the recovered end price, `UP` label,
  late-start quality flag, and preserved input bytes.
- A second recovery invocation skips the already verified output, confirming
  resumable behavior.
- The package command is `tradingbot-data proxy-recover`.

The implementation is currently uncommitted and unreleased. Colab must not use
it until a reviewed package revision is published and the notebook is repinned
to that revision.

## Post-commit status

The implementation and its tests were committed locally as
`6f5a0873b28024d62a72eb9f2411e79e9b299612`. The commit has not yet been pushed,
so the current remote Colab checkout cannot use it.
