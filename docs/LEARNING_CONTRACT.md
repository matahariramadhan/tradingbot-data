# Learning Contract

Status: Authoritative for pedagogy  
Last updated: 2026-08-13

## Learner Model

The student learns best through an abstraction-first, top-down, spiral process.
The preferred starting point is a usable end-to-end system that makes the whole
problem visible. Depth is added iteratively after the student has practical
context and curiosity about a component.

The student is not required to implement every component from scratch before
using it.

## Default Learning Cycle

For each project slice:

1. Show where the slice fits in the end-to-end system.
2. Use a mature library, SDK, framework, or service abstraction where practical.
3. Make the slice runnable and observable early.
4. Explain the abstraction's inputs, outputs, responsibility, assumptions, and
   important failure modes.
5. Use it in a real project experiment.
6. Follow demonstrated limitations or the student's curiosity one layer deeper.
7. Reimplement a lower-level part only when that exercise has a clear learning
   purpose or solves a project problem.

This cycle may revisit the same component several times at increasing depth.

## Implementation Policy

The default is to compose reliable abstractions, not recreate infrastructure or
algorithms for their own sake. Examples include dataframe libraries, established
ML implementations, WebSocket clients, database drivers, plotting packages, and
evaluation utilities.

Small from-scratch implementations are appropriate when they illuminate a core
idea—for example, a simple expected-value calculation, baseline trading rule, or
chronological split—or when the student explicitly asks to go deeper.

### Mechanical Work

Do not require manual transcription, formatting, or repetitive boilerplate when
the concept can be demonstrated clearly with an example. The instructor
should handle trivial mechanics and use the learner's effort for reasoning,
design choices, interpretation, leakage detection, debugging, and meaningful
implementation decisions.

Advanced abstractions are still earned by project need. Abstraction-first does
not mean complexity-first or black-box acceptance.

## Top-Down Guardrail

Before asking implementation-level questions, the instructor must show the
current slice in the whole system, explain why it matters to the current phase,
identify its inputs and outputs, and state the decision or gate it supports.
Skip low-level bookkeeping questions unless they affect an important design,
failure mode, or the student's understanding. Descend into field names and
status details only after the student understands the component's role.

## Question Selection

Do not repeat questions whose underlying concept the student has already
demonstrated reliably. Revisit a concept only when it is genuinely new, tied to
an important design decision, previously answered incorrectly, explicitly
identified by the student as uncertain, or requested as spaced review. A review
question should test transfer or interpretation rather than repeat an obvious
definition.

## Durable Update Batching

The instructor should separate question cadence from file-write cadence. Ask
small batches of two or three questions so the student can think actively, but
do not edit durable records after every answer. Accumulate related answers and
write one grouped update after roughly five to ten meaningful review questions
or one coherent lesson section, whichever comes first.

Write immediately only when necessary to preserve an accepted project decision,
a material code/evidence/state change, an explicit pause, or another fact that
would be risky to lose. Retake history should be appended as a dated batch,
not as one file edit per question.

## Evidence of Learning

Learning is demonstrated when the student can increasingly:

- explain the component's role in the complete system;
- trace important inputs into outputs;
- interpret experiment results;
- identify assumptions, leakage risks, and failure modes;
- compare reasonable alternatives;
- decide when deeper implementation knowledge is useful.

Reimplementing the component is optional unless the student chooses it as a
learning objective.

## Relationship to the Project Charter

This contract controls how the project is taught and built. It does not change
the goals, research standards, phases, or safety principles in `instruction.md`.
