---
title: "fix: Fit ZeroGPU work into a single quota slice"
type: fix
status: completed
date: 2026-05-23
origin: docs/plans/2026-05-23-002-feat-space-live-e2e-verify-plan.md
---

# fix: Fit ZeroGPU work into a single quota slice

## Summary

Live E2E failed because the UI called `warmup_runtime` (120s GPU reservation) immediately before `generate_3d` (up to 120s), exceeding remaining ZeroGPU quota. Shrink per-call durations and skip redundant pre-generate warmup on ZeroGPU so cold generate fits one slice.

---

## Requirements

- R1. ZeroGPU `warmup_runtime` requests a smaller duration (≤55s).
- R2. ZeroGPU `generate_3d` duration scales down with capped steps (≤55s).
- R3. ZeroGPU `extract_glb_api` duration ≤45s.
- R4. Frontend skips pre-generate `warmup_runtime` when `/health` reports `runtime_mode: zerogpu` (generate already calls `ensure_runtime_ready`).
- R5. Re-run live browser smoke; complete generate if quota allows.

---

## Implementation Units

- U1. Backend duration caps in `app.py`
- U2. Frontend skip redundant warmup in `index.html`
- U3. Deploy and live browser verification
