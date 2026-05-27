# Pixal3D Space recovery (2026-05)

See also [post-recovery.md](post-recovery.md) for operator handoff after recovery closes.

## Status: closed

The hosted ZeroGPU Space at https://th3w1zard1-pixal3d.hf.space/ is operational for anonymous cold generate with a geometry-only GLB (`glb_path`) and textured extract via Export (`extract_available: true`). Recovery implementation is complete (plans `docs/plans/2026-05-24-027-*` through `039-*`).

**Last gate (2026-05-24, plan 056 @ `a2622a6`):** `./scripts/verify_hosted_space.sh --browser` — parity + health/HTML pass; browser `load=done`, quota exit **1** (path verified). **Last CLI generate (2026-05-24):** `--generate` pass (~124s, `glb_path`, `extract_available: true`).

| Surface | Verification |
|---------|----------------|
| Backend `/generate_3d` (CLI) | **Pass** — anonymous cold run ~124s, `glb_path`, `extract_available: true` (2026-05-24) |
| Health + HTML smoke | **Pass** — markers + ZeroGPU recovery fields (`BiRefNet_lite`, prefetch, 120s cold slice, `cuda_mesh_operators`) |
| GitHub ↔ HF parity | **Pass** — `check_repo_parity.py` on `main` (sync after each push) |
| Browser gallery → GLB | **Pass** (2026-05-24, plans 051/054) — `./scripts/browser_glb_smoke.sh` or `verify_hosted_space.sh --browser`; exit **0** = GLB; **1** = explicit quota/error (verified); **2** timeout |

## Verification order (agents)

1. `./scripts/verify_hosted_space.sh` (parity + health/HTML), or `./scripts/verify_hosted_space.sh --browser` to include automated browser smoke in the same run
2. **Browser** (if not using `--browser`): gallery `assets/images/0_img.png` → Generate at 512 → step 3 GLB or explicit quota/error copy — must run before `--generate` in the same session
3. `./scripts/verify_hosted_space.sh --generate` only after browser, or on another day (never `--browser --generate` together)

## What was fixed

| Area | Outcome |
|------|---------|
| Gated rembg | Default `BiRefNet_lite` on ZeroGPU (`space_bootstrap.py`) |
| Cold GPU slice | 120s when pipeline unloaded; smoke skips `/warmup_runtime` on ZeroGPU |
| Generate path | GLB-only on ZeroGPU (no preview frames that hit `mesh.simplify`) |
| Smoke | Requires `glb_path` or `render_paths`; asserts `extract_available` when GLB returned |
| UI | Idle viewer error hidden on init; Extract available after GLB-only generate |

## Operator commands

```bash
./scripts/verify_hosted_space.sh
./scripts/verify_hosted_space.sh --generate   # optional; uses ZeroGPU quota
```

- **CI (manual):** GitHub Actions → **Python CI** → **Run workflow** → `space-generate-smoke` (`--generate`, ~2–3 min, uses quota).
- **Parity:** If drift is reported, run `git push origin main` or configure `HF_TOKEN` for GitHub Actions auto-sync.

## Browser note (2026-05-24)

Gallery sample `0_img.png` at 512 with idle error hidden. When anonymous quota is exhausted, Generate shows full **ZeroGPU quota exceeded** copy (not an empty overlay). With quota available, expect step 3 GLB viewer load after ~2–3 minutes cold.

**Automated browser (plan 043):** Script waits for `data-smoke-file-ready`, unlocks Generate when health is still pending, and detects `data-smoke-glb-ready` on success. Default generate wait is **300s**. Re-run on a fresh quota window; sign in on the Space for higher ZeroGPU limits.

## Remotes

| Remote | Target |
|--------|--------|
| `github` | GitHub `th3w1zard1/Pixal3D` |
| `origin` | Hugging Face Space `th3w1zard1/Pixal3D` |
