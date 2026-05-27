---
title: "feat: gate --write-summary and exit on overall_ok"
type: feat
status: completed
date: 2026-05-24
origin: README.md
---

# feat: gate --write-summary and exit on overall_ok

## Problem

Agents cannot persist gate JSON as an artifact, and `verify_hosted_space.sh` always exits 0 when the browser quota path verifies (`browser_exit: 1`) even though callers may want exit code 1 when `overall_ok` is false. Post-recovery docs omit `jq` and `schema_version`.

## Requirements

- R1. `verify_hosted_space.sh` accepts `--write-summary PATH` (requires `--summary-json`) and writes the same JSON to that file.
- R2. When `--summary-json`, final exit code is 0 iff `overall_ok` is true (after successful completion path).
- R3. `agent_gate.sh` forwards `--write-summary` and documents it in `--help`.
- R4. Add `docs/gate-results/README.md`; update `post-recovery.md` with jq/schema note; live gate run; push.

## Implementation units

- U1. Script changes (`verify_hosted_space.sh`, `agent_gate.sh`).
- U2. Docs + verification.

## Out of scope

- Committing live gate JSON to git by default
- CI changes
- Unit tests
