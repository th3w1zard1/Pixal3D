---
title: "feat: CPU standby → ZeroGPU transition UX"
type: feat
status: active
date: 2026-05-23
origin: docs/plans/2026-05-23-001-feat-space-frontend-e2e-plan.md
---

# feat: CPU standby → ZeroGPU transition UX

## Summary

When the Hugging Face Space boots on CPU standby, the UI still allows Generate and only surfaces a manual-reload message after a failed warmup. Detect `cpu-standby` from `/health`, gate Generate with clear copy, poll faster while waiting, and auto-reload once `runtime_mode` becomes `zerogpu`.

---

## Problem Frame

PRs #1–#3 merged runtime visibility, export defaults, and budget hints. CPU→ZeroGPU hardware switches still leave users on a stale page: `buildTransitionMessage` tells them to reload manually, and `/health` polling at 15s is too slow to catch the transition. Generate is not disabled during `cpu-standby`, so users hit opaque failures.

---

## Requirements

- R1. When `/health` reports `state: cpu-standby` or `runtime_mode: cpu`, runtime card shows CPU standby badge/copy and Generate stays disabled with explanation.
- R2. While in CPU standby, poll `/health` every 5s (restore 15s after transition).
- R3. When `runtime_mode` changes from `cpu` to `zerogpu`, show a short toast/banner and auto-reload the page within ~3s (once per session).
- R4. No backend API changes; preserve `@gradio/client` transport.
- R5. Deploy to HF Space; browser smoke on live `/health` states.

---

## Scope Boundaries

- Full anonymous generate→GLB E2E (quota-dependent; separate verification pass)
- Backend hardware-switch orchestration (HF platform concern)
- Automated CI browser tests (AGENTS.md defers unless requested)

---

## Context & Research

### Relevant Code and Patterns

- `index.html` — `refreshRuntimeStatus()`, `buildTransitionMessage()`, 15s `setInterval`
- `app.py` — `runtime_payload()` sets `state: cpu-standby`, `runtime_mode: cpu`, `ready: false` on CPU

### Key Technical Decisions

- **Frontend-only:** `/health` already exposes `runtime_mode`, `state`, `message`, `target_hardware`; no new endpoints.
- **Auto-reload once:** Use `sessionStorage` flag to avoid reload loops if user returns to CPU.
- **Generate gating:** Centralize in `refreshRuntimeStatus` + small helper rather than scattering in upload handler.

---

## Implementation Units

- U1. **CPU standby runtime card + Generate gate**

**Goal:** Reflect CPU standby in UI and prevent premature Generate.

**Requirements:** R1

**Dependencies:** None

**Files:**
- Modify: `index.html`

**Approach:**
- Extend `refreshRuntimeStatus` state map with `cpu-standby` label
- Add `updateGenerateAvailability(health)` helper: disable Generate + title/tooltip when CPU standby unless image missing
- Re-call after upload when health still CPU standby

**Test scenarios:**
- Happy path: `/health` with `state: cpu-standby` → badge "CPU Standby", Generate disabled
- Edge case: user uploads image on CPU standby → Generate remains disabled
- Happy path: `/health` with `runtime_mode: zerogpu`, `ready: true` → Generate enabled when image present

**Verification:**
- Manual browser: mock or live CPU standby shows gated Generate

---

- U2. **Faster poll + auto-reload on ZeroGPU transition**

**Goal:** Detect hardware switch without manual reload.

**Requirements:** R2, R3

**Dependencies:** U1

**Files:**
- Modify: `index.html`

**Approach:**
- Track `lastObservedRuntimeMode` across polls
- When mode was `cpu` and becomes `zerogpu`, toast "GPU runtime ready — reloading…" and `setTimeout(location.reload, 3000)`
- Adjust poll interval: 5s while `runtime_mode === 'cpu'`, else 15s
- Set `sessionStorage.setItem('pixal3d_zerogpu_reload', '1')` before reload to skip repeat

**Test scenarios:**
- Integration: simulate mode flip in devtools by stubbing fetch → auto-reload fires once
- Edge case: already on zerogpu at load → no reload

**Verification:**
- Transition detection logic present; live verify if Space is on CPU at test time

---

- U3. **Deploy and live browser smoke**

**Goal:** Ship to HF Space and confirm runtime card behavior live.

**Requirements:** R5

**Dependencies:** U1, U2

**Files:**
- Deploy: git push `origin main` (or feature branch → PR)

**Approach:**
- Push to HF; poll live `/health` and load Space in browser
- Confirm budget hint still visible on ZeroGPU; sample → Generate enabled

**Test scenarios:**
- Happy path: live `/health` returns 200 with expected fields
- Happy path: sample gallery enables Generate on warm ZeroGPU Space

**Verification:**
- Live Space reflects new transition UX markers in HTML/behavior

---

## System-Wide Impact

- **Unchanged invariants:** `warmup_runtime` skip on ZeroGPU, export profiles, sign-in CTA, budget hint
- **Interaction graph:** Only `/health` polling frequency and Generate button gating change

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| Auto-reload disrupts in-progress upload | Reload only on cpu→zerogpu flip; not while `isPreprocessing` or generation active |
| Space already on ZeroGPU at visit | No reload; normal flow |

---

## Sources & References

- Origin: `docs/plans/2026-05-23-001-feat-space-frontend-e2e-plan.md`
- Related: PR #1 CPU transition messaging
- `AGENTS.md` — deploy + browser verify before done
