---
title: "feat: Smoke marker for 512 ZeroGPU UI and HF_TOKEN runbook"
type: feat
status: active
date: 2026-05-24
origin: docs/plans/2026-05-24-024-feat-zerogpu-512-resolution-default-plan.md
---

# feat: Smoke marker for 512 ZeroGPU UI and HF_TOKEN runbook

## Summary

Extend live HTML smoke to assert the 512 ZeroGPU resolution option shipped in plan 024, and add a concise operator runbook for configuring `HF_TOKEN` so GitHub→HF auto-sync stops relying on manual pushes.

---

## Problem Frame

Plan 024 defaulted ZeroGPU resolution to 512 on the live Space, but CI smoke does not verify that string. Separately, `HF_TOKEN` is not configured in GitHub Actions, so every merge requires manual `git push origin main` until an operator adds the secret.

---

## Requirements

- R1. `scripts/space_smoke.py` HTML markers include `512 (Fast / ZeroGPU)`.
- R2. README documents how to add `HF_TOKEN` as a GitHub Actions secret and verify sync.
- R3. Live `space_smoke.py --health-only --html-check` passes after deploy.

---

## Scope Boundaries

- Setting HF_TOKEN in GitHub (operator action)
- Failing CI when HF_TOKEN is missing
- Anonymous full generate E2E success

---

## Implementation Units

- U1. **512 resolution smoke marker**

**Requirements:** R1

**Files:** Modify `scripts/space_smoke.py`

**Verification:** `--html-check` passes on live Space.

---

- U2. **HF_TOKEN operator runbook**

**Requirements:** R2

**Files:** Modify `README.md`

**Verification:** README lists secret name, HF token scope, and verification commands.

---

## Sources & References

- Plan 024 `index.html` resolution option
- `.github/workflows/sync-hf-space.yml`
