---
title: "feat: Complete live Pixal3D Space E2E verification"
type: feat
status: active
date: 2026-05-23
origin: docs/plans/2026-05-23-001-feat-space-frontend-e2e-plan.md
---

# feat: Complete live Pixal3D Space E2E verification

## Summary

Finish the open verification gate from the frontend runtime UX slice by running a full hosted smoke test on `th3w1zard1/Pixal3D`: sample image upload, `warmup_runtime` + `generate_3d`, preview frames, and `extract_glb_api` export. Fix only blockers discovered during the live run.

---

## Problem Frame

PR #1 and plan `2026-05-23-001` landed runtime readiness UI and deployed to the Hugging Face Space, but the live cold/warm generate → GLB export path was not completed in-session. AGENTS.md requires browser verification on the real Space before declaring the slice done.

---

## Requirements

- R1. Live Space loads updated `index.html` with runtime card and export profile controls.
- R2. Default sample image completes preprocess + generation on ZeroGPU without opaque client errors.
- R3. GLB export succeeds with balanced (2K) profile and produces a viewable asset.
- R4. PR #1 test plan updated with verification evidence; blockers fixed in-repo if found.

---

## Scope Boundaries

- No new unit tests unless a concrete bug fix requires one and user policy allows it.
- No unrelated refactors or dependency churn.
- Fix only issues that block the hosted smoke path.

---

## Implementation Units

- U1. **Live browser smoke on hosted Space**

**Goal:** Execute end-to-end flow on https://th3w1zard1-pixal3d.hf.space/

**Requirements:** R1, R2, R3

**Files:** None unless blockers found

**Verification:** Sample gallery item → Generate → Preview step → Export GLB → Result step with model loaded

- U2. **Fix live blockers (conditional)**

**Goal:** Patch minimal runtime/UI/backend issues if smoke fails

**Requirements:** R2, R3

**Dependencies:** U1 failure signals

**Files:** `index.html`, `app.py`, or bootstrap modules as needed

**Verification:** Re-run failed step successfully on live Space

- U3. **Record verification and sync PR**

**Goal:** Document evidence and update PR #1 checklist

**Requirements:** R4

**Dependencies:** U1 or U2

**Files:** PR body via `gh pr edit`; optional note in plan frontmatter

**Verification:** PR test plan shows completed live smoke with timestamp and Space URL

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| ZeroGPU quota / long cold start | Allow extended waits; use 1024 + balanced export profile |
| Space rebuild lag | Confirm deployed HTML markers before testing |
