# Pixal3D Space recovery (2026-05)

See also [post-recovery.md](post-recovery.md) and [workflow-hygiene.md](workflow-hygiene.md) for operator handoff and hygiene gates.

## Status: closed

The hosted ZeroGPU Space at https://th3w1zard1-pixal3d.hf.space/ is operational for anonymous cold generate with a geometry-only GLB (`glb_path`) and textured extract via Export (`extract_available: true`). Recovery implementation is complete (plans `docs/plans/2026-05-24-027-*` through `039-*`). Workflow hygiene (plans `067`–`071`), adapter policy runtime (**074**–**075**), API `generation_run` manifests (**076**), `repo_git_head` on `/health` (**077**), and agent gate schema v3 (**078**) are on `main`.

**Last pre-ship (2026-05-27, `95c4052`+):** `./scripts/pre_ship.sh` — expect `overall_ok: true`, `repo_git_head_match: true`, `browser_exit: 1` when quota copy is shown (verified pass). Health smoke polls up to `PIXAL3D_REPO_HEAD_WAIT_SECS` (default 120) after HF pushes while the Space container catches up. **Last CLI generate (2026-05-24):** `--generate` pass (~124s, `glb_path`, `extract_available: true`). Confirm `generation_run` via `space_smoke.py --generate` on a fresh quota window.

| Surface | Verification |
|---------|----------------|
| Backend `/generate_3d` (CLI) | **Pass** — anonymous cold run ~124s, `glb_path`, `extract_available: true` (2026-05-24); **076** adds `generation_run` on API success |
| Health + HTML smoke | **Pass** — markers + ZeroGPU fields; `repo_git_head` matches local `main` after deploy |
| GitHub ↔ HF parity | **Pass** — `check_repo_parity.py` on `main` (sync after each push) |
| Browser gallery → GLB | **Pass** — via `pre_ship.sh` / `agent_gate.sh`; exit **1** = quota (verified) |
| Workflow hygiene (static) | **Pass** — `./scripts/workflow_hygiene.sh` |
| Adapter policy (`/health`) | **Pass** — `adapter_policy_ok: true`, `adapter_policy_enabled_count: 2` |

## Verification order (agents)

1. `./scripts/pre_ship.sh` — static hygiene then parity + health/HTML + browser + JSON
2. Or `./scripts/workflow_hygiene.sh` then `./scripts/agent_gate.sh`
3. `./scripts/verify_hosted_space.sh` (health/HTML only)
4. Manual browser: gallery `0_img.png` at 512 → Generate — before `--generate` in the same session
5. `python scripts/space_smoke.py --generate [--write-manifest PATH]` — after browser or fresh quota; expects `generation_run` (**076**)

## What was fixed

| Area | Outcome |
|------|---------|
| Gated rembg | Default `BiRefNet_lite` on ZeroGPU (`space_bootstrap.py`) |
| Cold GPU slice | 120s when pipeline unloaded; smoke skips `/warmup_runtime` on ZeroGPU |
| Generate path | GLB-only on ZeroGPU (no preview frames that hit `mesh.simplify`) |
| Smoke | Deliverable checks + `generation_run` manifest (**076**) |
| UI | Idle viewer error hidden; Extract after GLB-only generate |
| Workflow hygiene | `pre_ship`, manifests, adapter policy (**067**–**076**) |

## Operator commands

```bash
./scripts/pre_ship.sh
curl -s https://th3w1zard1-pixal3d.hf.space/health | jq '{repo_git_head, adapter_policy_ok, adapter_policy_enabled_count}'
python scripts/space_smoke.py --health-only --html-check
python scripts/space_smoke.py --generate --write-manifest docs/generation-manifests/latest.json  # quota
```

- **Hygiene index:** [workflow-hygiene.md](workflow-hygiene.md)
- **API manifests:** [generation-runs/README.md](generation-runs/README.md) (`generation_run` field)
- **CI (manual):** Actions → Python CI → Run workflow → `space-generate-smoke`

## Browser note (2026-05-24)

Gallery sample `0_img.png` at 512. Anonymous quota exhaustion shows full **ZeroGPU quota exceeded** copy. Cold generate ~2–3 minutes when quota allows.

## Plan index (workflow hygiene, on `main`)

| Plan | Topic |
|------|--------|
| 067 | Generation smoke `--write-manifest` |
| 068 | README + CI manifest artifact |
| 069 | Adapter policy stub |
| 070 | `workflow_hygiene.sh` |
| 071 | `pre_ship.sh` + `workflow-hygiene.md` |
| 074 | Adapter policy on `/health` |
| 075 | Active rembg entries in `policy.example.json` |
| 076 | `generation_run` on `/generate_3d` |
| 077 | `repo_git_head` on `/health` + recovery doc sync |
| 078 | Agent gate `pixal3d-agent-gate/3` (deploy health fields) |
| 079 | Deploy-head poll + match `origin/main` (rebuild lag) |

## Remotes

| Remote | Target |
|--------|--------|
| `github` | GitHub `th3w1zard1/Pixal3D` |
| `origin` | Hugging Face Space `th3w1zard1/Pixal3D` |
