---
title: "fix: GLB fallback when CUDA mesh preview unavailable"
type: fix
status: active
date: 2026-05-24
origin: docs/plans/2026-05-24-029-feat-zerogpu-cold-prefetch-plan.md
---

# fix: GLB fallback when CUDA mesh preview unavailable

## Summary

Anonymous ZeroGPU `generate_3d` reaches mesh generation then fails at `mesh.simplify` with a bare `RuntimeError` when `cumesh` is unavailable. Disable preview rendering when CUDA mesh operators are missing and export a CPU GLB instead so generate smoke and the UI can complete.

---

## Problem Frame

Live progress shows `Rendering views` before failure. `Mesh.simplify` calls `_require_cumesh`, which raises `RuntimeError("simplify requires CUDA mesh operators.")` when `cumesh` failed to import. Gradio surfaces only the exception class name to clients.

---

## Requirements

- R1. Detect CUDA mesh operator availability (`cumesh` import) in one shared helper.
- R2. `resolve_generation_plan` sets `render_preview=False` when mesh operators are unavailable, even on CUDA/ZeroGPU.
- R3. `_generate_3d_impl` falls back to `export_basic_glb` if preview rendering raises mesh-operator errors.
- R4. `/health` exposes `cuda_mesh_operators` for deploy verification.
- R5. Smoke captures richer client errors and optional `/progress` stage on failure; deploy and re-run `--generate`.

---

## Scope Boundaries

- Unit tests (repo policy)
- Installing or rebuilding cumesh wheels on HF
- Full preview rendering parity without cumesh

---

## Implementation Units

- U1. **Mesh operator probe**

**Requirements:** R1

**Files:** Modify `trellis2/representations/mesh/base.py`

**Verification:** Helper returns False when cumesh import fails.

---

- U2. **Generation plan and fallback**

**Requirements:** R2, R3, R4

**Dependencies:** U1

**Files:** Modify `app.py`

**Verification:** Plan sets `render_preview=False` without cumesh; health field present.

---

- U3. **Smoke errors and verify**

**Requirements:** R5

**Dependencies:** U2

**Files:** Modify `scripts/space_smoke.py`, `README.md`

**Verification:** Deploy; `--generate` returns `glb_path` or clearer error.

---

## Sources & References

- Progress `Rendering views` before anonymous failure (~95–128s)
- `trellis2/representations/mesh/base.py` `_require_cumesh`
