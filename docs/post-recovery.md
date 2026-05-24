# Post-recovery operator guide

Space recovery for the hosted ZeroGPU demo is **closed**. Use this page after merging recovery work on `main`.

## Primary references

| Doc | Purpose |
|-----|---------|
| [SPACE_RECOVERY.md](SPACE_RECOVERY.md) | Verification matrix, operator commands, browser checklist |
| [README.md](../README.md) | ImageEZGen3D direction and runtime notes |
| `docs/plans/2026-05-24-027-*` … `040-*` | Recovery implementation plans (archived on `main`) |

## Verification order

1. `./scripts/verify_hosted_space.sh` — parity + live health/HTML (no quota burn).
2. **Browser** — gallery `assets/images/0_img.png` at 512 → Generate → step 3 GLB viewer (see checklist printed by the verify script).
3. `./scripts/verify_hosted_space.sh --generate` — only after browser, or on a fresh quota window.

## What to build next

Per README, the repo is prioritizing **workflow and deployment hygiene** (manifests, validation gates, adapter licensing) before heavy model integration. New feature work should start with `/ce-brainstorm` or `/ce-plan`, not ad-hoc recovery patches.

## CI and remotes

- **Manual generate smoke:** GitHub Actions → Python CI → Run workflow → `space-generate-smoke`.
- **HF sync:** `git push origin main` when `check_repo_parity.py` reports drift and `HF_TOKEN` is not configured in Actions.
