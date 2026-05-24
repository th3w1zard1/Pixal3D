---
title: "fix: gallery-only smoke sample load"
type: fix
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
supersedes: docs/plans/2026-05-24-049-fix-browser-smoke-step-machine-plan.md
---

# fix: gallery-only smoke sample load

## Problem

`browser_glb_smoke.sh` stalls at `tick=loading` for the full preview window. `loadSampleFromPath` in smoke mode tries `fetch()` first (25s); headless agent-browser often never completes fetch, so `__pixal3dSmokeSampleStatus` never reaches `done`.

## Requirements

- R1. In `smokeTestMode`, resolve sample file from gallery thumbnail only (no `fetch()`).
- R2. `__pixal3dSmokeAdvance` triggers a gallery click fallback once if load is slow.
- R3. Guard against duplicate `loadSampleFromPath` starts.
- R4. Deploy; browser smoke exit **0** or quota **1**; update `docs/SPACE_RECOVERY.md`.

## Implementation units

- U1. `index.html` — gallery-only smoke load; advance fallback click; load guard.
- U2. `scripts/browser_glb_smoke.sh` — optional gallery click before ticks.
- U3. Verify on live Space.
