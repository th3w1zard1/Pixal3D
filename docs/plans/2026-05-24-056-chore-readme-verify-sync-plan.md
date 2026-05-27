---
title: "chore: README verification sync and recovery SHA fix"
type: feat
status: completed
date: 2026-05-24
origin: README.md
---

# chore: README verification sync and recovery SHA fix

## Problem

`README.md` still documents only `./scripts/verify_hosted_space.sh` without `--browser`, while `post-recovery.md` and `AGENTS.md` already treat `--browser` as the combined agent gate. `SPACE_RECOVERY.md` last-gate SHA is stale (`02478af` vs current `main`).

## Requirements

- R1. `README.md` local verification section documents `verify_hosted_space.sh --browser` and exit **1** quota semantics.
- R2. `SPACE_RECOVERY.md` last-gate line uses current `main` SHA after this pass.
- R3. Run `./scripts/verify_hosted_space.sh --browser`; record outcome.
- R4. Push to `github` and `origin`.

## Implementation units

- U1. README + SPACE_RECOVERY doc edits.
- U2. Live gate run; mark plan completed.

## Out of scope

- Runtime or CI workflow changes
- Unit tests
