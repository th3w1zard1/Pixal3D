# Pixal3D Space recovery (2026-05)

## Status: closed

The hosted ZeroGPU Space at https://th3w1zard1-pixal3d.hf.space/ is operational for anonymous cold generate with a geometry-only GLB (`glb_path`) and textured extract via Export (`extract_available: true`). Recovery implementation is complete (plans `docs/plans/2026-05-24-027-*` through `039-*`).

**Last CLI check (2026-05-24):** `./scripts/verify_hosted_space.sh` pass; `--generate` pass (~124s, `glb_path`, `extract_available: true`).

| Surface | Verification |
|---------|----------------|
| Backend `/generate_3d` (CLI) | **Pass** — anonymous cold run ~124s, `glb_path`, `extract_available: true` (2026-05-24) |
| Health + HTML smoke | **Pass** — markers + ZeroGPU recovery fields (`BiRefNet_lite`, prefetch, 120s cold slice, `cuda_mesh_operators`) |
| GitHub ↔ HF parity | **Pass** — `check_repo_parity.py` on `main` |
| Browser gallery → GLB | **Blocked on quota** when anonymous daily slice is exhausted; sign in on the Space or retry after reset |

## Verification order (agents)

1. `./scripts/verify_hosted_space.sh` (parity + health/HTML)
2. **Browser** (before `--generate` in the same session): gallery `assets/images/0_img.png` → Generate at 512 → step 3 GLB or explicit quota/error copy
3. `./scripts/verify_hosted_space.sh --generate` only after browser, or on another day

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

Gallery sample `0_img.png` at 512 with idle error hidden; Generate reached step 3 but failed with full **ZeroGPU quota exceeded** copy (`120s requested vs. 19s left`) when anonymous daily quota is exhausted. Re-tested without prior CLI generate in-session: same quota message. Sign in on the Space or retry after reset for browser GLB proof; not an empty-overlay regression.

## Remotes

| Remote | Target |
|--------|--------|
| `github` | GitHub `th3w1zard1/Pixal3D` |
| `origin` | Hugging Face Space `th3w1zard1/Pixal3D` |
