---
title: "feat: agent gate schema_version and --help"
type: feat
status: completed
date: 2026-05-24
origin: AGENTS.md
---

# feat: agent gate schema_version and --help

## Problem

Agents parsing `agent_gate.sh` output have no schema identifier or in-script help. README shows the command but not the `jq` one-liner from plan 060.

## Requirements

- R1. JSON summary includes `schema_version: "pixal3d-agent-gate/1"`.
- R2. `scripts/agent_gate.sh` supports `--help` with usage and jq example.
- R3. `README.md` documents stdout JSON parsing (`2>/dev/null | jq`).
- R4. Live `agent_gate.sh` run; push to `github` and `origin`.

## Implementation units

- U1. `verify_hosted_space.sh` JSON field + `agent_gate.sh` help.
- U2. README + live gate.

## Out of scope

- CI changes
- Unit tests
