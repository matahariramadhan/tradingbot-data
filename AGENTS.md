# Project Operating Guide

This file defines where authoritative project information lives and how it is
maintained. `README.md` is the sole onboarding gate and owns the mandatory
reading sequence.

## Authority Map

| Document | Sole responsibility |
| --- | --- |
| `README.md` | First-session gate and mandatory document navigation |
| `instruction.md` | Project purpose, research principles, phases, and intended learning outcomes |
| `docs/LEARNING_CONTRACT.md` | The student's learning style and the default teaching/implementation approach |
| `docs/STATE.md` | Current project status, constraints, open questions, and immediate next work |
| `docs/DECISION_LOG.md` | Chronological index of accepted durable decisions and their canonical locations |
| `docs/LEARNING_PROGRESS.md` | Durable lesson progress, misconceptions, accepted understanding, and next teaching checkpoint |
| `docs/REVIEW_QUESTIONS.md` | Reusable review questions, answer keys, and retake history |
| `docs/DATA_QUALITY_POLICY.md` | Accepted rules for validating, preserving, and excluding market-data observations |
| `docs/evidence/*.md` | Reproducible observations, measurements, audit scope, and supporting sources |

These documents are complementary rather than a single precedence stack. When
statements conflict, use the document that owns the subject. Treat a conflict
inside one subject as unresolved; record it in `docs/STATE.md` and ask the user
instead of silently choosing an interpretation.

Do not rely on conversation memory when an authoritative document covers the
same subject.

## Immutability

`instruction.md` is immutable. Never edit, reformat, rename, or append to it.
Clarifications about pedagogy belong in `docs/LEARNING_CONTRACT.md`. Project
choices belong in their subject-specific document and are indexed by
`docs/DECISION_LOG.md`.

## Documentation Rules

- Store each fact or rule in exactly one authoritative place.
- Link to authoritative content; do not duplicate its details elsewhere.
- Separate observations from inferences, design choices, hypotheses, and
  unknowns.
- Put exact measurements and their scope in an evidence file. Keep only their
  current consequence in `docs/STATE.md`.
- Record a decision only after the user accepts it or explicitly directs it.
- Use ISO dates. Use UTC for data timestamps unless a source requires another
  timezone.
- Never rewrite historical evidence to match a newer conclusion. Add a new
  evidence record and update the current state instead.

## Stateless Remote Runtime Rule

Treat Google Colab as a disposable, stateless runtime. Git is the durable code
store and Google Drive is the durable data, checkpoint, manifest, output, and
report store. A fresh runtime must be able to rerun the notebook's bootstrap
cells and reconstruct its context; downstream cells must fail clearly when
their prerequisites have not been run. No cell may depend on in-memory
progress surviving a runtime interruption. Long-running cells must checkpoint
at a meaningful work-unit boundary and skip previously verified units when
rerun. Follow the detailed contract in `docs/COLAB_RUNBOOK.md`.

## End-of-Work Update

After material work:

1. Update `docs/STATE.md` if current status, blockers, or next actions changed.
2. Add an evidence record if new measurements or external facts were established.
3. Add a decision-log entry if a durable decision was accepted.
4. Leave unrelated documents untouched.
