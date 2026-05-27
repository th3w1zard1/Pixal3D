---
title: "feat: clean stdout for --summary-json agent parsing"
type: feat
status: completed
date: 2026-05-24
origin: AGENTS.md
---

# feat: clean stdout for --summary-json agent parsing

## Problem

With `--summary-json`, human progress and browser smoke lines mix with the JSON object on stdout, so agents cannot pipe `agent_gate.sh` output directly into `jq` without fragile filtering.

## Requirements

- R1. When `--summary-json` is set, `verify_hosted_space.sh` sends progress and browser subprocess output to stderr; stdout contains only the final JSON object.
- R2. Final human OK line goes to stderr in summary-json mode.
- R3. Document in `AGENTS.md` that `./scripts/agent_gate.sh 2>/dev/null | jq .overall_ok` is valid.
- R4. Live `agent_gate.sh` run; stdout is valid JSON; push to `github` and `origin`.

## Implementation units

- U1. `verify_hosted_space.sh` stderr routing for summary-json mode.
- U2. Docs + live verification.

## Out of scope

- CI workflow changes
- Unit tests
