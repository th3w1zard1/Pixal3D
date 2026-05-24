---
title: "fix: Align README with CI smoke and HF auto-sync"
type: fix
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-018-feat-hf-auto-sync-smoke-plan.md
---

# fix: Align README with CI smoke and HF auto-sync

## Summary

README still documents the old sync gate (`HF_SPACE_AUTO_SYNC=true` required, hard fail without `HF_TOKEN`). Update automation docs to match current behavior: default-on main sync, skip when token missing, live smoke in CI, and `scripts/space_smoke.py`.

---

## Problem Frame

Agents and contributors reading README get wrong rollout steps. CI and AGENTS.md already reference `space_smoke.py`; README does not.

---

## Requirements

- R1. README lists `space-live-smoke` CI job and `scripts/space_smoke.py` verification command.
- R2. README states main-push sync is default-on unless `HF_SPACE_AUTO_SYNC=false`.
- R3. README states push skips sync when `HF_TOKEN` missing; manual dispatch requires token.
- R4. README mentions post-sync smoke polling in `sync-hf-space.yml`.

---

## Scope Boundaries

- Runtime code changes
- Adding HF_TOKEN to GitHub (operator task)

---

## Implementation Units

- U1. **Update README GitHub automation sections**

**Goal:** Accurate sync and verification docs.

**Requirements:** R1–R4

**Files:** Modify `README.md`

**Verification:** README text matches `.github/workflows/*.yml` and AGENTS.md.

---

- U2. **PR merge**

**Dependencies:** U1

**Verification:** CI passes.

---

## Sources & References

- `.github/workflows/python-ci.yml`, `sync-hf-space.yml`
- `AGENTS.md`, `scripts/space_smoke.py`
