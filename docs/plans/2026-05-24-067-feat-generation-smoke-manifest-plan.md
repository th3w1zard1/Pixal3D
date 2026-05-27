---
title: "feat: generation smoke manifest (--write-manifest)"
type: feat
status: completed
date: 2026-05-24
origin: README.md
---

# feat: generation smoke manifest (--write-manifest)

## Problem

README targets inspectable generation runs via manifests. `space_smoke.py --generate` returns JSON to stdout but has no persisted, schema-stable artifact.

## Requirements

- R1. `space_smoke.py` accepts `--write-manifest PATH` (requires `--generate`) and writes `pixal3d-generation-smoke/1` JSON after generate completes.
- R2. `scripts/validate_generation_manifest.py` validates the schema; CI checks `docs/generation-manifests/example.json`.
- R3. `docs/generation-manifests/README.md` documents usage; `AGENTS.md` mentions optional manifest on CLI generate smoke.
- R4. Live `./scripts/agent_gate.sh` (no `--generate` in this session); push to `github` and `origin`.

## Implementation units

- U1. Manifest write + validator + CI.
- U2. Docs + agent gate run.

## Out of scope

- Browser or Space runtime changes
- Running `--generate` in this LFG session (ZeroGPU quota)
