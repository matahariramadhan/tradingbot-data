# Colab Recovery Fix Publication

Date: 2026-08-15

The legacy proxy-boundary recovery failure was fixed in package version
`0.4.1`, commit
`41fdff5619d4c00389628eb526f9f66ac19f3650`.

The maintained notebook and Colab runbook now pin this exact revision. The
notebook still uses the existing Drive boundary report and recovery checkpoint;
no raw archive rescan is required. The original proxy-target directory remains
read-only, and recovery continues to write a separate recovered view.

The commits are pushed to `origin/main`. The remote rerun has not yet occurred,
so no recovered target count is claimed here.
