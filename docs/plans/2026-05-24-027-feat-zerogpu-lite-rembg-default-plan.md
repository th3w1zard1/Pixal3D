---
title: "feat: BiRefNet_lite default rembg on ZeroGPU Space"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-026-fix-zerogpu-warmup-duration-plan.md
---

# feat: BiRefNet_lite default rembg on ZeroGPU Space

## Summary

When running on a hosted ZeroGPU Space (`SPACE_ID` + `ACCELERATOR=zero*`), default the rembg model to `ZhengPeng7/BiRefNet_lite` instead of full BiRefNet to shorten cold warmup load time.

---

## Problem Frame

Anonymous `warmup_runtime` still aborts after ~105s on cold ZeroGPU despite a 60s declared warmup slice. Full BiRefNet is heavier than `BiRefNet_lite`; the README already lists lite as the lighter fallback.

---

## Requirements

- R1. `build_runtime_config` selects `BiRefNet_lite` when `PIXAL3D_REMBG_MODEL` is unset, `SPACE_ID` is set, and `ACCELERATOR` starts with `zero`.
- R2. Full `BiRefNet` remains available as fallback and via `PIXAL3D_REMBG_MODEL` override.
- R3. README runtime notes mention ZeroGPU lite default.
- R4. Deploy and re-run `--generate` smoke; document outcome.

---

## Scope Boundaries

- Unit tests (repo policy)
- Changing main pipeline weights
- Guaranteed anonymous E2E without sign-in

---

## Implementation Units

- U1. **ZeroGPU lite rembg default**

**Requirements:** R1, R2

**Files:** Modify `space_bootstrap.py`

**Verification:** Config builder returns lite model for ZeroGPU env fixture.

---

- U2. **Document and verify**

**Requirements:** R3, R4

**Dependencies:** U1

**Files:** Modify `README.md`

**Verification:** Live deploy; generate smoke attempted.

---

## Sources & References

- `space_bootstrap.py`, README rembg models
- Plan 026 warmup abort at ~105s
