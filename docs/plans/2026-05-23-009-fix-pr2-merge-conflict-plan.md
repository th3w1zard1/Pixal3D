---
title: "fix: Resolve PR #2 merge conflict and merge export default"
type: fix
status: completed
date: 2026-05-23
origin: docs/plans/2026-05-23-008-fix-export-profile-default-plan.md
---

# fix: Resolve PR #2 merge conflict and merge export default

## Summary

PR #2 is CONFLICTING because the branch was rebased onto HF `origin/main` while GitHub `main` is the squash merge of PR #1. Rebase the fix onto `github/main`, verify CI, merge PR #2, and redeploy HF Space.

## Requirements

- R1. Branch rebased onto `github/main` with only the export-default diff.
- R2. PR #2 mergeable; CI green.
- R3. HF Space `main` updated after merge.
- R4. Live smoke: export profile defaults to `fast`.

## Implementation Units

- U1. Rebase `fix/export-profile-default` onto `github/main`
- U2. Merge PR #2
- U3. Sync HF + browser smoke
