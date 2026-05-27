---
title: "feat: gate JSON checked_at and git_head audit fields"
type: feat
status: completed
date: 2026-05-24
origin: docs/gate-results/README.md
---

# feat: gate JSON checked_at and git_head audit fields

## Problem

Persisted gate JSON (`--write-summary`) lacks when the check ran and which `main` commit was verified, limiting audit value for workflow hygiene.

## Requirements

- R1. Gate JSON adds `checked_at` (UTC ISO-8601) and `git_head` (short SHA, empty if unknown).
- R2. `AGENTS.md` documents `--write-summary` and `docs/gate-results/`.
- R3. `README.md` mentions optional `--write-summary`.
- R4. Live `agent_gate.sh` run; update `SPACE_RECOVERY` last gate; push.

## Implementation units

- U1. `verify_hosted_space.sh` JSON fields + doc sync.
- U2. Live verification.

## Out of scope

- CI changes
- Unit tests
