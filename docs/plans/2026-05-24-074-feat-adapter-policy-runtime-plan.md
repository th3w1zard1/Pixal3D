---
title: "feat: adapter policy runtime checks on /health"
type: feat
status: completed
date: 2026-05-24
origin: docs/adapters/README.md
---

# feat: adapter policy runtime checks on /health

## Problem

Adapter policy exists as a CLI stub (`check_adapter_policy.py`) but runtime does not load it. Operators cannot see policy alignment on `/health`, and there is no opt-in enforcement before boot.

## Requirements

- R1. `adapter_policy_runtime.py` loads policy JSON (default `docs/adapters/policy.example.json`, override `PIXAL3D_ADAPTER_POLICY`), validates rembg candidates against enabled `hub_repo` entries.
- R2. `space_bootstrap.build_runtime_config` evaluates policy; raises on mismatch only when `PIXAL3D_ADAPTER_POLICY_ENFORCE=1` and enabled adapters exist.
- R3. `/health` includes `adapter_policy_path`, `adapter_policy_ok`, `adapter_policy_enforced`, `adapter_policy_violations`.
- R4. Document env vars; deploy to HF Space; `./scripts/pre_ship.sh` on branch then merge.

## Out of scope

- Enabling adapters in policy (remain `enabled: false` on `main`)
- Unit tests
