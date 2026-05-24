---
title: "feat: ship plan 034 — merge PR, parity, recovery closure"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-034-fix-viewer-error-init-smoke-extract-plan.md
---

# feat: ship plan 034 — merge PR, parity, recovery closure

## Summary

Plan 034 is implemented on branch `fix/viewer-error-init-smoke-extract` (PR #28, CI green) and already deployed to HF `origin/main` at `5a3a8c8`. Close the recovery track by merging PR #28 into `github/main`, syncing GitHub to HF, adding a short operator recovery doc, and re-running live smokes plus a default-sample browser check.

---

## Problem Frame

HF Space runs plan-034 code while GitHub `main` lags at `a4bc897`, so `check_repo_parity.py` fails and the open PR blocks formal closure. AGENTS.md requires parity and live verification before declaring the hosted path done.

---

## Requirements

- R1. Merge PR #28 into `github/main` when CI is green.
- R2. `github/main` and HF `origin/main` match (`check_repo_parity.py` exits 0).
- R3. Add `docs/SPACE_RECOVERY.md` summarizing recovery outcomes and verification commands (plans 027–034).
- R4. Live `--health-only --html-check` passes on deployed Space.
- R5. Browser: fresh load hides viewer error; gallery `0_img.png` → generate completes with GLB **or** shows non-empty quota/error copy.

---

## Scope Boundaries

- New unit tests
- CI `--generate` on every push
- HF_TOKEN secret setup (document only)

---

## Implementation Units

- U1. **Merge PR #28** — `gh pr merge 28 --squash` (or merge commit if repo policy requires).

**Verification:** `github/main` contains plan-034 commits.

- U2. **Sync HF origin** — `git checkout main && git pull github main && git push origin main`.

**Verification:** `python3 scripts/check_repo_parity.py` exits 0.

- U3. **Recovery closure doc** — create `docs/SPACE_RECOVERY.md` with status, live URL, smoke commands, and pointer to plans 027–034.

**Verification:** File present in merged tree.

- U4. **Live verify** — health/html smoke; optional `--generate` if quota allows.

**Verification:** smoke exit 0.

- U5. **Browser sample check** — navigate Space, confirm idle error hidden, click first gallery item, attempt generate.

**Verification:** GLB on step 3 or actionable error message (not empty overlay).

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| ZeroGPU quota exhausted | Document in PR; health/html still pass |
| `gh pr merge` blocked | Report and stop before DONE |

---

## Sources & References

- PR https://github.com/th3w1zard1/Pixal3D/pull/28
- `docs/plans/2026-05-24-034-fix-viewer-error-init-smoke-extract-plan.md`
