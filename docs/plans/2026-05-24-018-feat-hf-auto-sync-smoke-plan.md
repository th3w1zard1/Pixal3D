---
title: "feat: Auto-sync HF Space on main push with post-sync smoke"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-017-feat-ci-space-smoke-sync-plan.md
---

# feat: Auto-sync HF Space on main push with post-sync smoke

## Summary

GitHub `main` and HF `origin/main` drifted because `sync-hf-space.yml` only runs when `HF_SPACE_AUTO_SYNC == 'true'` (unset). Enable sync on every push to `main` (opt-out via variable), expose resolved Space URL from config script, and run `space_smoke.py` after hub-sync with rebuild polling.

---

## Problem Frame

Manual `git push origin main` was required after each GitHub merge. CI already smoke-checks the live Space on PRs but does not verify the Space reflects the commit just synced from GitHub.

---

## Requirements

- R1. `sync-hf-space.yml` preflight/sync runs on `push` to `main` unless `HF_SPACE_AUTO_SYNC == 'false'`.
- R2. `resolve_hf_space_config.py` outputs `space_url` for `https://{namespace}-{name}.hf.space/`.
- R3. Post-sync job polls `space_smoke.py --health-only --html-check` against resolved URL after hub-sync.
- R4. Document opt-out in workflow comments; no README required.

---

## Scope Boundaries

- Changing HF Space SDK or secrets setup
- `--generate` post-sync (quota)

---

## Implementation Units

- U1. **Space URL helper + workflow auto-sync gate**

**Goal:** Reliable Space URL and default-on main sync.

**Requirements:** R1, R2

**Files:** `scripts/resolve_hf_space_config.py`, `.github/workflows/sync-hf-space.yml`

**Verification:** Script prints `space_url`; workflow YAML validates.

---

- U2. **Post-sync smoke job with rebuild polling**

**Goal:** Confirm synced Space serves expected HTML after deploy.

**Requirements:** R3

**Files:** `.github/workflows/sync-hf-space.yml`

**Verification:** Job structure valid; local smoke still passes.

---

- U3. **PR and merge**

**Dependencies:** U1, U2

**Verification:** CI passes including space-live-smoke on PR.

---

## Key Technical Decisions

- Default sync **on** for main push; repos without `HF_TOKEN` fail preflight clearly.
- Post-sync poll: up to ~2 min (8 × 15s) before failing.

---

## Sources & References

- `.github/workflows/sync-hf-space.yml` current `HF_SPACE_AUTO_SYNC` gate
- `scripts/space_smoke.py`
