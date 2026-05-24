---
title: "feat: final E2E verification gate and operator surfacing"
type: feat
status: active
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# feat: final E2E verification gate and operator surfacing

## Summary

Recovery code is merged and parity-aligned. Close the hosted path by recording a fresh anonymous `--generate` success, linking `docs/SPACE_RECOVERY.md` from README, adding a manual CI `workflow_dispatch` generate smoke job, and completing a browser gallery-sample generate on the live Space.

---

## Problem Frame

Plans 027–035 fixed runtime, smoke, and merge/parity, but AGENTS.md still requires a live default-sample browser check and durable operator docs. Anonymous `--generate` had been blocked by quota; it now passes again and should be recorded.

---

## Requirements

- R1. `docs/SPACE_RECOVERY.md` records last verified date and anonymous `--generate` outcome.
- R2. `README.md` links to `docs/SPACE_RECOVERY.md` from runtime/operator section.
- R3. `.github/workflows/python-ci.yml` exposes optional `workflow_dispatch` job running `space_smoke.py --generate`.
- R4. Live `--health-only --html-check` and `--generate` pass after any deploy.
- R5. Browser: gallery `0_img.png` → Generate completes with GLB on step 3 or explicit non-empty error.

---

## Scope Boundaries

- Unit tests
- Setting `HF_TOKEN` in GitHub (document only)
- Running `--generate` on every PR push

---

## Implementation Units

- U1. **Recovery doc verification stamp** — update `docs/SPACE_RECOVERY.md` with verification date and smoke result fields.

- U2. **README recovery link** — add link near Space verification / CI section in `README.md`.

- U3. **Manual CI generate smoke** — extend `python-ci.yml` with `workflow_dispatch` and `space-generate-smoke` job.

- U4. **Deploy and CLI verify** — push to HF if runtime-facing files change; run parity, health/html, `--generate`.

- U5. **Browser default-sample E2E** — live Space: idle error hidden, click first gallery sample, Generate at 512, confirm GLB viewer or actionable error.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Quota exhausts mid-browser run | CLI smoke already passed; document browser outcome |
