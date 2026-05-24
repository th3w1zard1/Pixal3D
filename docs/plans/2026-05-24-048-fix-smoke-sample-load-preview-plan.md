---
title: "fix: reliable smoke sample load and preview markers"
type: fix
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
supersedes: docs/plans/2026-05-24-047-fix-smoke-skip-preprocess-plan.md
---

# fix: reliable smoke sample load and preview markers

## Problem

`./scripts/browser_glb_smoke.sh` exits **2**: `data-smoke-file-ready` and `source-preview` never appear within 135s after plan 047 (skip preprocess). Skip-preprocess fixed preprocess hangs but sample load still never completes—likely `fetch()` stalling in headless before `handleImageUpload` runs. Gallery fallback uses the same `fetch` path with `showLoading()` and still runs preprocess.

## Requirements

- R1. `__pixal3dLoadSamplePath` sets preview UI and `data-smoke-file-ready` synchronously, then resolves `currentFile` with a bounded `fetch` (timeout) and DOM img fallback.
- R2. Gallery example clicks use `skipPreprocess: true` (smoke parity; preprocess remains available for manual uploads).
- R3. `browser_glb_smoke.sh` polls load completion via `data-smoke-sample-load` / `data-smoke-load-error` (no fire-and-forget eval only).
- R3b. Smoke mode (`?smoke=1`) skips cpu→zerogpu auto-reload; script waits for `data-runtime-mode=zerogpu` before sample load.
- R4. Deploy `main` to HF + GitHub; browser smoke exit **0** (GLB) or **1** (quota); update `docs/SPACE_RECOVERY.md`.
- R5. Mark plans 047 and 048 `status: completed` when verified.

## Implementation units

- U1. `index.html` — `loadSampleFromPath` helper; sync preview; timeout + gallery fallback; gallery `skipPreprocess`.
- U2. `scripts/browser_glb_smoke.sh` — await smoke load markers; clearer abort messages.
- U3. `docs/SPACE_RECOVERY.md` — browser row after smoke run.

## Decisions

- Synchronous preview from absolute URL or existing gallery `<img>` so agent-browser sees markers even when `fetch` is slow.
- 20s fetch timeout; fallback `canvas`/`fetch` from visible gallery thumbnail.
- Do not add unit tests (AGENTS.md).

## Risks

- ZeroGPU quota may still yield exit **1**; that is acceptable verification.
- Space rebuild lag after push—wait before smoke.

## Verification

```bash
python3 scripts/check_repo_parity.py
./scripts/verify_hosted_space.sh
./scripts/browser_glb_smoke.sh
```
