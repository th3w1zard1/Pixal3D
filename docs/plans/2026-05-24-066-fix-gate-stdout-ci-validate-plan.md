---
title: "fix: gate stdout purity and CI example validation"
type: fix
status: completed
date: 2026-05-24
origin: scripts/validate_gate_json.py
---

# fix: gate stdout purity and CI example validation

## Problem

`validate_gate_json.py` prints `OK: ...` to stdout when invoked from `--write-summary`, corrupting JSON-only stdout for `agent_gate.sh`. CI does not compile or validate the committed `example.json` reference.

## Requirements

- R1. `validate_gate_json.py` success messages go to stderr; stdout silent on success.
- R2. `python-ci.yml` compiles `validate_gate_json.py` and validates `docs/gate-results/example.json` on each run.
- R3. `post-recovery.md` primary references links `docs/gate-results/`.
- R4. Live `agent_gate.sh 2>/dev/null | jq .` succeeds; push to `github` and `origin`.

## Implementation units

- U1. Validator stdout fix + CI wiring.
- U2. Doc link + live gate.

## Out of scope

- Running agent_gate in CI (needs agent-browser)
- Unit tests
