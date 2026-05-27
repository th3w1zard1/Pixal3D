---
title: "docs+health: SPACE_RECOVERY 076 sync and repo_git_head"
type: feat
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# docs+health: SPACE_RECOVERY 076 sync and repo_git_head

## Problem

Plan 076 merged (`4e5f5dc`) but `SPACE_RECOVERY.md` stops at plan 075. Operators cannot confirm the live Space revision without running `--generate`.

## Requirements

- R1. `/health` includes `repo_git_head` (short SHA at runtime).
- R2. `space_smoke.py` fails health smoke when `repo_git_head` differs from local `main`.
- R3. `SPACE_RECOVERY.md` documents plans 074–076, `generation_run`, and `repo_git_head`.
- R4. Deploy HF; `./scripts/pre_ship.sh` with matching `repo_git_head`.

## Out of scope

- Running `--generate` in this session
