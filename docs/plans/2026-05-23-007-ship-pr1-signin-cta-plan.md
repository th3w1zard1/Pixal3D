---
title: "ship: Merge PR #1 and add ZeroGPU sign-in CTA"
type: ship
status: completed
date: 2026-05-23
origin: docs/plans/2026-05-23-006-fix-pr-ci-lint-plan.md
---

# ship: Merge PR #1 and add ZeroGPU sign-in CTA

## Summary

PR #1 is mergeable with green CI. Add a direct Hugging Face sign-in action on quota/abort errors so users can unlock higher ZeroGPU quota, then merge the branch to GitHub `main` and verify the live Space smoke path.

## Requirements

- R1. Quota/abort viewer errors show a **Sign in on Hugging Face** action linking back to the Space.
- R2. `ruff check --select F,E9` still passes.
- R3. Live smoke: sample → Generate enabled.
- R4. Merge PR #1 to GitHub `main` after push.

## Implementation Units

- U1. `index.html` — sign-in CTA in viewer error overlay
- U2. Deploy + browser smoke
- U3. `gh pr merge` for PR #1
