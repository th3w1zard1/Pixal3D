---
title: "feat: generation_run manifest in /generate_3d response"
type: feat
status: completed
date: 2026-05-24
origin: README.md
---

# feat: generation_run manifest in /generate_3d response

## Problem

README requires inspectable generation runs. CLI smoke has `pixal3d-generation-smoke/1` manifests; successful `/generate_3d` responses still lack a stable inline manifest.

## Requirements

- R1. `generation_run_manifest.py` builds `pixal3d-generation-run/1` JSON; attached as `generation_run` on successful `_generate_3d_impl` results.
- R2. `scripts/validate_generation_run_json.py` + `docs/generation-runs/example.json`; CI validation; `workflow_hygiene.sh` includes validator.
- R3. `space_smoke.py --generate` requires `generation_run` when generate succeeds (after deploy).
- R4. Deploy HF; `./scripts/pre_ship.sh`; push `main` to `github` and `origin`.

## Out of scope

- Persisting manifests to disk on the Space
- Unit tests
