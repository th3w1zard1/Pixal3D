---
title: "ship: merge post-recovery PR and sync GitHub↔HF parity"
type: chore
status: active
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# ship: merge post-recovery PR and sync GitHub↔HF parity

## Summary

PR #34 (`feat/post-recovery-plan-hygiene`) has green CI and bundles post-recovery docs, browser GLB smoke, and UI smoke markers. HF `origin/main` is ahead from interim `hf upload` commits. Merge the PR, push `github/main` to `origin`, re-run hosted verification, and attempt browser GLB smoke before CLI `--generate`.

## Requirements

- R1. Merge PR #34 into `main` when mergeable and CI green.
- R2. Update local `main`, push to `github` and `origin` so `check_repo_parity.py` passes.
- R3. Run `./scripts/verify_hosted_space.sh` (no `--generate` first).
- R4. Run `./scripts/browser_glb_smoke.sh`; record pass (exit 0), quota error (exit 1), or timeout in `docs/SPACE_RECOVERY.md`.
- R5. Do not run CLI `--generate` in the same session before browser smoke.

## Scope Boundaries

- New feature work beyond shipping PR #34
- Playwright CI

## Implementation Units

- U1. Merge PR #34; sync `main` to both remotes.
- U2. Hosted verify + browser smoke; update recovery docs.

## Verification

- `python3 scripts/check_repo_parity.py` exits 0.
- `./scripts/verify_hosted_space.sh` exits 0.
