---
title: "feat: GitHub–HF Space repo parity check"
type: feat
status: active
date: 2026-05-24
origin: docs/plans/2026-05-24-018-feat-hf-auto-sync-smoke-plan.md
---

# feat: GitHub–HF Space repo parity check

## Summary

Add a small CLI that compares `github/main` and `origin/main` SHAs so agents and operators can detect GitHub↔Hugging Face drift before claiming deploy complete. Document usage in AGENTS.md and sync the live Space when local `hf` auth is available.

---

## Problem Frame

`github/main` (`9ed693a`) is ahead of HF `origin/main` (`80ee561`) because GitHub Actions skips hub-sync without `HF_TOKEN`. Agents following AGENTS.md need a deterministic way to spot drift; manual `git push origin main` remains the fallback when CI sync is skipped.

---

## Requirements

- R1. `scripts/check_repo_parity.py` fetches `github` and `origin`, prints both SHAs and commit delta count, exits 0 when equal and 1 when diverged.
- R2. `AGENTS.md` and README mention the parity check before closing hosted tasks.
- R3. Script included in `python-ci.yml` py_compile list.
- R4. When local HF auth works, push `github/main` to `origin/main` to close current drift.

---

## Scope Boundaries

- Adding `HF_TOKEN` to GitHub secrets (operator task)
- Failing CI on drift (informational script only; sync may be intentionally skipped)

---

## Implementation Units

- U1. **Parity check script**

**Goal:** Detect github vs origin main drift.

**Requirements:** R1

**Files:** Create `scripts/check_repo_parity.py`; modify `.github/workflows/python-ci.yml` py_compile list

**Approach:** `git fetch github origin --quiet`; compare `refs/remotes/github/main` and `refs/remotes/origin/main`; list commits unique to each side when diverged.

**Test expectation:** none — operational script per AGENTS.md.

**Verification:** Script exits 1 today (known drift), 0 after sync.

---

- U2. **Document parity workflow**

**Goal:** Agents run parity before declaring hosted work done.

**Requirements:** R2

**Files:** Modify `AGENTS.md`, `README.md` (GitHub automation section)

**Verification:** Docs reference `python scripts/check_repo_parity.py`.

---

- U3. **Sync HF Space and verify**

**Goal:** Close current drift when push is safe.

**Requirements:** R4

**Dependencies:** U1

**Files:** none (git push to `origin`)

**Verification:** Parity script exits 0; `space_smoke.py --health-only --html-check` passes.

---

## Sources & References

- Remotes: `github` → GitHub, `origin` → HF Space
- `.github/workflows/sync-hf-space.yml` skip-without-token behavior
- Plan 018 post-sync smoke pattern
