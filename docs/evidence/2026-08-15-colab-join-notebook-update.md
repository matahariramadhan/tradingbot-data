# Colab Proxy-Join Notebook Update

Date: 2026-08-15

The Phase 1 notebook now has 29 cells and 19 code cells. It pins package
`0.5.0` at commit
`d8df657d9d59a4eb34365b3717f05758fc0012a0` and adds the resumable
`proxy-join` step.

The new step writes a per-day audit join and a per-day model-ready proxy view,
then verifies duplicate-key handling, 288-row audit shape, eligibility counts,
proxy label source, and exclusion of target price/receipt columns from the
model columns.

Local notebook JSON/code validation passed, and the complete local test suite
passed with 19 tests. The updated notebook has not yet run remotely.
