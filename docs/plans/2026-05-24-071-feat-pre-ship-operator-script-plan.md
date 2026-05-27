---
title: "feat: pre_ship.sh and workflow hygiene index"
type: feat
status: completed
date: 2026-05-24
origin: docs/post-recovery.md
---

# feat: pre_ship.sh and workflow hygiene index

## Problem

Operators run `workflow_hygiene.sh` then `agent_gate.sh` manually. PR #36 (plans 067–070) is CI-green and mergeable; hygiene docs are split across three README trees.

## Requirements

- R1. `scripts/pre_ship.sh` runs `workflow_hygiene.sh` then `agent_gate.sh`, forwarding `--parity` to hygiene and `--url` / `--write-summary` to the agent gate.
- R2. `docs/workflow-hygiene.md` indexes gate, generation manifest, and adapter policy artifacts.
- R3. Remove duplicate workflow YAML CI step (covered by `workflow_hygiene.sh` after PyYAML install).
- R4. Live `./scripts/pre_ship.sh` (or hygiene + gate); merge PR #36 if mergeable; push `main` to `github` and `origin`.

## Out of scope

- `app.py` runtime changes
- `--generate` in pre_ship
