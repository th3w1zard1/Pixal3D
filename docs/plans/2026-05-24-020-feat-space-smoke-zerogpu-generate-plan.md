---
title: "feat: ZeroGPU-safe space_smoke generate path"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-016-feat-space-smoke-script-plan.md
---

# feat: ZeroGPU-safe space_smoke generate path

## Summary

Improve `scripts/space_smoke.py --generate` so agent E2E checks mirror the hosted UI: call `warmup_runtime` in its own GPU slice before `generate_3d`, use ZeroGPU-capped parameters (512 resolution, 5 stage steps), and document anonymous cold-start limits.

---

## Problem Frame

Anonymous `--generate` on the live Space fails after ~139s with `GPU task aborted` because cold model load and inference share one ZeroGPU slice. The UI already calls `warmup_runtime` first; the smoke script does not. Recovery U4 is closed as partial; this makes the smoke path align with production behavior.

---

## Requirements

- R1. `--generate` calls `/warmup_runtime` before `/generate_3d`.
- R2. `--generate` uses ZeroGPU-safe defaults: 512 resolution, 5 sampling steps per stage, fast-profile-aligned settings.
- R3. Script help and AGENTS.md note that anonymous cold runs may still abort; sign-in improves quota.
- R4. Live verify: `--health-only --html-check` still passes; optional `--generate` attempted and outcome documented.

---

## Scope Boundaries

- Changing ZeroGPU duration caps in `app.py`
- Adding unit tests (repo policy: no tests unless requested)
- Authenticated generate CI (needs secrets)

---

## Implementation Units

- U1. **Prime warmup and ZeroGPU-safe generate in space_smoke**

**Goal:** Separate cold load from generation in smoke CLI.

**Requirements:** R1, R2

**Files:** Modify `scripts/space_smoke.py`

**Approach:**
- Add `run_warmup()` using `client.predict("/warmup_runtime", session_id=...)`.
- Align `run_generate()` positional args with UI defaults capped for ZeroGPU (512, step count 5).
- Return structured errors when warmup or generate fails.

**Test expectation:** none — operational smoke script per AGENTS.md.

**Verification:** Script runs without import errors; warmup invoked before generate when `--generate` set.

---

- U2. **Document smoke generate expectations**

**Goal:** Agents know limits of anonymous generate.

**Requirements:** R3

**Files:** Modify `AGENTS.md`, `scripts/space_smoke.py` epilog

**Verification:** Docs mention warmup-first and quota caveat.

---

- U3. **Deploy and live verify**

**Goal:** Runtime-facing script change deployed when safe; smoke health check passes.

**Requirements:** R4

**Dependencies:** U1, U2

**Verification:** `python scripts/space_smoke.py --health-only --html-check` exit 0 on live Space.

---

## Sources & References

- `scripts/space_smoke.py`, `index.html` (`ensureRuntimePrimed`, export fast profile)
- `app.py` ZeroGPU caps (`ZEROGPU_*` constants)
- Plan 016 partial E2E outcome
