---
title: "feat: Surface ZeroGPU budget hints and retry live E2E"
type: feat
status: completed
date: 2026-05-23
origin: docs/plans/2026-05-23-009-fix-pr2-merge-conflict-plan.md
---

# feat: Surface ZeroGPU budget hints and retry live E2E

## Summary

PRs #1–#2 are merged on `github/main`. Expose `/health` `zerogpu_gpu_budgets` in the runtime card so users understand slice limits before generating, then retry live sample → generate → export on the Space.

## Requirements

- R1. Runtime card shows hosted GPU slice caps when `zerogpu_gpu_budgets` is present.
- R2. No change to backend duration logic.
- R3. Deploy to HF Space; browser smoke + generate attempt.
- R4. Open PR from `github/main` if not already merged.

## Implementation Units

- U1. `index.html` — runtime budget hint from `/health`
- U2. Deploy + browser verification
- U3. Push branch and open PR
