---
title: "docs: sync SPACE_RECOVERY with workflow hygiene bundle"
type: docs
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# docs: sync SPACE_RECOVERY with workflow hygiene bundle

## Problem

`SPACE_RECOVERY.md` still cites plan 066 and `agent_gate.sh` only. Plans 067–071 landed on `main` (`881c031`) with `pre_ship.sh`, generation manifests, and adapter policy stubs, but the recovery runbook was not updated.

## Requirements

- R1. `SPACE_RECOVERY.md` documents `pre_ship.sh`, `workflow_hygiene.sh`, and links `docs/workflow-hygiene.md`; updates last-gate note for merge `881c031`.
- R2. `docs/adapters/policy.example.json` lists current rembg Hub models as `enabled: false` with `license_spdx` (documentation only).
- R3. `./scripts/pre_ship.sh` on `main`; push feature branch and open PR.

## Out of scope

- Runtime adapter enforcement in `app.py`
