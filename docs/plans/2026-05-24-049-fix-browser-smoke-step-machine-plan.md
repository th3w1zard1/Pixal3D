---
title: "fix: browser smoke step machine for agent-browser"
type: fix
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
supersedes: docs/plans/2026-05-24-048-fix-smoke-sample-load-preview-plan.md
---

# fix: browser smoke step machine for agent-browser

## Problem

`browser_glb_smoke.sh` reaches sample `done` and `generate started` but not exit **0**. A single long `Runtime.evaluate` hits agent-browser CDP limits (~80s) or leaves later `ab eval` calls unable to read the page. Fire-and-forget `void loadSample()` does not run after eval returns.

## Approach

Expose `window.__pixal3dSmokeAdvance()` — a short async tick that advances load → generate → GLB poll. The shell script calls it every few seconds so the browser event loop runs between CDP calls.

## Requirements

- R1. `__pixal3dSmokeAdvance()` returns one of: `loading`, `sample-done`, `generating`, `glb-ready`, `error:…`, `timeout:…`.
- R2. `browser_glb_smoke.sh` polls `__pixal3dSmokeAdvance()` (no monolithic eval); honors `--preview-wait` and `--generate-wait`.
- R3. Deploy to HF; run smoke until exit **0** or explicit quota exit **1**; update `docs/SPACE_RECOVERY.md`.

## Implementation units

- U1. `index.html` — smoke advance state machine (smokeTestMode only).
- U2. `scripts/browser_glb_smoke.sh` — tick loop instead of single eval.
- U3. Docs + plan status.

## Verification

```bash
./scripts/browser_glb_smoke.sh --generate-wait 420
```
