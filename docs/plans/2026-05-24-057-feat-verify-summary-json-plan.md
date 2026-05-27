---
title: "feat: verify_hosted_space --summary-json for agents"
type: feat
status: completed
date: 2026-05-24
origin: README.md
---

# feat: verify_hosted_space --summary-json for agents

## Problem

`space_smoke.py` emits JSON summaries for health checks, but `verify_hosted_space.sh` only prints human text. Agents closing tasks need a single machine-readable record of parity, health, and optional browser outcome.

## Requirements

- R1. `scripts/verify_hosted_space.sh` accepts `--summary-json` and prints one JSON object to stdout after checks (before final OK line).
- R2. JSON includes: `url`, `parity_ok`, `health_ok`, `browser_ran`, `browser_exit` (null if not run), `overall_ok`.
- R3. Document flag in script usage, `AGENTS.md`, and run live `--browser --summary-json` gate.
- R4. Update `docs/SPACE_RECOVERY.md` last-gate line; push to `github` and `origin`.

## Implementation units

- U1. Extend `verify_hosted_space.sh` with summary capture and JSON emit.
- U2. Doc updates + live verification.

## Out of scope

- CI workflow changes
- Unit tests
