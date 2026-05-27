---
title: "chore: sync post-recovery docs with verify --browser"
type: feat
status: completed
date: 2026-05-24
origin: docs/post-recovery.md
---

# chore: sync post-recovery docs with verify --browser

## Problem

Plan 054 added `./scripts/verify_hosted_space.sh --browser`, but `docs/post-recovery.md` still lists browser smoke as a separate manual step. Operators and agents need one authoritative verification path.

## Requirements

- R1. `docs/post-recovery.md` recommends `verify_hosted_space.sh --browser` as the combined gate.
- R2. `docs/SPACE_RECOVERY.md` last-gate line references commit on `main` after this pass.
- R3. Run `./scripts/verify_hosted_space.sh --browser` on live Space; record outcome.
- R4. Push to `github` and `origin`.

## Implementation units

- U1. Doc updates (post-recovery, SPACE_RECOVERY).
- U2. Run verification gate and mark plan completed.

## Out of scope

- Runtime code changes
- CI workflow changes
- Unit tests
