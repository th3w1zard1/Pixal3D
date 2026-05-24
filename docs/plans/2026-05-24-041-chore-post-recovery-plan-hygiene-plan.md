---
title: "chore: post-recovery plan hygiene and operator handoff"
type: chore
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# chore: post-recovery plan hygiene and operator handoff

## Summary

Space recovery is closed on `main` (PRs #28–#33). Many recovery-era plans still show `status: active` in frontmatter. Close that bookkeeping loop, add a short post-recovery operator doc, re-run non-generate hosted verification, and attempt browser default-sample GLB E2E when browser tools are available (best effort).

## Requirements

- R1. Set `status: completed` in YAML frontmatter for recovery plans `docs/plans/2026-05-24-012-*` through `040-*` that shipped on `main`.
- R2. Add `docs/post-recovery.md` with links to `docs/SPACE_RECOVERY.md`, verification order, and README ImageEZGen3D direction.
- R3. Run `./scripts/verify_hosted_space.sh` (no `--generate` in this session until browser E2E completes or is documented as blocked).
- R4. Best-effort browser E2E: gallery `assets/images/0_img.png` at 512 → Generate → GLB viewer or explicit quota error; update `docs/SPACE_RECOVERY.md` browser row if outcome is known.
- R5. Do not change runtime Python/HTML unless browser finds a regression.

## Scope Boundaries

- Playwright CI automation
- New unit tests
- CLI `--generate` before browser in the same session

## Implementation Units

- U1. Mark recovery plan frontmatter `status: completed` (012–040).
- U2. Add `docs/post-recovery.md`; cross-link from `docs/SPACE_RECOVERY.md`.
- U3. Run `verify_hosted_space.sh` (parity + health/HTML only).
- U4. Browser E2E + doc update (skip code if MCP unavailable; record blocker in SPACE_RECOVERY).

## Verification

- `python3 scripts/check_repo_parity.py` passes.
- `./scripts/verify_hosted_space.sh` exits 0.
- All touched plan files show `status: completed` except this plan until shipped.
