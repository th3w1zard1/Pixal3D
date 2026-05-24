---
title: "feat: browser default-sample GLB E2E and recovery closure"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-036-feat-final-e2e-verification-gate-plan.md
---

# feat: browser default-sample GLB E2E and recovery closure

## Summary

Plans 027–036 restored hosted ZeroGPU generate and operator docs. AGENTS.md still requires a live browser run with the default sample. Complete that path (browser before CLI `--generate` to avoid quota contention), record the outcome in `docs/SPACE_RECOVERY.md`, and mark the recovery track closed.

---

## Problem Frame

CLI `--generate` smoke passes, but the last browser attempts failed on ZeroGPU quota immediately after CLI smoke consumed the daily slice. Operators need a documented verification order and a recorded browser GLB success (or explicit quota-blocked outcome with full error copy).

---

## Requirements

- R1. Browser E2E runs **before** CLI `--generate` in this session.
- R2. Browser: idle viewer error hidden; gallery `0_img.png` → Generate at 512 → step 3 shows GLB viewer **or** non-empty quota/error message.
- R3. `docs/SPACE_RECOVERY.md` updated with browser verification outcome and recommended order (browser first when testing both).
- R4. `AGENTS.md` references `docs/SPACE_RECOVERY.md` for hosted verification checklist.
- R5. Recovery status marked **closed** when R2–R4 satisfied.

---

## Scope Boundaries

- New unit tests
- Runtime code changes unless browser finds a regression
- HF_TOKEN setup

---

## Implementation Units

- U1. **AGENTS recovery pointer** — `AGENTS.md`: link `docs/SPACE_RECOVERY.md`.

- U2. **Recovery closure doc** — `docs/SPACE_RECOVERY.md`: verification order, browser outcome stamp, status closed.

- U3. **Browser E2E** — live Space default-sample generate (no prior `--generate` in session).

- U4. **CLI smoke** — run `--generate` only after browser, if quota remains.

- U5. **Ship** — commit on branch, PR, merge if CI green; parity unchanged (docs only).

---

## Risks

| Risk | Mitigation |
|------|------------|
| Quota blocks browser | Record full error text; CLI may still pass on another day |
