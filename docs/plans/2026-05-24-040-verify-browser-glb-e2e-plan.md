---
title: "verify: browser default-sample GLB end-to-end"
type: feat
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# verify: browser default-sample GLB end-to-end

## Summary

Recovery is closed and CLI smoke passes. The only open verification gap is browser gallery → GLB. Run browser E2E first (no CLI `--generate` in session) and update `docs/SPACE_RECOVERY.md` with pass or quota outcome.

---

## Requirements

- R1. No `verify_hosted_space.sh --generate` before browser in this session.
- R2. Browser: `0_img.png` at 512 → Generate → step 3 shows GLB viewer (`main-3d-viewer` src) or explicit non-empty error.
- R3. Update `SPACE_RECOVERY.md` browser row and browser note.
- R4. If GLB passes, record date and do not run CLI generate in same session.

---

## Scope Boundaries

- Playwright automation in CI
- Runtime code changes unless browser finds regression

---

## Implementation Units

- U1. Browser E2E on live Space.
- U2. Update `docs/SPACE_RECOVERY.md` with outcome.
- U3. Ship doc-only PR if needed.
