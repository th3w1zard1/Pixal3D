---
title: "ship: merge browser smoke PR and verify GLB E2E"
type: chore
status: active
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# ship: merge browser smoke PR and verify GLB E2E

## Summary

PR #35 adds browser smoke hooks and script hardening. Merge it, sync `github/main` to `origin`, run `browser_glb_smoke.sh` on the live Space (no CLI `--generate` first), and update recovery docs with the outcome.

## Requirements

- R1. Squash-merge PR #35 when CI is green.
- R2. `check_repo_parity.py` passes after pushing `main` to both remotes.
- R3. `./scripts/verify_hosted_space.sh` passes.
- R4. `./scripts/browser_glb_smoke.sh` runs on live Space; record exit 0 (GLB ready), 1 (quota), or 2 (timeout) in `docs/SPACE_RECOVERY.md`.
- R5. No CLI `--generate` in the same session before browser smoke.

## Scope Boundaries

- Further UI refactors beyond merge
- Playwright CI

## Implementation Units

- U1. Merge PR #35; sync `main` to `github` and `origin`.
- U2. Run hosted verify + browser smoke; update docs.

## Verification

- Parity OK; browser smoke exit 0 preferred, explicit quota error (exit 1) acceptable.
