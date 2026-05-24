---
title: "fix: reliable browser smoke generation start"
type: fix
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# fix: reliable browser smoke generation start

## Summary

`browser_glb_smoke.sh` often exits 2 because programmatic `.click()` on a disabled **Start Generation** button does not invoke `startGeneration()` (no loading overlay). Expose a smoke entrypoint, set a generation-active body marker in `showLoading`, harden the script, deploy to the Space, and re-run browser E2E.

## Requirements

- R1. `window.__pixal3dRunGeneration` calls `startGeneration()` after UI init.
- R2. `showLoading` / `hideLoading` set/clear `data-smoke-generation-active` on `<body>`.
- R3. Script waits for `__pixal3dRunGeneration`, calls it after file-ready, polls `data-smoke-generation-active` or `data-smoke-glb-ready`.
- R4. Deploy runtime change to HF; push `main` to `github` and `origin`; run browser smoke (no CLI `--generate` first).
- R5. Update `docs/SPACE_RECOVERY.md` with exit code outcome.

## Scope Boundaries

- Playwright CI
- Changing generate API semantics

## Implementation Units

- U1. `index.html` smoke hooks for generation start/active.
- U2. `scripts/browser_glb_smoke.sh` use hooks instead of disabled-button click.
- U3. Deploy, verify parity, browser smoke, doc update.

## Verification

- `./scripts/browser_glb_smoke.sh` exits 0 with GLB ready, or 1 with explicit viewer quota error (not exit 2 at 45s).
