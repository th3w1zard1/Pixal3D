---
title: "feat: Finalize live Space E2E after ZeroGPU budget deploy"
type: feat
status: completed
date: 2026-05-23
origin: docs/plans/2026-05-23-004-feat-space-generate-e2e-plan.md
---

# feat: Finalize live Space E2E after ZeroGPU budget deploy

## Summary

Plan 004 landed (`96fd584`) with 40s generate budget and `/health` GPU budget hints. Complete the interrupted pipeline: live browser verification through generate/export, fix any blockers found, and update PR #1 with evidence.

## Requirements

- R1. Confirm deployed `/health` includes `zerogpu_gpu_budgets`.
- R2. Browser: sample → Generate enabled → Start Generation.
- R3. If quota allows: generate completes and GLB export path works.
- R4. If quota blocks: capture error text and duration requested; update PR test plan.
- R5. No unrelated runtime changes in deploy.

## Implementation Units

- U1. Live browser verification (pipeline)
- U2. PR #1 body refresh with verification results
- U3. Code fix only if E2E reveals a regression (optional)
