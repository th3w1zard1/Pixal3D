---
title: "feat: /ready-aware runtime card and Generate gating"
type: feat
status: active
date: 2026-05-24
origin: docs/plans/2026-05-23-011-feat-cpu-zerogpu-transition-plan.md
---

# feat: /ready-aware runtime card and Generate gating

## Summary

The backend exposes `/ready` (200 only when models are primed) but the UI only polls `/health`. Probe both endpoints together, reflect `initializing` accurately in the runtime card, poll faster while warming, and gate Generate on non-ZeroGPU paths until `/ready` succeeds.

---

## Problem Frame

PR #4 adds CPU standby detection and auto-reload. Users on dedicated GPU or cold non-ZeroGPU runtimes still see "Cold" while models initialize and can click Generate before `/ready` would pass, causing confusing warmup failures. README documents `/ready` but the frontend ignores it.

---

## Requirements

- R1. `refreshRuntimeStatus` probes `/health` and `/ready` in parallel; stores authoritative `runtimeReady` from `/ready` status.
- R2. Runtime badge shows `Warming` when `state === 'initializing'` or `/ready` is 503 with non-cpu health.
- R3. On non-ZeroGPU (`runtime_mode !== 'zerogpu'`), disable Generate until `runtimeReady` is true (CPU standby rules from PR #4 unchanged).
- R4. On ZeroGPU, keep allowing Generate when cold (generate self-primes in GPU slice).
- R5. Poll every 5s while warming (`!runtimeReady` and not cpu-standby); 15s when ready.
- R6. Deploy to HF Space; browser smoke on live `/ready` + sample → Generate.

---

## Scope Boundaries

- Backend API changes
- Full generate→GLB E2E (quota-dependent)
- Automated tests (AGENTS.md)

---

## Implementation Units

- U1. **Parallel /health + /ready probe**

**Goal:** Single refresh function merges both signals.

**Requirements:** R1, R2

**Files:** Modify `index.html`

**Approach:** `fetch` both in parallel; set `lastRuntimeReady` boolean from `/ready` ok status; prefer `initializing` badge when payload state says so.

**Verification:** Live `/ready` 503 → badge Warming; 200 → Ready when models loaded.

---

- U2. **Generate gating + adaptive poll for warming**

**Goal:** Prevent premature Generate on dedicated GPU; poll faster while warming.

**Requirements:** R3, R4, R5

**Files:** Modify `index.html`

**Approach:** Extend `updateGenerateAvailability` and `scheduleRuntimePollInterval` to consider `lastRuntimeReady` and `runtime_mode`.

**Verification:** Non-zerogpu cold → Generate disabled with tooltip; zerogpu cold + image → Generate enabled.

---

- U3. **Deploy and live browser smoke**

**Goal:** Ship and verify on HF Space.

**Requirements:** R6

**Dependencies:** U1, U2

**Verification:** Live Space serves updated markers; sample enables Generate on ZeroGPU.

---

## Key Technical Decisions

- **ZeroGPU exception:** Do not gate Generate on `/ready` for `runtime_mode === 'zerogpu'` — matches existing warmup-skip behavior.
- **No backend changes:** `/ready` already returns full `runtime_payload()`.

---

## Sources & References

- `app.py` `/ready` endpoint
- `README.md` readiness documentation
- PR #4 CPU standby UX
