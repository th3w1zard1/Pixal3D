---
title: "fix: clear idle viewer error and assert extract in smoke"
type: fix
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-033-feat-zerogpu-glb-extract-ux-plan.md
---

# fix: clear idle viewer error and assert extract in smoke

## Summary

Plans 027–033 restored ZeroGPU generate and GLB-only extract UX. Finish AGENTS.md’s “default sample” bar by ensuring the viewer error overlay never appears on a fresh load, extending `--generate` smoke to assert `extract_available` when a GLB is returned, and verifying the live Space with health/HTML smoke plus one gallery-sample browser run.

---

## Problem Frame

Anonymous `--generate` smoke passes with `glb_path` and `extract_available: true`, but `init()` never calls `hideViewerError()`, so a stale `.viewer-error.show` class (or tooling that reads hidden error copy) can imply failure before any run. Operator closure still lacks a smoke guard on `extract_available` and a documented default-sample browser check.

---

## Requirements

- R1. On page load, the viewer error overlay is hidden until `showViewerError` runs for a real failure.
- R2. `--generate` smoke fails when `glb_path` is present but `extract_available` is explicitly `false`.
- R3. Static HTML includes a stable marker tying the UI default smoke image to `assets/images/0_img.png`.
- R4. Deploy to HF Space; `check_repo_parity`, `--health-only --html-check`, and `--generate` pass; browser: click first gallery sample and confirm generate completes or shows actionable error (not idle empty overlay).

---

## Scope Boundaries

- New unit/regression tests in `tests/`
- Re-enabling preview frames on ZeroGPU
- CI `--generate` on every push

---

## Key Technical Decisions

- **Init reset:** Call `hideViewerError()` at end of `init()` after successful client connect — minimal, matches `startGeneration()` behavior.
- **Smoke contract:** When `glb_path` is set and `runtime_mode` is `zerogpu` (from pre-generate `/health`), require `extract_available is not False`.
- **HTML marker:** Add `data-smoke-default-sample="assets/images/0_img.png"` on `<body>` for `space_smoke.py` HTML checks (no behavior change).

---

## Implementation Units

- U1. **Viewer error init reset** — `index.html`: call `hideViewerError()` from `init()` after `setupUI()` / runtime refresh.

**Verification:** Fresh load has no `.viewer-error.show`; error still appears on failed generate.

- U2. **Smoke extract assertion** — `scripts/space_smoke.py`: after deliverable check, if `glb_path` and ZeroGPU health, assert `extract_available !== false`; add HTML marker to `HTML_MARKERS`.

**Verification:** Local logic review; live `--generate` passes.

- U3. **Body smoke marker** — `index.html`: `data-smoke-default-sample` on `<body>`.

**Verification:** `--health-only --html-check` includes new marker.

- U4. **Deploy and verify** — `hf` push when tree clean; `scripts/check_repo_parity.py`; health/html/generate smokes; browser gallery sample E2E.

**Verification:** All commands exit 0; browser shows step 3 with GLB or explicit error message (non-empty).

---

## System-Wide Impact

- **Unchanged:** Backend generate/export contracts from plan 033.
- **Smoke:** Stricter failure mode if backend regresses `extract_available`.

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| ZeroGPU quota blocks `--generate` | Retry once; report partial if health/html pass |
| Browser automation unavailable | Rely on smoke + manual note in PR |

---

## Sources & References

- Origin: `docs/plans/2026-05-24-033-feat-zerogpu-glb-extract-ux-plan.md`
- `AGENTS.md` browser + smoke verification requirements
