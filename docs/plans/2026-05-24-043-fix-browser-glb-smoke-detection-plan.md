---
title: "fix: browser GLB smoke detection and cold-generate wait"
type: fix
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# fix: browser GLB smoke detection and cold-generate wait

## Summary

Plan 042 added `browser_glb_smoke.sh` but timed out at 200s without detecting success. Cold ZeroGPU generate can exceed 200s wall clock, and the model-viewer keeps `visibility:hidden` until the GLB load event. Add a body smoke marker when the viewer GLB is ready, improve the script's success predicates and default wait, and re-run against the live Space.

## Requirements

- R1. Set `data-smoke-glb-ready="true"` on `<body>` when `loadViewerModel` completes; clear when a new generation starts.
- R2. `browser_glb_smoke.sh` succeeds on the marker or step-3 active + export button visible; default `--generate-wait` 300s.
- R3. Script verifies generation loading started after Generate click; clearer stderr on timeout.
- R4. Update `docs/SPACE_RECOVERY.md` with pass/fail from this run; no CLI `--generate` in same session first.

## Scope Boundaries

- Playwright in CI
- Changing generate API behavior

## Implementation Units

- U1. `index.html` smoke marker on GLB ready / clear on generate start.
- U2. Harden `scripts/browser_glb_smoke.sh` detection and defaults.
- U3. Run browser smoke; update recovery docs.

## Verification

- `./scripts/browser_glb_smoke.sh` exits 0 with GLB marker or visible step 3, or exits 1 with explicit viewer quota error.
