---
title: "feat: ZeroGPU cold-start hub prefetch and GPU budget"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-028-feat-zerogpu-smoke-parity-plan.md
---

# feat: ZeroGPU cold-start hub prefetch and GPU budget

## Summary

Reduce anonymous ZeroGPU `GPU task aborted` failures by prefetching Hub weights on CPU during Space idle, auto-enabling low-VRAM mode on hosted ZeroGPU, and granting a 120s generation slice when the pipeline is not yet loaded.

---

## Problem Frame

After plans 027–028, live `/health` confirms `BiRefNet_lite`, but anonymous `--generate` still aborts (~99s) because cold `init_models` downloads and loads the full Pixal3D stack inside a 60s ZeroGPU slice. The browser UI skips warmup and loads everything on first generate.

---

## Requirements

- R1. Hosted ZeroGPU Spaces default `PIXAL3D_LOW_VRAM=1` unless explicitly overridden.
- R2. Hosted Spaces start a background CPU thread that prefetches pipeline.json, Trellis weights, rembg, DINO, and MoGe Hub artifacts before first GPU use.
- R3. `/health` reports `low_vram`, `hub_prefetch_state`, and related message.
- R4. ZeroGPU `generate_3d` requests a 120s GPU slice when `pipeline is None` (cold init); warm runs stay capped at 60s.
- R5. README documents prefetch + cold slice behavior; deploy and re-run `--generate` smoke.

---

## Scope Boundaries

- Unit tests (repo policy)
- Guaranteed anonymous E2E without sign-in
- Changing inference quality defaults beyond low-VRAM posture

---

## Implementation Units

- U1. **ZeroGPU env defaults and prefetch helpers**

**Requirements:** R1, R2

**Files:** Modify `space_bootstrap.py`

**Verification:** Config builder sees LOW_VRAM after defaults; prefetch downloads without importing CUDA models.

---

- U2. **Wire prefetch, health fields, cold GPU duration**

**Requirements:** R2, R3, R4

**Dependencies:** U1

**Files:** Modify `app.py`

**Verification:** `/health` shows prefetch state; cold duration returns 120.

---

- U3. **Docs and live verify**

**Requirements:** R5

**Dependencies:** U2

**Files:** Modify `README.md`

**Verification:** Deploy; health/html smoke; `--generate` attempted.

---

## Sources & References

- Plan 028 generate abort at ~99s with skip-warmup
- `space_runtime.py` background init pattern
- `ZEROGPU_MAX_DURATION_SECONDS = 120` in `app.py`
