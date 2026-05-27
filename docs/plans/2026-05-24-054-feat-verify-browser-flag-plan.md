---
title: "feat: optional --browser on verify_hosted_space.sh"
type: feat
status: completed
date: 2026-05-24
origin: docs/post-recovery.md
---

# feat: optional --browser on verify_hosted_space.sh

## Problem

Agents run three separate commands for post-recovery validation (`check_repo_parity` is already inside `verify_hosted_space.sh`, then browser smoke separately). A single entry point with an explicit `--browser` flag reduces missed ordering and documents exit-code semantics in one place.

## Requirements

- R1. `scripts/verify_hosted_space.sh` accepts `--browser` and runs `./scripts/browser_glb_smoke.sh` after health/HTML (never with `--generate` in the same invocation).
- R2. Usage/help and `docs/SPACE_RECOVERY.md` verification order mention `--browser`.
- R3. `AGENTS.md` points agents to `./scripts/verify_hosted_space.sh --browser` for full non-generate gate.
- R4. Run default gate: script without flags (parity + health); with `--browser` on live Space; record outcomes; sync parity SHA in recovery doc to current `main`.
- R5. Push to `github` and `origin`.

## Implementation units

- U1. Extend `scripts/verify_hosted_space.sh` with `--browser` flag and ordering guard vs `--generate`.
- U2. Update `docs/SPACE_RECOVERY.md` and `AGENTS.md`.
- U3. Run verification ladder and update recovery snapshot.

## Out of scope

- Combining `--browser` and `--generate` in one command
- New unit tests

## Test scenarios

| ID | Scenario | Expected |
|----|----------|----------|
| T1 | `./scripts/verify_hosted_space.sh` | Exit 0, parity + health |
| T2 | `--browser --generate` | Exit 2, usage error |
| T3 | `--browser` only | Browser runs after health; exit 0 or 1 (quota) per smoke rules |
