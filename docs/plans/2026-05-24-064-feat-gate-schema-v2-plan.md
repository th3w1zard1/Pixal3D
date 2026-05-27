---
title: "feat: gate schema pixal3d-agent-gate/2"
type: feat
status: completed
date: 2026-05-24
origin: docs/gate-results/README.md
---

# feat: gate schema pixal3d-agent-gate/2

## Problem

`pixal3d-agent-gate/1` predates `checked_at` and `git_head`. Bumping the schema version signals the stable audit field set and gives agents a committed reference shape.

## Requirements

- R1. Gate JSON uses `schema_version: "pixal3d-agent-gate/2"`.
- R2. Add `docs/gate-results/example.json` (documented sample, not live output).
- R3. Update docs referencing `/1` to `/2`.
- R4. Live `agent_gate.sh` run; push to `github` and `origin`.

## Implementation units

- U1. Script + example + doc sync.
- U2. Live verification.

## Out of scope

- CI validation of gate JSON
- Unit tests
