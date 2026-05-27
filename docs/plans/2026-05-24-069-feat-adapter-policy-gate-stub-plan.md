---
title: "feat: adapter policy gate stub"
type: feat
status: completed
date: 2026-05-24
origin: README.md
---

# feat: adapter policy gate stub

## Problem

README prioritizes gating heavy adapters behind license checks. Generation smoke manifests and agent gates exist, but there is no policy file or validator for future adapters.

## Requirements

- R1. `docs/adapters/policy.example.json` defines `pixal3d-adapter-policy/1` with an `adapters` array.
- R2. `scripts/validate_adapter_policy.py` validates policy JSON; CI checks the example on every run.
- R3. `scripts/check_adapter_policy.py` loads a policy (default example), enforces enabled adapters have `license_spdx`, emits JSON summary on stdout.
- R4. `docs/adapters/README.md`, `AGENTS.md`, and `post-recovery.md` reference the gate; live `./scripts/agent_gate.sh`; push to PR #36 branch.

## Implementation units

- U1. Policy schema, validator, checker script, CI.
- U2. Operator docs + agent gate run.

## Out of scope

- Enabling adapters in `app.py`
- Runtime license verification against Hub
