---
title: "feat: hosted verification script and browser GLB proof"
type: feat
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# feat: hosted verification script and browser GLB proof

## Summary

Recovery is closed; operators still run four separate commands. Add `scripts/verify_hosted_space.sh` that runs parity + health/HTML smoke in order (optional `--generate`), attempt browser default-sample GLB when quota allows, and update `docs/SPACE_RECOVERY.md` with the outcome.

---

## Problem Frame

Repeated manual verification is error-prone (CLI generate before browser exhausts quota). A single script reduces drift; browser GLB proof remains the only open verification gap when quota resets.

---

## Requirements

- R1. `scripts/verify_hosted_space.sh` runs parity, `--health-only --html-check`, and supports `--generate` flag.
- R2. Script prints verification order reminder and exits non-zero on first failure.
- R3. `README.md` and `docs/SPACE_RECOVERY.md` reference the script.
- R4. Browser E2E attempted before any `--generate` in this session.
- R5. Record browser outcome in `SPACE_RECOVERY.md` (pass with GLB or quota note).

---

## Scope Boundaries

- Automating browser (Playwright) in CI
- Unit tests for shell script

---

## Implementation Units

- U1. **verify_hosted_space.sh** — parity + smoke; `--generate` optional.
- U2. **Docs** — README + SPACE_RECOVERY links and usage.
- U3. **Browser GLB** — live default-sample attempt (no prior CLI generate).
- U4. **Ship** — branch, PR, merge, parity push if needed.
