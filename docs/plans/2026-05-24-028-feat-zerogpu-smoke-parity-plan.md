---
title: "feat: ZeroGPU smoke parity and rembg observability"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-027-feat-zerogpu-lite-rembg-default-plan.md
---

# feat: ZeroGPU smoke parity and rembg observability

## Summary

Align `--generate` smoke with the hosted ZeroGPU UI (skip redundant `/warmup_runtime`) and expose `rembg_model` on `/health` so deploys verify BiRefNet_lite defaults.

---

## Problem Frame

Plan 027 defaulted ZeroGPU to `BiRefNet_lite`, but smoke still calls `/warmup_runtime` before `/generate_3d` while `index.html` skips warmup on ZeroGPU. That stacks an extra GPU slice and often aborts before generate runs. Health also omits the resolved rembg model, so lite-default verification requires log inspection.

---

## Requirements

- R1. `space_smoke.py --generate` skips `/warmup_runtime` when `/health` reports `runtime_mode: zerogpu`.
- R2. `/health` and `/ready` include `rembg_model` from `runtime_config`.
- R3. README and smoke help document ZeroGPU skip-warmup behavior.
- R4. Deploy and re-run generate smoke; record outcome.

---

## Scope Boundaries

- Unit tests (repo policy)
- Guaranteed anonymous cold E2E without sign-in
- Changing main pipeline weights or GPU duration budgets

---

## Implementation Units

- U1. **ZeroGPU smoke skip-warmup**

**Requirements:** R1

**Files:** Modify `scripts/space_smoke.py`

**Verification:** Dry-run logic: zerogpu health → no warmup call; non-zerogpu → warmup retained.

---

- U2. **Rembg model in health payload**

**Requirements:** R2

**Files:** Modify `app.py`

**Verification:** `curl /health` includes `rembg_model: ZhengPeng7/BiRefNet_lite` on live Space.

---

- U3. **Docs and live verify**

**Requirements:** R3, R4

**Dependencies:** U1, U2

**Files:** Modify `README.md`

**Verification:** Health/html smoke pass; generate smoke attempted post-deploy.

---

## Sources & References

- `index.html` `ensureRuntimePrimed()` ZeroGPU skip
- Plan 027 BiRefNet_lite default
