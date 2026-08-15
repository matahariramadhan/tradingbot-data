# Stage-Specific Feature Provenance

Date: 2026-08-15

The previous notebook reused feature CSVs only when the entire package revision
and package version matched. That made an unrelated change, such as adding a
split report, trigger another expensive scan of all raw archives.

Package `0.7.1` changes the feature reuse contract. Feature outputs now carry
the dedicated implementation identity
`feature-view-2026-08-15-net-return-v1`, and the notebook compares that identity
instead of the global package version. A genuine feature algorithm or policy
change must bump this identity; unrelated package and notebook changes do not.

The compatibility function recognizes the already verified corrected feature
outputs produced by package `0.6.1` at commit
`a3e038a648ed8d182377147eddd64742bfc50495`, so the next Colab run does not
rescan the raw archives merely because the split command was added.

The local suite passes 25 tests. The package and notebook changes are in
commit `7c70fb2435865759fef231170da7e87eea1aa010`; remote execution is the
next verification step.
