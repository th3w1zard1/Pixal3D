---
title: "feat: workflow_hygiene.sh static gate bundle"
type: feat
status: completed
date: 2026-05-24
origin: docs/post-recovery.md
---

# feat: workflow_hygiene.sh static gate bundle

## Problem

Plans 067–069 added generation manifests, adapter policy, and agent gate JSON separately. Operators lack one fast, non-browser command that runs all static hygiene checks before `./scripts/agent_gate.sh`.

## Requirements

- R1. `scripts/workflow_hygiene.sh` runs example JSON validators, `check_adapter_policy.py`, and `check_workflow_yaml.py`; exits non-zero on failure.
- R2. Optional `--parity` runs `check_repo_parity.py` (documented; off by default for offline/PR forks).
- R3. `README.md`, `AGENTS.md`, `post-recovery.md`, and `python-ci.yml` reference the script.
- R4. Live `./scripts/agent_gate.sh`; push to PR #36 branch.

## Implementation units

- U1. `workflow_hygiene.sh` + CI step.
- U2. Operator docs + agent gate.

## Out of scope

- Merging PR #36 automatically
- Browser or `--generate` smoke in this script
