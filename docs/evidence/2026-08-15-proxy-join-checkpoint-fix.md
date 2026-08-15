# Proxy-Join Stale-Checkpoint Fix

Date: 2026-08-15

The first proxy join wrote outputs using the incorrect raw-string timestamp
key. Because the checkpoint originally trusted matching input/output hashes
without identifying the join implementation, a rerun could have skipped those
incorrect outputs after the key logic was fixed.

Package `0.5.2` adds `join_implementation_version` to the persisted report and
requires it to match before a day can be skipped. Reports from the earlier
implementation are therefore safely treated as stale and rebuilt from the
existing Drive source views. No raw data or original target files are deleted.

The fix is committed at
`420041347f78215cf71b9f8d76852968eb6374fd` and the notebook is being repinned
to it. Local tests pass; the corrected join has not yet run remotely.
