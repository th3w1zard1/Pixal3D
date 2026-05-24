---
title: "chore: post-recovery re-verification gate"
type: feat
status: completed
date: 2026-05-24
origin: docs/post-recovery.md
---

# chore: post-recovery re-verification gate

## Problem

Plan 052 closed the browser-smoke verification gate. A fresh `/lfg` pass should confirm the live Space still matches `main` and record the latest verification snapshot without burning quota on CLI `--generate` in the same session as browser smoke.

## Requirements

- R1. `python scripts/check_repo_parity.py` passes.
- R2. `./scripts/verify_hosted_space.sh` passes (no `--generate`).
- R3. `./scripts/browser_glb_smoke.sh` runs; record exit code and outcome (`load=`, `generate=`).
- R4. Update `docs/SPACE_RECOVERY.md` verification table with current `main` SHA and browser/CLI timestamps (exit **0** or **1** with explicit quota/error both documented as pass).
- R5. Mark this plan `status: completed` and push to `github` + `origin`.

## Implementation units

- U1. Run verification ladder (parity → hosted verify → browser smoke).
- U2. Doc sync in `docs/SPACE_RECOVERY.md` with results.

## Out of scope

- New smoke code changes unless a regression is found
- `verify_hosted_space.sh --generate` in same session as browser
- Unit tests

## Test scenarios

| ID | Scenario | Expected |
|----|----------|----------|
| T1 | Parity on clean `main` | Exit 0, matching SHAs |
| T2 | Health/HTML markers | `verify_hosted_space.sh` exit 0 |
| T3 | Browser load path | `load=done` within 150s |
| T4 | Browser generate | GLB exit 0, or exit 1 with explicit ZeroGPU quota copy |
