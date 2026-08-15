# Net One-Minute Return Feature Fix

Date: 2026-08-15

The remote proxy model-view review exposed that the feature-view builder used
the latest one-second return as `return_1m`. The accepted policy requires the
net return across the complete 60-second lookback.

The builder now computes:

```text
return_1m = (last_close - first_close) / first_close
```

The package version is `0.6.1`, committed and pushed at
`a3e038a648ed8d182377147eddd64742bfc50495`.

A regression test constructs a valid lookback whose final one-second movement
differs from its net 60-second movement. The local suite passes all 22 tests.
The existing remote feature, join, and review outputs remain preserved as
pre-fix evidence. They must be regenerated or invalidated by provenance before
the proxy view is used for training or evaluation.
