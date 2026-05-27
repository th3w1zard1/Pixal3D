---
title: "feat: scripts/agent_gate.sh canonical agent entrypoint"
type: feat
status: completed
date: 2026-05-24
origin: AGENTS.md
---

# feat: scripts/agent_gate.sh canonical agent entrypoint

## Problem

Agents must remember `./scripts/verify_hosted_space.sh --browser --summary-json`. A single named entrypoint reduces drift across `AGENTS.md`, `post-recovery.md`, and `SPACE_RECOVERY.md`.

## Requirements

- R1. Add `scripts/agent_gate.sh` that runs `verify_hosted_space.sh --browser --summary-json` and forwards `--url` / exit codes.
- R2. `AGENTS.md`, `post-recovery.md`, `SPACE_RECOVERY.md` verification sections reference `agent_gate.sh` as primary.
- R3. Live run `./scripts/agent_gate.sh`; update last-gate line.
- R4. Push to `github` and `origin`.

## Implementation units

- U1. New script + doc sync.
- U2. Live gate run.

## Out of scope

- CI workflow changes
- Unit tests
