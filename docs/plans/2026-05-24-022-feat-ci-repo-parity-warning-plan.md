---
title: "feat: CI repo parity warning on main push"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-021-feat-github-hf-parity-check-plan.md
---

# feat: CI repo parity warning on main push

## Summary

Run `scripts/check_repo_parity.py` on every push to `main` so drift between GitHub and the Hugging Face Space is visible in CI when `HF_TOKEN` auto-sync is skipped. The job warns but does not fail the workflow.

---

## Problem Frame

Plan 021 added a local parity CLI, but CI never runs it. When `HF_TOKEN` is absent, merges land on GitHub while the live Space falls behind until someone runs `git push origin main` manually.

---

## Requirements

- R1. New `repo-parity` job in `python-ci.yml` runs on push to `main` only.
- R2. Job adds the public HF Space git remote, fetches `main`, and runs `check_repo_parity.py` with `--github-remote origin --hf-remote hf-space`.
- R3. Job uses `continue-on-error: true` so drift warns without blocking merges.
- R4. README notes the CI parity warning behavior.

---

## Scope Boundaries

- Adding `HF_TOKEN` to GitHub (operator task)
- Failing CI on drift (sync may be intentionally deferred)

---

## Implementation Units

- U1. **Add repo-parity CI job**

**Goal:** Surface GitHub↔HF drift in Actions logs.

**Requirements:** R1–R3

**Files:** Modify `.github/workflows/python-ci.yml`

**Verification:** Job runs on main push; logs "Parity OK" or drift remedy when SHAs differ.

---

- U2. **Document CI parity warning**

**Goal:** Operators know where to look.

**Requirements:** R4

**Files:** Modify `README.md` (GitHub automation section)

**Verification:** README mentions `repo-parity` job and `continue-on-error` behavior.

---

## Sources & References

- `scripts/check_repo_parity.py`
- `.github/workflows/sync-hf-space.yml` skip-without-token gate
