# Pixal3D Space recovery (2026-05)

See also [post-recovery.md](post-recovery.md) and [workflow-hygiene.md](workflow-hygiene.md) for operator handoff and hygiene gates.

## Status: closed

The hosted ZeroGPU Space at https://th3w1zard1-pixal3d.hf.space/ is operational for anonymous cold generate with a geometry-only GLB (`glb_path`) and textured extract via Export (`extract_available: true`). Recovery implementation is complete (plans `docs/plans/2026-05-24-027-*` through `039-*`). Workflow hygiene bundle (plans `067`–`071`, merge `881c031`) adds static gates, generation smoke manifests, adapter policy stub, and `pre_ship.sh`.

**Last pre-ship (2026-05-27, `881c031`):** `./scripts/pre_ship.sh` — `overall_ok: true`, `browser_exit: 1` (quota copy, verified pass). **Last CLI generate (2026-05-24):** `--generate` pass (~124s, `glb_path`, `extract_available: true`).

| Surface | Verification |
|---------|----------------|
| Backend `/generate_3d` (CLI) | **Pass** — anonymous cold run ~124s, `glb_path`, `extract_available: true` (2026-05-24) |
| Health + HTML smoke | **Pass** — markers + ZeroGPU recovery fields (`BiRefNet_lite`, prefetch, 120s cold slice, `cuda_mesh_operators`) |
| GitHub ↔ HF parity | **Pass** — `check_repo_parity.py` on `main` (sync after each push) |
| Browser gallery → GLB | **Pass** (2026-05-24, plans 051/054) — via `agent_gate.sh` / `pre_ship.sh`; exit **0** = GLB; **1** = explicit quota/error (verified); **2** timeout |
| Workflow hygiene (static) | **Pass** — `./scripts/workflow_hygiene.sh` (schemas, adapter policy, workflow YAML in CI) |

## Verification order (agents)

1. `./scripts/pre_ship.sh` — static hygiene then parity + health/HTML + browser + JSON (`overall_ok`, `browser_exit`)
2. Or `./scripts/workflow_hygiene.sh` then `./scripts/agent_gate.sh`
3. `./scripts/verify_hosted_space.sh` (health/HTML only) / `--browser` without JSON
4. Manual browser only if not using the gate: gallery `assets/images/0_img.png` at 512 → Generate — before `--generate` in the same session
5. `python scripts/space_smoke.py --generate [--write-manifest PATH]` only after browser, or on another day (never browser gate and `--generate` together in one session)

## What was fixed

| Area | Outcome |
|------|---------|
| Gated rembg | Default `BiRefNet_lite` on ZeroGPU (`space_bootstrap.py`) |
| Cold GPU slice | 120s when pipeline unloaded; smoke skips `/warmup_runtime` on ZeroGPU |
| Generate path | GLB-only on ZeroGPU (no preview frames that hit `mesh.simplify`) |
| Smoke | Requires `glb_path` or `render_paths`; asserts `extract_available` when GLB returned |
| UI | Idle viewer error hidden on init; Extract available after GLB-only generate |
| Workflow hygiene | `workflow_hygiene.sh`, `pre_ship.sh`, generation manifest + adapter policy stubs (067–071) |

## Operator commands

```bash
./scripts/pre_ship.sh                                         # static hygiene + agent gate (recommended)
./scripts/workflow_hygiene.sh                                 # static only
./scripts/agent_gate.sh                                       # parity + health/HTML + browser + JSON
./scripts/verify_hosted_space.sh                              # parity + health/HTML only
python scripts/space_smoke.py --generate --write-manifest docs/generation-manifests/latest.json  # optional; quota
```

- **Hygiene index:** [workflow-hygiene.md](workflow-hygiene.md) (gate, generation manifest, adapter policy).
- **CI (manual):** GitHub Actions → **Python CI** → **Run workflow** → `space-generate-smoke` (`--generate`, uploads `generation-smoke-manifest` artifact; ~2–3 min, uses quota).
- **Parity:** If drift is reported, run `git push origin main` or configure `HF_TOKEN` for GitHub Actions auto-sync.

## Browser note (2026-05-24)

Gallery sample `0_img.png` at 512 with idle error hidden. When anonymous quota is exhausted, Generate shows full **ZeroGPU quota exceeded** copy (not an empty overlay). With quota available, expect step 3 GLB viewer load after ~2–3 minutes cold.

**Automated browser (plan 043):** Script waits for `data-smoke-file-ready`, unlocks Generate when health is still pending, and detects `data-smoke-glb-ready` on success. Default generate wait is **300s**. Re-run on a fresh quota window; sign in on the Space for higher ZeroGPU limits.

## Plan index (workflow hygiene, on `main`)

| Plan | Topic |
|------|--------|
| 067 | Generation smoke `--write-manifest` |
| 068 | README + CI manifest artifact |
| 069 | Adapter policy stub |
| 070 | `workflow_hygiene.sh` |
| 071 | `pre_ship.sh` + `workflow-hygiene.md` |

## Remotes

| Remote | Target |
|--------|--------|
| `github` | GitHub `th3w1zard1/Pixal3D` |
| `origin` | Hugging Face Space `th3w1zard1/Pixal3D` |
