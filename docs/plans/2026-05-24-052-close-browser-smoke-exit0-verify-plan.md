---
title: "close: browser smoke exit 0 verification and recovery gate"
type: feat
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# close: browser smoke exit 0 verification and recovery gate

## Problem

Plans 050–051 made browser smoke reliable (`load=done`, generate reaches viewer). Last live run exited **1** (ZeroGPU quota). Recovery closure needs a fresh smoke attempt and parity/health confirmation.

## Requirements

- R1. `check_repo_parity.py` passes on `main`.
- R2. `./scripts/verify_hosted_space.sh` passes (no `--generate` in same session as browser).
- R3. `./scripts/browser_glb_smoke.sh` run; record exit code; update `docs/SPACE_RECOVERY.md` if exit **0**.
- R4. Push any doc updates to GitHub + HF `origin`.

## Implementation units

- U1. Run verification ladder (parity → hosted verify → browser smoke).
- U2. Doc update if GLB exit 0.

## Out of scope

- HF_TOKEN browser sign-in automation
- New unit tests
