---
title: "fix: in-eval await loops for browser smoke"
type: fix
status: active
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# fix: in-eval await loops for browser smoke

## Problem

Bash `__pixal3dSmokeAdvance` ticks never progress async `loadSampleFromPath` (stuck at `loading`). agent-browser does not reliably run microtasks between separate `eval` calls.

## Approach

Two short-lived monolithic evals with internal `await` loops:
1. Load sample until `done` (preview window).
2. Start generation and poll until `glb-ready` (generate window).

## Requirements

- R1. `browser_glb_smoke.sh` uses in-eval loops; no bash tick loop for load/generate.
- R2. Keep gallery-only smoke load from plan 050.
- R3. Live smoke exit **0** or quota **1**.
