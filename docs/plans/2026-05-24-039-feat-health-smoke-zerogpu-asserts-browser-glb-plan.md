---
title: "feat: ZeroGPU health smoke asserts and browser GLB proof"
type: feat
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# feat: ZeroGPU health smoke asserts and browser GLB proof

## Summary

Recovery is closed and `verify_hosted_space.sh` exists, but health smoke only checks HTTP 200. Add ZeroGPU recovery field assertions to `space_smoke.py`, then attempt browser default-sample GLB (no CLI `--generate` first) and record the outcome.

---

## Requirements

- R1. Health smoke fails when hosted ZeroGPU `/health` misses recovery fields (`rembg_model`, `hub_prefetch_state`, `cold_generation_max_seconds`, `cuda_mesh_operators`).
- R2. `./scripts/verify_hosted_space.sh` passes on live Space after change.
- R3. Browser E2E before any `--generate` in session.
- R4. Update `docs/SPACE_RECOVERY.md` verification matrix (browser pass or quota note).

---

## Scope Boundaries

- Playwright in CI
- Unit tests

---

## Implementation Units

- U1. **`zerogpu_health_ok()` in `scripts/space_smoke.py`** — validate recovery fields when `runtime_mode=zerogpu`.
- U2. **Browser GLB** — gallery `0_img.png`, Generate at 512, wait for GLB or quota error.
- U3. **Docs** — SPACE_RECOVERY matrix + parity SHA.
- U4. **Ship** — PR, merge, HF sync.
