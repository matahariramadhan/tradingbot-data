# Proxy Model-View Quality Review Implementation

Date: 2026-08-15

The next Phase 1 gate is now implemented as `tradingbot-data proxy-review`.
It reads the persisted audit join and per-day model-ready view, rejects
duplicate canonical `window_start_utc` keys, verifies exact model columns,
checks `UP`/`DOWN` labels and `binance_proxy` provenance, validates finite
numeric feature values, checks chronological ordering, and writes excluded
rows with their eligibility reasons.

The review is a read-only analysis of derived views. It does not train a model,
modify raw data, or modify the audit/model CSVs. Package version in the working
tree is `0.6.0`; the complete local test suite passes with `21` tests. Colab
integration and remote execution are the next steps.
