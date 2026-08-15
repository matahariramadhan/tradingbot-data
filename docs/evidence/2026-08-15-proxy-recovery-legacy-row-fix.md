# Proxy Recovery Legacy-Row Fix

Date: 2026-08-15

## Observed failure

The Colab recovery cell stopped while processing the existing target row for
`2026-06-30T23:55:00.000Z` with:

```text
cannot recover an end boundary without a valid start
```

The original proxy-target builder emitted an otherwise blank invalid row when
either boundary was missing. Therefore a row classified as
`missing_end_boundary` could lose its valid start boundary in the derived CSV.
This was a derived-output bug; it did not show that the raw start observation
was absent.

## Correction

The proxy-target builder now preserves every boundary that is uniquely present,
even when the other boundary is missing. Recovery also accepts the legacy CSV
shape by checking the immediately preceding row: its end observation must have
the exact interval identity required for the current row's start, plus a price
and receipt timestamp. If that check fails, recovery records the row for review
instead of inventing a value or aborting the entire batch.

The original target directory remains unchanged. Recovered output continues to
be written to the separate recovered-target directory.

## Local validation

- Package version in the working tree: `0.4.1`.
- The unittest suite passed: `17` tests.
- Compilation of `scripts/` and `tradingbot_data/` passed.
- `git diff --check` passed.
- A regression test covers the exact legacy case: a missing end on the final
  window with the start fields blank, repaired from the preceding row's exact
  end boundary.

The corrected package has not yet been published or rerun in Colab. No new
Drive recovery count is claimed by this record.
