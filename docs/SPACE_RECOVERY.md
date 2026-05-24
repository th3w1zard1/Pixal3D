# Pixal3D Space recovery (2026-05)

## Status: closed

The hosted ZeroGPU Space at https://th3w1zard1-pixal3d.hf.space/ is operational for anonymous cold generate with a geometry-only GLB (`glb_path`) and textured extract via Export (`extract_available: true`). Recovery implementation is complete (plans `docs/plans/2026-05-24-027-*` through `037-*`).

| Surface | Verification |
|---------|----------------|
| Backend `/generate_3d` (CLI) | **Pass** — anonymous cold run ~134s, `glb_path`, `extract_available: true` (2026-05-24) |
| Health + HTML smoke | **Pass** — markers include 512 ZeroGPU option and `data-smoke-default-sample` |
| GitHub ↔ HF parity | **Pass** — `check_repo_parity.py` at `a14b875` |
| Browser gallery → GLB | **Blocked on quota** when anonymous daily slice is exhausted; sign in on the Space or retry after reset |

## Verification order (agents)

1. `python3 scripts/check_repo_parity.py`
2. `python3 scripts/space_smoke.py --health-only --html-check`
3. **Browser** (optional but required by AGENTS.md before closing runtime work): load Space → confirm no idle viewer error → gallery `assets/images/0_img.png` → Generate at 512 → expect step 3 GLB or explicit quota/error copy
4. `space_smoke.py --generate` **only after** browser, or on a separate day — CLI cold generate uses ~120s of ZeroGPU quota and will cause the browser run to fail if run first

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
python3 scripts/check_repo_parity.py
python3 scripts/space_smoke.py --health-only --html-check
python3 -m venv .venv && .venv/bin/pip install -r scripts/smoke-requirements.txt
.venv/bin/python scripts/space_smoke.py --generate
```

- **CI (manual):** GitHub Actions → **Python CI** → **Run workflow** → `space-generate-smoke` (`--generate`, ~2–3 min, uses quota).
- **Parity:** If drift is reported, run `git push origin main` or configure `HF_TOKEN` for GitHub Actions auto-sync.

## Browser note (2026-05-24)

Gallery sample `0_img.png` at 512 with idle error hidden; Generate reached step 3 but failed with full **ZeroGPU quota exceeded** copy (`120s requested vs. 19s left`) after prior CLI smokes in the same quota window. This is expected operator behavior, not an empty-overlay regression.

## Remotes

| Remote | Target |
|--------|--------|
| `github` | GitHub `th3w1zard1/Pixal3D` |
| `origin` | Hugging Face Space `th3w1zard1/Pixal3D` |
