---
title: "feat: README and CI wiring for generation manifests"
type: feat
status: completed
date: 2026-05-24
origin: docs/post-recovery.md
---

# feat: README and CI wiring for generation manifests

## Problem

Plan 067 added `--write-manifest` and docs under `docs/generation-manifests/`, but `README.md` still omits the flag and the manual `space-generate-smoke` CI job does not persist or publish a manifest artifact.

## Requirements

- R1. `README.md` documents `--write-manifest` alongside the existing `--generate` smoke example.
- R2. `space-generate-smoke` writes a manifest and uploads it as a workflow artifact (even on generate failure when manifest was written).
- R3. `docs/post-recovery.md` notes the CI artifact for manual generate smoke.
- R4. Live `./scripts/agent_gate.sh` on the branch; push updates to PR #36.

## Implementation units

- U1. README + post-recovery copy.
- U2. `python-ci.yml` manifest path + `upload-artifact`.

## Out of scope

- `app.py` runtime manifest integration
- Running `--generate` in this LFG session
