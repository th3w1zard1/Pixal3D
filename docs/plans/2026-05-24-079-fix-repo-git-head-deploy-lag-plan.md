---
title: "fix: repo_git_head deploy lag and recovery doc sync"
type: fix
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# fix: repo_git_head deploy lag and recovery doc sync

## Problem

After merging **078** (`95c4052`, scripts-only), `./scripts/pre_ship.sh` failed because live `/health` still reported `repo_git_head: 28c5e40` while local `HEAD` was already `95c4052`. Parity was fine; the running Space container had not caught up yet. `repo_git_head_ok` compared Space to local `HEAD` only, so operators saw a false failure during normal HF rebuild lag.

## Requirements

- R1. `repo_git_head_ok` compares Space `repo_git_head` to **deployed** refs (`origin/main`, then `github/main`, then `HEAD`); error text names `expected=`.
- R2. Health smoke polls `/health` for deploy-head match up to `PIXAL3D_REPO_HEAD_WAIT_SECS` (default 120) before failing.
- R3. Gate v3 `repo_git_head_match` uses the same expected deploy head as smoke (via `VERIFY_DEPLOY_GIT_HEAD` in `verify_hosted_space.sh`).
- R4. `SPACE_RECOVERY.md` and plan index document **078** (gate v3) and last pre-ship at `95c4052`.
- R5. `./scripts/pre_ship.sh` passes on `main` after merge; push `github` + `origin` when merged.

## Out of scope

- Changing `pixal3d-agent-gate/3` schema version
- Runtime `app.py` changes (HF rebuild not required for script-only fix)

## Implementation units

### IU1 — `scripts/space_smoke.py`

- Add `_remote_short_head`, `_expected_deploy_git_head`, `wait_for_repo_git_head_health`.
- Wire poll in `main()` before `repo_git_head_ok` final assertion.
- Add `--repo-head-wait-secs` (optional CLI override).

### IU2 — `scripts/verify_hosted_space.sh`

- Set `VERIFY_DEPLOY_GIT_HEAD` from `origin/main` / `github/main` / `HEAD`.
- Use it for `repo_git_head_match` in gate JSON.

### IU3 — Docs

- Update `docs/SPACE_RECOVERY.md`, `docs/workflow-hygiene.md` (deploy lag note), plan index row **078**–**079**.

## Test scenarios

- With Space head matching `origin/main`, `repo_git_head_ok` returns true.
- When Space head lags remotes, poll succeeds within wait window (manual / live).
- `validate_gate_json.py docs/gate-results/example.json` still passes.
- `./scripts/pre_ship.sh` → `overall_ok: true`.
