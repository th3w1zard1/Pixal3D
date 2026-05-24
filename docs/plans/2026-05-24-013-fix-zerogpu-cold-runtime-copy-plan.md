---
title: "fix: ZeroGPU cold-start runtime card messaging"
type: fix
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-012-feat-ready-endpoint-ui-plan.md
---

# fix: ZeroGPU cold-start runtime card messaging

## Summary

Plan 012 correctly gates Generate on `/ready` for non-ZeroGPU runtimes but also relabels ZeroGPU cold start as "Warming" with copy implying Generate is locked. Fix runtime card badge and text for `runtime_mode === 'zerogpu'` when `/ready` is 503 so users know they can start Generate immediately.

---

## Problem Frame

On the live Space, `/health` reports `runtime_mode: zerogpu`, `state: pending`, `ready: false`, and `warmup_on_start: false`. That is expected — models load on the first GPU slice. The UI currently shows the Warming badge and "Generate unlocks when ready", which contradicts ZeroGPU behavior where Generate is enabled and self-primes.

---

## Requirements

- R1. When `runtime_mode === 'zerogpu'` and `/ready` is not OK, runtime badge stays **Cold** (not Warming).
- R2. Runtime card copy explains that the first Generate loads models in a GPU slice; do not imply Generate is disabled.
- R3. Non-ZeroGPU `/ready` gating and Warming badge from plan 012 remain unchanged.
- R4. Deploy to HF Space; browser smoke confirms sample → Generate enabled with corrected copy.

---

## Scope Boundaries

- Backend warmup policy changes
- Full generate→GLB E2E (quota-dependent)
- Automated tests (AGENTS.md)

---

## Implementation Units

- U1. **ZeroGPU-specific runtime card state and copy**

**Goal:** Accurate badge and message for ZeroGPU cold start.

**Requirements:** R1, R2, R3

**Files:** Modify `index.html`

**Approach:** Only promote `pending` → `initializing` when `runtime_mode !== 'zerogpu'`. Add ZeroGPU branch in runtime status text before the generic warming message.

**Verification:** Live Space with `/ready` 503 + `runtime_mode: zerogpu` shows Cold badge and cold-start copy; Generate enabled with sample image.

---

- U2. **Deploy and live browser smoke**

**Goal:** Ship and verify on HF Space.

**Requirements:** R4

**Dependencies:** U1

**Verification:** Served HTML includes updated copy; sample → Generate enabled.

---

## Key Technical Decisions

- **ZeroGPU exception preserved:** No change to `updateGenerateAvailability` or `startGeneration` guards — only runtime card presentation.

---

## Sources & References

- `docs/plans/2026-05-24-012-feat-ready-endpoint-ui-plan.md`
- Live `/health` on `th3w1zard1/Pixal3D` (2026-05-24): zerogpu + pending + warmup_on_start false
