---
title: "feat: ZeroGPU GLB success UX and textured extract"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-032-feat-recovery-closure-smoke-docs-plan.md
---

# feat: ZeroGPU GLB success UX and textured extract

## Summary

ZeroGPU generate now returns `state_path` plus a geometry-only `glb_path`, but the UI hid textured extract and only showed export controls on step 2. Enable extract after GLB-only generate and surface export on step 3 so the browser path matches smoke success.

---

## Problem Frame

`--generate` smoke passes with `glb_path`, yet the hosted UI left `extract_available: false` and placed the Extract button only on step 2 while GLB success jumps to step 3. Users could view/download coarse GLB but not continue to textured extract without confusion.

---

## Requirements

- R1. ZeroGPU GLB-only `generate_3d` responses set `extract_available: true` when `state_path` is present.
- R2. Export controls show Extract on step 3 when a GLB was loaded and extract is available.
- R3. Post-generate toast hints that preview frames were skipped and textured export is available.
- R4. Deploy; health/html smoke; browser load check on live Space.

---

## Scope Boundaries

- Unit tests
- Re-enabling preview frames on ZeroGPU
- CI generate job

---

## Implementation Units

- U1. **Backend extract flag** — `app.py`
- U2. **UI export step + toast** — `index.html`
- U3. **Verify** — deploy, smokes, browser
