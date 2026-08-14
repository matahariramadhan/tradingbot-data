# Review Questions

Status: Durable refresher and retake bank  
Last updated: 2026-08-14

This file stores meaningful questions used during instruction. It is separate
from `docs/LEARNING_PROGRESS.md`: that file records demonstrated understanding,
while this file preserves questions for later review.

## How to Use

For a retake, answer the questions before reading the answer key. The instructor
can select a small batch of two or three questions. New answers should be
accumulated and recorded as one dated batch after roughly five to ten meaningful
questions or one coherent lesson section, not written after every answer.

Status values:

- `mastered-after-correction`: initially confused, then corrected;
- `mastered`: answered correctly;
- `pending`: not yet answered or needs another attempt.

## Questions

| ID | Review question | Original status |
| --- | --- | --- |
| RQ-001 | What is the prediction unit? | mastered |
| RQ-002 | What is the target label, and when is it known? | mastered |
| RQ-003 | Is `P(UP)=0.60` the same thing as the realized target? | mastered |
| RQ-004 | If a kline interval is complete but its receipt arrives after decision time, can it be used? | mastered |
| RQ-005 | What is a data gap? | mastered |
| RQ-006 | Why is the first return missing even when there is no data gap? | mastered |
| RQ-007 | Should missing market data be silently invented or filled? | mastered |
| RQ-008 | Should an invalid observation be deleted from the audit view? | mastered |
| RQ-009 | Does one invalid feature automatically invalidate every other feature? | mastered |
| RQ-010 | What is required for the initial 60-second aggregated features? | mastered |
| RQ-011 | What does deviation mean? | mastered |
| RQ-012 | What does standard deviation describe? | mastered |
| RQ-013 | For `100 → 101 → 100`, what is net return and what happens to volatility? | mastered-after-correction |
| RQ-014 | If recent return is negative and volatility is high, does that prove the market label will be `DOWN`? | mastered-after-correction |
| RQ-015 | With model probability `0.60` and ask `$0.68`, what is the raw edge and simple action? | mastered |
| RQ-016 | With model probability `0.75` and ask `$0.68`, is the edge positive, and does it guarantee a win? | mastered |
| RQ-017 | What does zero edge mean, and should a strictly-positive-edge strategy trade it? | mastered-after-correction |
| RQ-018 | If the settlement beginning and ending prices are equal, is the label `UP` or `DOWN`? | mastered |
| RQ-019 | Which source defines the official label: Binance or Chainlink? | mastered |
| RQ-020 | If official Chainlink data is missing, can Binance replace the label? What happens to the row? | mastered |
| RQ-021 | Can a row be eligible for a live prediction before its future label is known? Can it enter training? | mastered |
| RQ-022 | If heavy computation is remote, what belongs on the local laptop? | mastered |
| RQ-023 | What does a checksum verify in an archive manifest? | mastered-after-correction |
| RQ-024 | If an archive is completed and its checksum is unchanged, should it be processed again? | mastered |
| RQ-025 | If a remote runtime stops during processing, can that archive be trusted as complete? | mastered |
| RQ-026 | If the filename is unchanged but the checksum changes, should the old audit be silently overwritten? | mastered |
| RQ-027 | If the checksum is unchanged but the audit script changed, can the old audit be blindly reused? | mastered-after-correction |
| RQ-028 | What field records which version of the audit logic produced a result? | mastered |
| RQ-029 | If the data-quality policy changes while data and code stay the same, can the old result be blindly reused, and what field records the rules used? | mastered |
| RQ-030 | If one reproducibility identifier changes, must we always rerun, or is there a documented exception? | mastered |
| RQ-031 | What decision should the Phase 1 Data Readiness Gate make? | mastered-after-correction |
| RQ-032 | Why must we audit all 30 days before trusting model results? | mastered |
| RQ-033 | What kinds of problems could cause the Data Readiness Gate to fail? | mastered |
| RQ-034 | What can a Binance-proxy evaluation prove? | mastered |
| RQ-035 | What can a Binance-proxy evaluation not prove? | mastered-after-correction |
| RQ-036 | Why must every target record include `label_source`? | mastered |
| RQ-037 | Why should `label_definition` be stored separately from the label value? | mastered-after-correction |
| RQ-038 | If Binance and Chainlink produce different labels for the same window, should we combine them? | mastered |
| RQ-039 | What time boundary must target construction and feature construction respect? | mastered-after-correction |
| RQ-040 | Is future data forbidden when creating a historical target? | mastered |
| RQ-041 | Is future data forbidden as an input feature at decision time? | mastered |
| RQ-042 | What is the difference between the clean proxy task and the Polymarket-faithful in-window task? | mastered |
| RQ-043 | Which completed one-second closes define the first proxy window's start and end prices? | mastered |
| RQ-044 | Can a boundary observation received after decision time still define a historical target, and can it be used as a feature at that decision time? | mastered-after-correction |
| RQ-045 | What is the resumable work unit for the multi-day audit? | mastered |
| RQ-046 | When may an archive be marked `completed`? | mastered |
| RQ-047 | If a manifest says `completed` but its expected output is missing, may the archive be skipped? | mastered |
| RQ-048 | If an output exists but the manifest says `interrupted` or `failed`, may the output be trusted automatically? | mastered |
| RQ-049 | Why must the batch runner receive an explicit archive-to-UTC-day coverage map instead of inferring the day from the upload filename? | mastered |

## Answer Key

1. `RQ-001`: One five-minute BTC Up/Down market at a specified decision time.
2. `RQ-002`: The later official `UP` or `DOWN` result; it is known only after
   the market resolves.
3. `RQ-003`: No. `0.60` is a model probability; the realized target is one
   outcome, such as `UP` or `DOWN`.
4. `RQ-004`: No. Receipt/availability time must be at or before the decision
   cutoff.
5. `RQ-005`: A missing expected interval in an otherwise time-ordered sequence.
6. `RQ-006`: There is no previous observation with which to calculate a return.
7. `RQ-007`: No. Preserve the observation and flag the missing or invalid
   dependency.
8. `RQ-008`: No. Retain it in the raw/audit view; exclude it only from an
   explicit model view when required.
9. `RQ-009`: No. Feature validity is dependency-specific, but a model row needs
   every feature required by that model to be valid.
10. `RQ-010`: Sixty consecutive one-second intervals, with every required input
    complete, received by the cutoff, and valid.
11. `RQ-011`: The distance between a value and the average.
12. `RQ-012`: The typical distance of values from their average; it is not a
    future direction prediction and is nonnegative.
13. `RQ-013`: Net return is zero because the endpoints are equal; volatility is
    nonzero because the path moved in between.
14. `RQ-014`: No. It describes past movement and activity, not a guaranteed
    future outcome.
15. `RQ-015`: `0.60 - 0.68 = -0.08`; under the simple rule, do not buy UP.
16. `RQ-016`: The edge is `+0.07`; it is favorable expectation, not a guaranteed
    individual win.
17. `RQ-017`: Zero is neutral, neither positive nor negative. A strategy that
    requires strictly positive edge should not trade at zero, especially after
    costs.
18. `RQ-018`: `UP`, because the rule is end price greater than or equal to
    beginning price.
19. `RQ-019`: Chainlink BTC/USD defines the official label; Binance may provide
    predictive features but is not the settlement source.
20. `RQ-020`: No substitution. Retain the row for audit, but exclude it from
    labeled training and evaluation until the official target is recovered.
21. `RQ-021`: Yes for live prediction if decision-time inputs are valid and
    available; no for supervised training until the official label exists.
22. `RQ-022`: Code, documentation, tests, small fixtures, and compact reports or
    model artifacts—not the full heavy data workload.
23. `RQ-023`: The exact contents of the file; it detects whether the data changed
    even when the filename stays the same.
24. `RQ-024`: No, it can be skipped unless the audit version or policy changed.
25. `RQ-025`: No. It must be marked interrupted or otherwise unconfirmed and
    processed again.
26. `RQ-026`: No. Preserve the old result and create a new audit record for the
    changed contents.
27. `RQ-027`: No, not blindly. A changed audit implementation may produce a
    different result from the same raw data.
28. `RQ-028`: An audit version, script version, or Git commit identifier.
29. `RQ-029`: No. Record a policy version so the result can be traced to the
    exact validation rules used.
30. `RQ-030`: The conservative default is to create a new result. Reuse is
    acceptable only after deliberately verifying and documenting that the
    change is backward-compatible and cannot affect that result.
31. `RQ-031`: Whether the available data is trustworthy, correctly timed, and
    labeled well enough to support a research dataset.
32. `RQ-032`: A model's result depends heavily on the dataset, and one sample
    cannot establish whether problems affect the complete period.
33. `RQ-033`: Gaps, late or misaligned records, incomplete market coverage,
    missing official labels, or other source/integrity defects.
34. `RQ-034`: It can show that the feature, dataset, training, and evaluation
    pipeline works on a controlled proxy task.
35. `RQ-035`: It cannot establish the final research result for Polymarket's
    official outcome.
36. `RQ-036`: To distinguish a Binance proxy target from an official Chainlink
    target and prevent mixing their results.
37. `RQ-037`: It records how the value was generated, which makes the target
    interpretable and reproducible even though it is not a model feature.
38. `RQ-038`: No. Keep them separate because they represent different target
    sources and definitions.
39. `RQ-039`: Features must use only data available by decision time `t`; a
    historical target may use future data after `t`, but only as `y`, never as
    an input feature.
40. `RQ-040`: No. Future data is allowed to construct the historical target.
41. `RQ-041`: Yes. Future data must not be available to the model at decision
    time.
42. `RQ-042`: The clean proxy starts its five-minute target window at the
    decision time; the Polymarket-faithful task uses a fixed market window and
    may make the decision after that window has started. They are different
    prediction problems.
43. `RQ-043`: The close immediately before the window start and the close
     immediately before the five-minute end. Both are target-construction
     inputs, so their receipts may be later; the feature cutoff applies if a
     boundary value is considered as a model input.
44. `RQ-044`: Yes, it can still define the historical target when used only for
    offline target construction; no, it cannot be used as a feature at the
    earlier decision time because it was not available then.
45. `RQ-045`: One complete archive. The audit should not need to resume at an
    arbitrary raw-record position for the initial workflow.
46. `RQ-046`: Only after the audit output and its metadata have been saved and
    verified. Finishing the scan in memory is not enough.
47. `RQ-047`: No. The status and filesystem state disagree, so the entry must
    be investigated and the output verified or the archive reprocessed.
48. `RQ-048`: No. The output's provenance and contents must be verified, or the
    archive must be reprocessed before it can be trusted.
49. `RQ-049`: Because an upload filename identifies the transfer artifact, not
    necessarily the recording-day coverage. Inferring the day could audit the
    wrong UTC interval, so the scope must be supplied and verified explicitly.

## Retake Record

New attempts should be recorded below with the date, question IDs, the
student's answers, and whether the answer was correct, corrected, or still
pending. Do not erase the original status history.

### 2026-08-11 Retake Attempt

- `RQ-027`: The student answered `no`, followed by contradictory wording. The
  intended distinction was clarified: an old result cannot be reused as the
  result of changed audit code without rerunning.
- `RQ-028`: The student initially did not know, then correctly identified the
  audit/code version as the traceability field.
- `RQ-029`: The student correctly identified that a changed data-quality policy
  requires a policy-version field.
- `RQ-030`: The student correctly identified the conservative rerun default and
  the backward-compatible exception.
- `RQ-031`–`RQ-036`: The student completed the Data Readiness Gate and
  Binance-proxy evaluation checkpoint, including the distinction between
  pipeline validation and final research claims.
- `RQ-037`–`RQ-041`: The student completed the target-contract checkpoint,
  including the distinction between offline target construction and
  decision-time feature leakage.
- `RQ-042`: The student accepted the separate clean-proxy and
  Polymarket-faithful task design.
- `RQ-043`: The student accepted the exact proxy boundary-sampling rule.

### 2026-08-14 Target Boundary Timing Checkpoint

- `RQ-044`: The student answered that late data cannot be used by the model at
  decision time but can be used later to construct the historical label. The
  distinction was correct and the resulting policy was accepted as D-021.

### 2026-08-14 Archive Resumability Checkpoint

- `RQ-045`–`RQ-046`: The student selected one complete archive as the work
  unit and required saved, verified output and metadata before `completed`.
  These choices were recorded as D-022.

- `RQ-047`–`RQ-048`: The student correctly rejected trusting either a missing
  output for `completed` or an output from an `interrupted`/`failed` entry.
  This consistency rule was recorded as D-023.

### 2026-08-14 Coverage Map Checkpoint

- `RQ-049`: The student correctly identified that an upload filename identifies
  a transfer artifact, can be renamed, and does not prove recording-day scope.
  Ambiguous or multi-day coverage must be marked for review rather than guessed.
