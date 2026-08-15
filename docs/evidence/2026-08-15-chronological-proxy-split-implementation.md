# Chronological Proxy Split Implementation

Date: 2026-08-15

Package `0.7.0` adds the `tradingbot-data proxy-split` command. It reads the
reviewed per-day model CSVs and does not copy or modify their rows.

The command requires a completed proxy model-view review report and an explicit
training-day count. It verifies:

- model filenames are valid UTC days and match the review report;
- every `window_start_utc` belongs to its declared day;
- per-day and global keys are chronological and unique;
- training and evaluation key intersection is zero;
- the last training key is earlier than the first evaluation key; and
- total model rows match the completed quality-review report.

The report records the train/evaluation day lists, per-day row counts, source
CSV SHA-256 hashes, review-report SHA-256, and verification results. The
initial accepted configuration uses 23 training days and 6 evaluation days.

The implementation is committed and pushed at
`45a317e9d215d935a496ed6ce0a9e5ff3ac35d45`. The local test suite passes all 24
tests. Remote execution is the next step.
