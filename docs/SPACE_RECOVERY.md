# Pixal3D Space recovery (2026-05)

## Status

The hosted ZeroGPU Space at https://th3w1zard1-pixal3d.hf.space/ is operational for anonymous cold generate with a geometry-only GLB (`glb_path`) and textured extract via Export (`extract_available: true`). Recovery work is tracked in plans `docs/plans/2026-05-24-027-*` through `036-*`.

**Last verified (anonymous, 2026-05-24):** `space_smoke.py --health-only --html-check` pass; `--generate` pass (~134s) with `glb_path`, `extract_available: true`, geometry-only GLB message. GitHub and HF `main` at parity (`check_repo_parity.py` OK).

## What was fixed

| Area | Outcome |
|------|---------|
| Gated rembg | Default `BiRefNet_lite` on ZeroGPU (`space_bootstrap.py`) |
| Cold GPU slice | 120s when pipeline unloaded; smoke skips `/warmup_runtime` on ZeroGPU |
| Generate path | GLB-only on ZeroGPU (no preview frames that hit `mesh.simplify`) |
| Smoke | Requires `glb_path` or `render_paths`; asserts `extract_available` when GLB returned |
| UI | Idle viewer error hidden on init; Extract available after GLB-only generate |

## Operator verification

```bash
python3 scripts/check_repo_parity.py
python3 scripts/space_smoke.py --health-only --html-check
python3 -m venv .venv && .venv/bin/pip install -r scripts/smoke-requirements.txt
.venv/bin/python scripts/space_smoke.py --generate
```

- **CI (manual):** GitHub Actions → **Python CI** → **Run workflow** runs `space-generate-smoke` (`--generate`). Use when quota allows; not run on every push.

- **Parity:** `github/main` should match HF `origin/main`. If drift is reported, run `git push origin main` or configure `HF_TOKEN` in GitHub Actions.
- **Browser:** Open the Space, confirm no error overlay on load, click the first gallery sample (`assets/images/0_img.png`), run Generate at 512 / ZeroGPU-safe steps. Expect ~2–3 minutes cold; sign in if ZeroGPU quota is exhausted.

## Remotes

| Remote | Target |
|--------|--------|
| `github` | GitHub `th3w1zard1/Pixal3D` |
| `origin` | Hugging Face Space `th3w1zard1/Pixal3D` |
