---
title: "feat: recovery closure — smoke GLB assert and operator docs"
type: feat
status: active
date: 2026-05-24
origin: docs/plans/2026-05-24-031-fix-zerogpu-glb-only-generate-plan.md
---

# feat: recovery closure — smoke GLB assert and operator docs

## Summary

Anonymous `--generate` smoke now passes with a geometry-only GLB on ZeroGPU. Close the recovery track by asserting `glb_path` in smoke, exposing cold GPU slice budgets on `/health`, and aligning AGENTS/README with the current skip-warmup / GLB-only flow.

---

## Problem Frame

Plans 027–031 fixed runtime and smoke, but operator docs still describe priming `/warmup_runtime` before generate, and smoke treats any non-error dict as success without checking for `glb_path`. Health still reports only a 60s `generation_max_seconds` even when cold init uses 120s.

---

## Requirements

- R1. `--generate` smoke requires `glb_path` or non-empty `render_paths` in the result payload.
- R2. `/health` `zerogpu_gpu_budgets` includes `cold_generation_max_seconds` when the pipeline is unloaded.
- R3. `AGENTS.md` and `README.md` describe current ZeroGPU smoke (skip warmup, GLB-only generate, ~2–3 min cold).
- R4. Deploy; health/html smoke pass; `--generate` smoke still passes.

---

## Scope Boundaries

- Unit tests
- Re-enabling preview frames on ZeroGPU
- HF_TOKEN CI setup

---

## Implementation Units

- U1. **Smoke GLB assertion** — `scripts/space_smoke.py`
- U2. **Health cold budget** — `app.py`
- U3. **Operator docs** — `AGENTS.md`, `README.md`
- U4. **Live verify** — deploy + smokes
