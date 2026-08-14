# BTC → Polymarket ML Research Project

## First Gate

Every AI agent must read this file first when entering the workspace. This file
only controls onboarding and document navigation; it does not define project,
learning, or implementation policy.

Before analyzing, planning, editing, or running project tasks, read in this
order:

1. `AGENTS.md` — documentation authority and operating rules
2. `instruction.md` — immutable project charter
3. `docs/LEARNING_CONTRACT.md` — authoritative learning approach
4. `docs/STATE.md` — current status, constraints, and next work
5. Evidence or decision records linked by `docs/STATE.md` that are relevant to
   the task

Do not substitute conversation memory for this reading sequence. After it is
complete, follow the ownership and update rules in `AGENTS.md`.

When an AI session is taking over instruction or resuming after context
compaction, also read `docs/INSTRUCTOR_HANDOFF.md`. It is a portable teaching
and resume prompt; the documents listed above remain authoritative for their
respective subjects.

For a project-independent teaching protocol that can be reused elsewhere, use
`docs/INSTRUCTOR_PROMPT.md`. `docs/INSTRUCTOR_HANDOFF.md` is the adapter for
this project only. The current master-instructor learning summary is in
`docs/MASTER_INSTRUCTOR_REPORT.md`.

The installable data-audit package and Colab execution instructions are in
`pyproject.toml` and `docs/COLAB_RUNBOOK.md`.
