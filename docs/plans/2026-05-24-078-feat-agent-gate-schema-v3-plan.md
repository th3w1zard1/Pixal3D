---
title: "feat: agent gate schema v3 with deploy health fields"
type: feat
status: completed
date: 2026-05-24
origin: docs/gate-results/README.md
---

# feat: agent gate schema v3 with deploy health fields

## Problem

`pixal3d-agent-gate/2` omits live deploy signals now on `/health` (`repo_git_head`, `adapter_policy_ok`). Operators must curl `/health` separately after `agent_gate.sh`.

## Requirements

- R1. Gate JSON schema `pixal3d-agent-gate/3` adds `space_repo_git_head`, `repo_git_head_match`, `adapter_policy_ok`, `adapter_policy_enabled_count`.
- R2. `verify_hosted_space.sh` fetches `/health` after smoke and embeds fields; `overall_ok` requires `repo_git_head_match` when both heads are known.
- R3. Update `validate_gate_json.py`, `docs/gate-results/example.json`, README, `AGENTS.md`.
- R4. `./scripts/pre_ship.sh` on `main`; deploy if only scripts change? (verify_hosted_space only — no app.py); push `github` + `origin` when merged.

## Out of scope

- Bumping generation manifest schemas
