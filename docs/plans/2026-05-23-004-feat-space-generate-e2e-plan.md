---
title: "feat: Complete live Space generate → GLB E2E under ZeroGPU quota"
type: feat
status: completed
date: 2026-05-23
origin: docs/plans/2026-05-23-003-fix-zerogpu-quota-budget-plan.md
---

# feat: Complete live Space generate → GLB E2E under ZeroGPU quota

## Summary

Plan 003 removed stacked GPU reservations but live generate still fails at the quota margin (`55s requested vs 57s left`). Tighten the single-slice budget further, align hosted export defaults with ZeroGPU caps, surface duration hints on `/health`, and re-verify the full browser flow on the deployed Space.

## Requirements

- R1. ZeroGPU `generate_3d` reservation ≤40s with conservative step scaling.
- R2. `/health` exposes hosted GPU duration budgets for the UI.
- R3. On ZeroGPU, default export profile to Fast Preview (512px texture cap).
- R4. Live browser: sample → generate → export GLB (or document quota block with evidence).

## Implementation Units

- U1. `app.py` — duration caps + `runtime_payload` hints
- U2. `index.html` — ZeroGPU export default + health-driven hints
- U3. Deploy to HF Space + pipeline browser verification

## Test scenarios

| ID | Scenario | Expected |
|----|----------|----------|
| T1 | GET `/health` on Space | `runtime_mode: zerogpu`, `zerogpu_gpu_budgets` present |
| T2 | Sample gallery click | Generate enabled within ~10s |
| T3 | Start Generation (cold) | Succeeds or shows quota error with ≤40s in message |
| T4 | Export GLB after generate | GLB download path works when T3 succeeds |
