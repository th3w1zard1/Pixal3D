---
title: "docs: active rembg adapters in policy + SPACE_RECOVERY 074"
type: docs
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# docs: active rembg adapters in policy + SPACE_RECOVERY 074

## Problem

Plan 074 added runtime `adapter_policy_*` on `/health`, but `SPACE_RECOVERY.md` still stops at plan 071 and `policy.example.json` lists rembg models as `enabled: false`, so `/health` reports `adapter_policy_enabled_count: 0` despite production using those Hub repos.

## Requirements

- R1. Enable both rembg entries in `policy.example.json` with correct `hub_repo` values (matches ZeroGPU defaults).
- R2. Update `SPACE_RECOVERY.md` for plan 074 and `/health` adapter policy fields.
- R3. `workflow_hygiene.sh` and local policy evaluation still pass.
- R4. Deploy to HF; `./scripts/pre_ship.sh`; `adapter_policy_enabled_count: 2` on live `/health`.

## Out of scope

- `PIXAL3D_ADAPTER_POLICY_ENFORCE=1` on the Space
