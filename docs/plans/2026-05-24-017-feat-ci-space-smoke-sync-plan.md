---
title: "feat: CI live Space smoke and HF main sync"
type: feat
status: active
date: 2026-05-24
origin: docs/plans/2026-05-24-016-feat-space-smoke-script-plan.md
---

# feat: CI live Space smoke and HF main sync

## Summary

`scripts/space_smoke.py` landed on `github/main` but HF `origin/main` is behind (`a92cb93` vs `8e58fbf`). Wire the smoke script into CI for repeatable live checks, add it to syntax-smoke `py_compile`, document the path in AGENTS.md, and sync HF Space to GitHub main.

---

## Problem Frame

LFG runs manually invoke smoke checks; CI does not yet run them. HF Space deploy lags GitHub after script-only merges because those commits were not pushed to `origin`. Agents following AGENTS.md lack an explicit pointer to the smoke CLI.

---

## Requirements

- R1. `syntax-smoke` job compiles `scripts/space_smoke.py`.
- R2. New CI job runs `python scripts/space_smoke.py --health-only --html-check` against the live Space on PR and push to `main`.
- R3. AGENTS.md references `scripts/space_smoke.py` as the hosted verification path.
- R4. HF `origin/main` synced to `github/main` after merge.

---

## Scope Boundaries

- `--generate` in CI (quota-consuming)
- Unit tests (AGENTS.md)

---

## Implementation Units

- U1. **CI smoke job + py_compile**

**Goal:** Automate live health/html verification.

**Requirements:** R1, R2

**Files:** Modify `.github/workflows/python-ci.yml`

**Verification:** Workflow YAML valid; smoke command exits 0 locally.

---

- U2. **AGENTS.md verification pointer**

**Goal:** Agents use smoke script by default.

**Requirements:** R3

**Files:** Modify `AGENTS.md`

**Verification:** AGENTS mentions `scripts/space_smoke.py`.

---

- U3. **Sync HF origin/main**

**Goal:** Space runtime matches GitHub main.

**Requirements:** R4

**Dependencies:** U1, U2 merged or pushed on branch then sync after merge

**Verification:** `git rev-parse github/main origin/main` match after sync.

---

## Key Technical Decisions

- Live smoke hits public `/health` and `/` only — no GPU quota use.
- Job runs on PR and main push; failures surface Space outages or stale deploys.

---

## Sources & References

- `scripts/space_smoke.py`
- Remote drift: `github/main` `8e58fbf` vs `origin/main` `a92cb93`
