---
title: "fix: Default export profile to Fast Preview on hosted Space"
type: fix
status: completed
date: 2026-05-23
origin: docs/plans/2026-05-23-007-ship-pr1-signin-cta-plan.md
---

# fix: Default export profile to Fast Preview on hosted Space

## Summary

PR #1 merged. The export `<select>` still marks **Balanced** as `selected` in HTML, so users see the wrong hint until JS runs (and on slow `/health` races). Align static markup with ZeroGPU Fast Preview default and verify live smoke after deploy.

## Requirements

- R1. `export-profile` HTML default is `fast`, not `balanced`.
- R2. Default hint copy matches Fast Preview.
- R3. Branch from `github/main`; deploy to HF Space; browser smoke.
- R4. Open follow-up PR (PR #1 already merged).

## Implementation Units

- U1. `index.html` — static export default + hint
- U2. Deploy + browser verification
- U3. Push branch and open PR
