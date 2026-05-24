---
title: "fix: ZeroGPU cold-start GPU abort UX and E2E verification record"
type: fix
status: completed
date: 2026-05-24
origin: .cursor/plans/pixal3d_space_recovery_5b65d5a8.plan.md
verified_e2e: "2026-05-24 anonymous cold generate → GPU task aborted (~139s); UX mitigations shipped"
---

# fix: ZeroGPU cold-start GPU abort UX and E2E verification record

## Summary

Live E2E via `gradio_client` on `th3w1zard1-pixal3d.hf.space` failed after ~139s with `GPU task aborted` on anonymous ZeroGPU cold start. Improve runtime and error UX for this failure mode, add return URL to the runtime sign-in link, and document verification outcomes to close recovery plan U4 (partial: UX verified; full GLB blocked on quota/slice).

---

## Problem Frame

Recovery plan U4 remains open. Runtime UX PRs #1–#6 landed, but anonymous cold Generate still aborts when model load exceeds the hosted GPU slice. Users see a generic "Generation could not complete" title and the runtime sign-in link does not return them to the Space after login.

---

## Requirements

- R1. Runtime sign-in link uses `https://huggingface.co/login?next=<current Space URL>`.
- R2. ZeroGPU cold runtime copy warns that the first Generate may abort if cold load exceeds the hosted slice; points to sign-in.
- R3. Viewer error for `GPU task aborted` uses title **GPU slice ended early** and actionable copy (sign-in / retry after reset).
- R4. Quota exceeded errors keep existing title and sign-in CTA behavior.
- R5. Deploy to HF Space; browser smoke confirms updated copy and sign-in URL pattern.

---

## Scope Boundaries

- Increasing `@spaces.GPU` duration (quota trade-off; separate issue)
- Automated CI E2E tests (AGENTS.md)
- Full anonymous generate→GLB success (blocked on HF ZeroGPU quota/slice)

---

## Implementation Units

- U1. **Sign-in return URL + cold-start copy**

**Goal:** Proactive and reactive sign-in flows return to the Space; cold copy sets expectations.

**Requirements:** R1, R2

**Files:** Modify `index.html`

**Approach:** Set `runtime-signin-link.href` in `updateRuntimeBudgetHint`; extend ZeroGPU cold `runtime-status-text`.

**Verification:** Served HTML link includes `login?next=`; cold copy mentions first-run abort risk.

---

- U2. **GPU abort viewer error title**

**Goal:** Distinguish slice abort from generic generation failure.

**Requirements:** R3, R4

**Files:** Modify `index.html` (`showViewerError` callers or helper)

**Approach:** When error text matches `/GPU task aborted/i`, pass title `GPU slice ended early`.

**Verification:** Simulated error path sets correct title (source inspection + live if abort reproduces).

---

- U3. **Deploy, browser smoke, record E2E outcome**

**Goal:** Ship and document recovery U4 partial closure.

**Requirements:** R5

**Dependencies:** U1, U2

**Files:** Plan documents only for E2E record

**Verification:** Live Space serves changes; plan notes 2026-05-24 E2E: `GPU task aborted` at ~139s anonymous cold.

---

## Key Technical Decisions

- Do not raise GPU duration in this slice — prior plans established quota constraints; UX guidance is the safe fix.
- Record U4 as **partial**: browser smoke + generate attempt documented; full GLB requires authenticated quota.

---

## Sources & References

- Live E2E attempt 2026-05-24: `gradio_client.predict(api_name="/generate_3d")` → `AppError GPU task aborted` (~139s)
- Recovery plan U4: `.cursor/plans/pixal3d_space_recovery_5b65d5a8.plan.md`
