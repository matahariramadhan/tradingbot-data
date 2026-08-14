# Evidence: 2026-08-14 Archive Audit Runner Reproduction

Status: Point-in-time local end-to-end reproduction  
Audit date: 2026-08-14  
Scope: Manifest-controlled one-archive audit and resumable batch behavior

## Method

The local manifest was created with
`scripts/build_archive_manifest.py`, then one archive was processed with
`scripts/run_archive_audit.py` using:

```text
archive = drive-download-20260810T091218Z-1-001.zip
day_start = 2026-07-27T00:00:00Z
duration_seconds = 86400
audit_version = binance-audit-v1
policy_version = data-quality-2026-08-14
```

The batch runner was then run with an explicit coverage map. A second normal
batch run was used to test the completed-entry verification and skip path. An
empty coverage map was used to verify that the batch runner refuses to guess a
day start.

## Observed

- The archive ended in manifest status `completed`.
- The recorded audit-output SHA-256 was
  `9d0cc280ac6f959da874d2ee18ccd137f3554b3b04c2864c12e87e3a70479f2e`.
- The manifest checksum matched the actual output file checksum.
- The audit result contained 10,092,865 scanned records and 0 malformed JSON
  records.
- It contained 85,409 closed klines in total and 85,408 closed klines inside
  the requested UTC day.
- The strict in-day audit reported 992 missing starts, 0 duplicate starts, and
  6 gap events.
- A normal batch rerun reported the completed output as verified and skipped
  the archive.
- A batch run without a coverage-map entry exited with an error stating that
  it would not guess the timestamp.
- A coverage-map entry at `2026-07-27T00:05:00Z` was rejected because audit-day
  starts must be aligned to UTC midnight.
- Four focused workflow unit tests passed for hashing, manifest lookup,
  completed-output verification, and coverage-map validation.

## Consequence

The project now has a manifest-controlled single-archive runner at
`scripts/run_archive_audit.py` and a multi-archive orchestrator at
`scripts/run_archive_batch.py`. The runner writes a versioned output, records
its checksum, and marks `completed` only after the output and manifest update
are successful.
