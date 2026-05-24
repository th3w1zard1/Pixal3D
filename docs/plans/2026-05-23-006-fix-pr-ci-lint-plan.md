---
title: "fix: Unblock PR #1 CI lint and merge readiness"
type: fix
status: completed
date: 2026-05-23
origin: docs/plans/2026-05-23-005-feat-space-live-e2e-finalize-plan.md
---

# fix: Unblock PR #1 CI lint and merge readiness

## Summary

PR #1 fails Ruff (`lint` job). Fix typing/unused-variable violations in `app.py`, verify CI locally, re-run live Space smoke, and refresh PR #1.

## Requirements

- R1. `ruff check app.py` passes (F403/F405/F841).
- R2. No behavior change to runtime paths.
- R3. Push branch; confirm CI green on PR #1.
- R4. Live Space smoke: `/health` + sample → Generate enabled.

## Implementation Units

- U1. `app.py` — explicit typing imports, unused var cleanup
- U2. Local ruff verification + deploy unchanged runtime to HF if needed
- U3. PR #1 update
