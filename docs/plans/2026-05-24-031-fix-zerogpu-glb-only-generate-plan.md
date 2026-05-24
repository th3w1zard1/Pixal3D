---
title: "fix: ZeroGPU generate exports GLB without preview frames"
type: fix
status: active
date: 2026-05-24
origin: docs/plans/2026-05-24-030-fix-zerogpu-generate-preview-fallback-plan.md
---

# fix: ZeroGPU generate exports GLB without preview frames

## Summary

Plan 030 showed `cuda_mesh_operators: true` on the live Space, but anonymous generate still failed during preview rendering. Disable preview frames on ZeroGPU and use the geometry-only GLB export path so cold generate completes within slice limits.

---

## Requirements

- R1. `resolve_generation_plan` sets `render_preview=False` when `runtime_mode=zerogpu`.
- R2. Preview render try/except still falls back on ZeroGPU for any residual preview attempts.
- R3. README notes ZeroGPU GLB-only generate path.
- R4. Deploy and confirm `--generate` smoke passes.

---

## Implementation Units

- U1. **ZeroGPU GLB-only plan** — `app.py`, `README.md`
- U2. **Live verify** — deploy + `--generate` smoke
