---
title: "feat: ZeroGPU cold fast-poll and proactive sign-in link"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-013-fix-zerogpu-cold-runtime-copy-plan.md
---

# feat: ZeroGPU cold fast-poll and proactive sign-in link

## Summary

After plan 013 fixed ZeroGPU cold copy, two UX gaps remain: the runtime card polls every 15s on ZeroGPU cold (slow to flip to Ready after first Generate), and quota guidance only appears reactively on errors. Fast-poll while ZeroGPU is cold and add a sign-in link beside the GPU budget hint.

---

## Problem Frame

Live Space reports `runtime_mode: zerogpu`, `/ready` 503, `warmup_on_start: false`. Users can Generate immediately, but the badge stays Cold for up to 15s after models load. Quota/sign-in guidance is buried in error toasts instead of the runtime card where users decide whether to run Generate.

---

## Requirements

- R1. Poll `/health` + `/ready` every 5s when `runtime_mode === 'zerogpu'` and `/ready` is not OK; restore 15s when ready.
- R2. Show a sign-in link in the runtime card when on ZeroGPU (reuse HF login URL from viewer error CTA).
- R3. No backend changes; preserve `@gradio/client` transport.
- R4. Deploy to HF Space; browser smoke: budget hint + sign-in link visible; sample → Generate enabled.

---

## Scope Boundaries

- Full generate→GLB E2E (quota-dependent; attempt during verify, document outcome)
- Automated tests (AGENTS.md)

---

## Implementation Units

- U1. **Fast-poll ZeroGPU cold until ready**

**Goal:** Runtime badge updates within ~5s after first successful GPU warm.

**Requirements:** R1

**Files:** Modify `index.html` (`scheduleRuntimePollInterval`)

**Approach:** Extend fast-poll branch to include `runtime_mode === 'zerogpu' && !lastRuntimeReady`.

**Verification:** After generate completes on warm Space, badge moves to Ready within one fast poll cycle.

---

- U2. **Proactive sign-in link in runtime card**

**Goal:** Surface HF sign-in before quota errors.

**Requirements:** R2

**Files:** Modify `index.html` (runtime card HTML, CSS, `updateRuntimeBudgetHint`)

**Approach:** Add `#runtime-signin-link` anchor next to budget hint; show when `runtime_mode === 'zerogpu'`.

**Verification:** Live Space shows link on ZeroGPU; hidden on non-ZeroGPU.

---

- U3. **Deploy and live browser smoke**

**Goal:** Ship and verify on HF Space.

**Requirements:** R4

**Dependencies:** U1, U2

**Verification:** Served HTML includes sign-in link; sample enables Generate; optional generate attempt documented.

---

## Key Technical Decisions

- Reuse `https://huggingface.co/login` from existing viewer sign-in CTA for consistency.
- Sign-in link lives in runtime card, not budget hint textContent, to avoid HTML injection via string concat.

---

## Sources & References

- `index.html` viewer-error-signin pattern (PR #1)
- Live `/health` zerogpu cold state (2026-05-24)
