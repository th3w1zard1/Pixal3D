---
title: "feat: validate_gate_json.py for gate summaries"
type: feat
status: completed
date: 2026-05-24
origin: README.md
---

# feat: validate_gate_json.py for gate summaries

## Problem

Persisted gate JSON has a documented shape (`example.json`) but no validator. Workflow hygiene calls for validation gates before claiming success.

## Requirements

- R1. Add `scripts/validate_gate_json.py PATH` validating `pixal3d-agent-gate/2` required fields and types.
- R2. `verify_hosted_space.sh` runs validator after `--write-summary` when path is set.
- R3. Document in `docs/gate-results/README.md` and `AGENTS.md`.
- R4. Live `agent_gate.sh --write-summary`; push to `github` and `origin`.

## Implementation units

- U1. Validator script + verify hook.
- U2. Docs + live run.

## Out of scope

- CI integration
- Unit tests per AGENTS.md unless asked
