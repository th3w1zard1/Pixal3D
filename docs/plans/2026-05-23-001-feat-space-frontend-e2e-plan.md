---
title: "feat: Align Space frontend with runtime readiness and verify live E2E"
type: feat
status: completed
date: 2026-05-23
origin: .cursor/plans/pixal3d_space_recovery_5b65d5a8.plan.md
---

# feat: Align Space frontend with runtime readiness and verify live E2E

## Summary

Complete the remaining Space recovery slice by porting runtime readiness, warmup priming, export-profile controls, and CPU→ZeroGPU transition UX from `index_bak.html` into the canonical `index.html`, then deploy to the Hugging Face Space and verify the full browser flow on the live runtime.

---

## Problem Frame

Backend work landed `/health`, `/ready`, `warmup_runtime`, ZeroGPU caps, and CPU hardware-transition payloads in `app.py`, but the production UI served at `/` still uses `index.html` without those integrations. Users on a cold or CPU-standby Space see opaque failures instead of guided warmup or hardware-switch messaging. The recovery plan’s final verification gate (U4) remains open.

---

## Requirements

- R1. `index.html` probes `/health` on load and periodically to show cold/warming/ready runtime state.
- R2. Generation calls `warmup_runtime` before `generate_3d` when the runtime is not ready.
- R3. CPU transition responses (`hardware_transition_requested`, `message`) render actionable UI instead of generic errors.
- R4. GLB export respects selectable texture budgets (1K/2K/4K) aligned with ZeroGPU caps.
- R5. Changes deploy to `th3w1zard1/Pixal3D` and pass a live browser smoke test (sample image → generate → export).

---

## Scope Boundaries

- No new pytest suite (repo policy defers tests unless explicitly requested).
- No refactor of `runtime_policy` extraction or backup file deletion.
- No proxy/local app path changes.

---

## Key Technical Decisions

- **Canonical UI is `index.html`**: Port patterns from `index_bak.html` rather than switching the homepage route.
- **Preserve existing viewer/error UX**: Extend `showViewerError` / toast helpers instead of replacing the richer current UI.
- **Deploy via `hf` CLI**: Push only when runtime-facing changes are isolated per AGENTS.md.

---

## Implementation Units

- U1. **Runtime status and warmup priming in `index.html`**

**Goal:** Surface backend readiness and prime models before generation.

**Requirements:** R1, R2

**Dependencies:** None

**Files:**
- Modify: `index.html`

**Approach:**
- Add runtime status card CSS/HTML in sidebar.
- Add `refreshRuntimeStatus`, `ensureRuntimePrimed`, `runtimePrimed` state, interval polling.
- Call warmup before `startGeneration` queue join.

**Verification:**
- Cold Space shows “Cold”; after warmup, badge shows “Ready”.
- Network tab shows `/health` and `/warmup_runtime` before `/generate_3d`.

- U2. **Hardware transition and export profile UX**

**Goal:** Handle CPU standby gracefully and expose GLB texture budget control.

**Requirements:** R3, R4

**Dependencies:** U1

**Files:**
- Modify: `index.html`

**Approach:**
- Detect `generationResult.error` with `hardware_transition_requested` and show reload/retry guidance.
- Add export profile select + pass `texture_size` to `extract_glb_api`.
- Reuse `formatApiError` for preprocess/generate/export toasts.

**Verification:**
- CPU-mode response shows hardware-switch message (not “Unexpected response shape”).
- Export uses selected texture size parameter.

- U3. **Deploy and live Space browser verification**

**Goal:** Confirm hosted runtime matches source changes end-to-end.

**Requirements:** R5

**Dependencies:** U1, U2

**Files:**
- Modify: (deploy only if U1/U2 changed)

**Approach:**
- Push to HF Space with `hf` when working tree is clean for runtime files.
- Open live Space, run default sample through generate and GLB export.

**Verification:**
- Space build succeeds; sample image completes generation and export on live URL.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| ZeroGPU quota blocks full E2E | Verify at least health/warmup UI; document partial verification |
| Long cold-start | Use bundled sample; allow extended wait in browser test |

---

## Sources & References

- Origin: `.cursor/plans/pixal3d_space_recovery_5b65d5a8.plan.md`
- Backend: `app.py`, `index_bak.html`
- Agent policy: `AGENTS.md`
