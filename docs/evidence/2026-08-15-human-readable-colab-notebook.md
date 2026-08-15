# Human-Readable Colab Notebook

Date: 2026-08-15 UTC

## Motivation

The earlier notebook was a strong reproducible execution runbook but exposed
important results mainly as dictionaries and text. That was efficient for
machine verification and difficult for a human learner to inspect as a whole.

## Implementation

Package `0.8.1` at commit
`63cbd647953d203abab23ccd5d27c9a87aec3d4a` adds Matplotlib to the optional
training environment without changing the baseline algorithm. The notebook is
expanded from 35 to 41 cells and adds three self-contained visual checkpoints:

1. model-ready versus excluded rows by day, proxy-label balance, and the three
   feature distributions;
2. daily row counts with an explicit chronological training/evaluation
   boundary; and
3. model-versus-majority metrics, probability losses, confusion matrix,
   calibration, probability distributions by actual label, and standardized
   logistic coefficients.

Every visual cell reloads its required verified JSON or CSV artifacts from
Google Drive. It does not depend on an earlier cell's in-memory report object,
run a long computation, retrain the model, or rescan raw data.

## Local Verification

- The notebook is valid JSON with 41 uniquely identified cells.
- All 25 code cells compile.
- Structural tests require all three visualization cells and their direct Drive
  artifact loading.
- The complete local suite passes 30 tests.
- Package `0.8.1` builds and installs with matching distribution and module
  versions.

## Scope Limit

The Drive-backed plot cells were not rendered locally because the remote
artifacts are not present in this workspace. Their first Colab rendering is the
next verification checkpoint. The existing baseline output remains eligible
for reuse because its implementation identity is unchanged.
