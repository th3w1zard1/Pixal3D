---
title: "chore: gate doc sync and accurate summary-json flags"
type: feat
status: completed
date: 2026-05-24
origin: docs/post-recovery.md
---

# chore: gate doc sync and accurate summary-json flags

## Problem

Plan 057 added `--summary-json`, but `emit_summary_json` always sets `parity_ok` and `health_ok` to true when reached. Operator docs (`post-recovery.md`, `SPACE_RECOVERY.md` commands block) omit `--summary-json` and the combined agent gate.

## Requirements

- R1. `verify_hosted_space.sh` sets `VERIFY_PARITY_OK` / `VERIFY_HEALTH_OK` from actual step results; JSON reflects them.
- R2. `docs/post-recovery.md` and `docs/SPACE_RECOVERY.md` operator commands reference `--browser --summary-json`.
- R3. Live run: `./scripts/verify_hosted_space.sh --browser --summary-json`; update last-gate line with `main` SHA.
- R4. Push to `github` and `origin`.

## Implementation units

- U1. Script accuracy fix + doc sync.
- U2. Verification gate run.

## Out of scope

- CI changes
- Unit tests
