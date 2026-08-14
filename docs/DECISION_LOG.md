# Decision Log

Status: Authoritative chronological index  
Last updated: 2026-08-14

This file records that durable decisions were accepted and points to their
canonical definitions. It does not restate those definitions.

| ID | Date | Decision | Canonical location |
| --- | --- | --- | --- |
| D-001 | 2026-08-11 | Treat the original project instruction as immutable | `AGENTS.md` under **Immutability** |
| D-002 | 2026-08-11 | Partition documentation authority by subject | `AGENTS.md` under **Authority Map** |
| D-003 | 2026-08-11 | Use an abstraction-first, top-down, spiral learning approach | `docs/LEARNING_CONTRACT.md` |
| D-004 | 2026-08-11 | Make the root README the first gate for every AI agent | `README.md` under **First Gate** |
| D-005 | 2026-08-11 | Keep durable lesson progress separate from current project state | `docs/LEARNING_PROGRESS.md` |
| D-006 | 2026-08-11 | Prioritize meaningful reasoning over trivial manual transcription exercises | `docs/LEARNING_CONTRACT.md` under **Mechanical Work** |
| D-007 | 2026-08-11 | Do not silently fill missing market data; require consecutive klines for `return_1s` | `docs/DATA_QUALITY_POLICY.md` |
| D-008 | 2026-08-11 | Retain invalid rows for audit and exclude them only from the first model view | `docs/DATA_QUALITY_POLICY.md` |
| D-009 | 2026-08-11 | Validate features independently and require all model features to be valid | `docs/DATA_QUALITY_POLICY.md` |
| D-010 | 2026-08-11 | Use a complete 60-second one-second lookback for the initial `return_1m` feature | `docs/DATA_QUALITY_POLICY.md` |
| D-011 | 2026-08-11 | Define initial `volatility_1m` as population standard deviation over the same 60 returns | `docs/DATA_QUALITY_POLICY.md` |
| D-012 | 2026-08-11 | Require the official Chainlink result for the supervised target; never substitute Binance and retain unlabeled rows for audit | `docs/DATA_QUALITY_POLICY.md` |
| D-013 | 2026-08-11 | Keep large raw archives and heavy data/model computation remote; use the local laptop for development, small fixtures, and compact artifacts | `docs/STATE.md` under **Available Artifacts** |
| D-014 | 2026-08-11 | Keep meaningful lesson questions in a separate durable review bank for refresher and retake sessions | `docs/REVIEW_QUESTIONS.md` |
| D-015 | 2026-08-11 | Batch durable lesson writes instead of editing records after every answer; flush at coherent checkpoints and explicit pauses | `docs/LEARNING_CONTRACT.md` under **Durable Update Batching** |
| D-016 | 2026-08-11 | Apply a strict top-down guardrail before descending into implementation bookkeeping | `docs/LEARNING_CONTRACT.md` under **Top-Down Guardrail** |
| D-017 | 2026-08-11 | Use a separate Binance-proxy target for engineering validation while reserving official Chainlink labels for final Polymarket research claims | `docs/DATA_QUALITY_POLICY.md` |
| D-018 | 2026-08-13 | Start with a clean five-minute Binance proxy where decision time equals window start, then add the separate Polymarket-faithful in-window task | `docs/DATA_QUALITY_POLICY.md` |
| D-019 | 2026-08-13 | Do not repeat reliably demonstrated concepts; revisit only for new decisions, mistakes, uncertainty, or requested spaced review | `docs/LEARNING_CONTRACT.md` under **Question Selection** |
| D-020 | 2026-08-13 | Define proxy boundaries using completed one-second closes immediately before the window start and five-minute end, with the start observation timely at decision time | `docs/DATA_QUALITY_POLICY.md` |
| D-021 | 2026-08-14 | Clarify that target-boundary receipt time is not a target-validity cutoff: late boundary observations may construct an offline historical label, while decision-time features still require receipt by the cutoff | `docs/DATA_QUALITY_POLICY.md` |
| D-022 | 2026-08-14 | Use one complete archive as the resumable audit unit, and mark it `completed` only after its audit output and metadata are saved and verified | `docs/STATE.md` under **Archive Processing Contract** |
| D-023 | 2026-08-14 | Treat manifest status and actual output state as a consistency check: never skip a `completed` entry without a verified output, and never trust output from an `interrupted` or `failed` entry automatically | `docs/STATE.md` under **Archive Processing Contract** |
| D-024 | 2026-08-14 | Require an explicit UTC coverage start for each archive audit; never infer the recording day from an archive upload filename | `docs/STATE.md` under **Archive Processing Contract** |
| D-025 | 2026-08-14 | Distribute the data-foundation workflow as an installable GitHub package for Colab, while keeping raw data and audit outputs in Google Drive | `docs/COLAB_RUNBOOK.md` |

New entries are append-only. If a decision is superseded, append a new entry and
link both entries to the new canonical definition; do not rewrite the old row.
