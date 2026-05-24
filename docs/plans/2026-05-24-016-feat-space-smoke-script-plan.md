---
title: "feat: Agent-friendly Space smoke script"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-015-fix-gpu-abort-ux-plan.md
---

# feat: Agent-friendly Space smoke script

## Summary

Recovery U4 and repeated LFG runs need a repeatable, non-interactive way to verify the hosted Space without ad-hoc Python one-liners. Add `scripts/space_smoke.py` that checks `/health`, `/ready`, optional HTML markers, and optional sample generate via `gradio_client`, with clear exit codes for agents and CI-style smoke.

---

## Problem Frame

Live E2E on anonymous ZeroGPU cold start fails with `GPU task aborted` (~139s). UX mitigations shipped in PR #7. Verification still relies on manual curl/browser/venv scripts each session. AGENTS.md requires deploy + browser E2E but forbids adding unit tests unless requested — an operational smoke CLI is in scope.

---

## Requirements

- R1. `scripts/space_smoke.py` supports `--url` (default live Space), `--health-only`, and `--generate` (optional full predict).
- R2. Prints JSON summary to stdout; exit 0 on health checks pass; exit 1 on transport/health failure; exit 2 on generate failure.
- R3. `--html-check` verifies key UI markers in served `index.html` (runtime sign-in, GPU abort title string).
- R4. `--generate` uses `assets/images/0_img.png` and `api_name=/generate_3d` with ZeroGPU-safe step counts.
- R5. Mark recovery plan U4 `deploy-and-browser-verify` completed with pointer to smoke script (partial E2E: anonymous cold abort documented).

---

## Scope Boundaries

- Raising `@spaces.GPU` duration (quota-blocked for anonymous users)
- Pytest/unit tests (AGENTS.md)
- HF Space code deploy (script-only change)

---

## Implementation Units

- U1. **`scripts/space_smoke.py`**

**Goal:** Repeatable agent verification CLI.

**Requirements:** R1–R4

**Files:** Create `scripts/space_smoke.py`

**Approach:** stdlib `urllib` for health/ready/html; optional `gradio_client` import with clear error if missing; argparse with `--help` examples.

**Verification:** `python scripts/space_smoke.py --health-only --html-check` exits 0 against live Space.

---

- U2. **Close recovery plan U4**

**Goal:** Durable record that verification gate is operationalized.

**Requirements:** R5

**Files:** Modify `.cursor/plans/pixal3d_space_recovery_5b65d5a8.plan.md`

**Approach:** Set U4 todo `completed`; note smoke script + anonymous E2E partial outcome.

**Verification:** Plan frontmatter shows U4 completed.

---

- U3. **PR and local smoke run**

**Goal:** Land on `main` via PR.

**Dependencies:** U1, U2

**Verification:** CI lint passes; smoke script run recorded in PR body.

---

## Key Technical Decisions

- Script lives under `scripts/` not `tests/` to respect AGENTS.md test policy.
- Generate step is opt-in (`--generate`) because it consumes ZeroGPU quota.

---

## Sources & References

- `docs/plans/2026-05-24-015-fix-gpu-abort-ux-plan.md` E2E record
- AGENTS.md deploy/verify requirements
