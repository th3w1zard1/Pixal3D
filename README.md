---
title: Pixal3D
emoji: 🏆
colorFrom: indigo
colorTo: gray
sdk: gradio
sdk_version: 6.14.0
python_version: "3.12"
app_file: app.py
pinned: false
short_description: "High-fidelity pixel-aligned image-to-3D generation."
---

## Upstream and workspace direction

This repository is a modified derivative of the upstream TencentARC Pixal3D work, specifically the `TencentARC/Pixal3D-T` pipeline used by this Space.

In this repo, that upstream foundation is being reshaped into ImageEZGen3D with a stricter workflow goal:

> ImageEZGen3D is aiming to be a reliable image-to-3D workspace scaffold before it becomes a heavy model integration project.

The current direction of the repository is to:

- prefer a ZeroGPU-first Gradio workflow when the environment supports it;
- follow the hardware assigned to the current Space or local run without browser-managed fallback layers;
- keep local development viable without CUDA, model weights, or native build friction;
- keep every generation run inspectable through manifests, reports, and retained outputs;
- validate inputs and exported artifacts before claiming success;
- gate heavy adapters behind license, dependency, and runtime checks instead of enabling them early.

In short, the project is prioritizing dependable workflow and deployment hygiene over chasing model capability too early.

## Runtime notes

- The Space now patches the upstream `TencentARC/Pixal3D-T` pipeline config locally before model boot so it does not depend on the gated `briaai/RMBG-2.0` repo.
- Default background-removal model: `ZhengPeng7/BiRefNet`
- Default fallback model: `ZhengPeng7/BiRefNet_lite`
- On hosted ZeroGPU (`ACCELERATOR=zero*`), the Space defaults to `BiRefNet_lite` for faster cold warmup unless `PIXAL3D_REMBG_MODEL` is set
- On hosted ZeroGPU, `PIXAL3D_LOW_VRAM=1` is enabled by default so MoGe and env maps stay on CPU until needed
- Hosted Spaces prefetch Hub weights on CPU in the background (`hub_prefetch_state` on `/health`); set `PIXAL3D_HUB_PREFETCH=0` to disable
- Preview frame rendering needs CUDA mesh operators (`cumesh`); `/health` reports `cuda_mesh_operators`. Hosted ZeroGPU uses a geometry-only GLB export path (no preview frames) to stay within GPU slice limits; other CUDA runtimes still render previews when operators are available
- Health endpoint: `/health`
- Readiness endpoint: `/ready` returns `200` only after the GPU runtime is actually primed
- Space recovery runbook: [docs/SPACE_RECOVERY.md](docs/SPACE_RECOVERY.md) (verification commands, plan index, parity notes)

## Optional environment variables

- `PIXAL3D_REMBG_MODEL` to override the primary background-removal model
- `PIXAL3D_REMBG_FALLBACKS` as a comma-separated fallback list
- Hosted Spaces default to lazy GPU initialization; set `PIXAL3D_WARMUP_ON_START=1` only if you explicitly want startup warmup
- `GRADIO_SHARE=1` to enable Gradio share links outside the hosted Space runtime
- `HF_TOKEN` only if you intentionally need authenticated Hugging Face Hub access for other assets

## GitHub automation

This repo now carries three GitHub Actions workflows under `.github/workflows/`:

- `python-ci.yml` runs a hosted-runner-safe validation slice on pull requests and pushes to `main`
- `release.yml` publishes GitHub release assets for tagged builds and supports manual draft releases
- `sync-hf-space.yml` mirrors this repository to a Hugging Face Space after a preflight token and target check

### CI scope

The CI workflow is intentionally CPU-safe and lightweight.

It currently validates:

- Ruff functional checks on `app.py`, `api_payload_utils.py`, `space_bootstrap.py`, `space_runtime.py`, and `scripts/`
- GitHub Actions workflow YAML parsing through `scripts/check_workflow_yaml.py`
- syntax compilation for the core app and runtime files
- live hosted Space smoke via `scripts/space_smoke.py --health-only --html-check` (`space-live-smoke` job)
- on pushes to `main`, a non-blocking `repo-parity` job compares GitHub `main` to the public Hugging Face Space git ref and logs drift when `HF_TOKEN` sync was skipped
- optional manual full generate smoke via **Actions → Python CI → Run workflow** (`space-generate-smoke` job; consumes ZeroGPU quota, ~2–3 minutes)

It intentionally does not validate:

- CUDA-only dependencies from the runtime requirements files
- heavyweight model downloads
- end-to-end inference or GPU kernels on GitHub-hosted runners

For local or agent verification of the hosted Space:

```bash
# Parity + health/HTML only (no agent-browser)
./scripts/verify_hosted_space.sh

# Combined gate: parity + health/HTML + browser default-sample E2E (needs agent-browser)
./scripts/verify_hosted_space.sh --browser
```

Browser smoke exit **0** means GLB ready; exit **1** with explicit ZeroGPU quota copy is a verified pass (path exercised). Do not combine `--browser` with `--generate` in one invocation.

Equivalent manual health/HTML steps:

```bash
python scripts/space_smoke.py --health-only --html-check
```

Use `--generate` only when ZeroGPU quota allows (see `AGENTS.md`). That path needs `gradio_client`:

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/smoke-requirements.txt
.venv/bin/python scripts/space_smoke.py --generate
```

On hosted ZeroGPU, `--generate` skips `/warmup_runtime` and calls `/generate_3d` directly (same as the browser UI). The first cold generate requests a 120s ZeroGPU slice while the pipeline is unloaded; warm runs stay on the 60s cap. Expect a geometry-only GLB (`glb_path`) in ~2–3 minutes for anonymous cold runs. Check `/health` for `rembg_model`, `low_vram`, `hub_prefetch_state`, `cuda_mesh_operators`, and `zerogpu_gpu_budgets.cold_generation_max_seconds`.

### Release behavior

The release workflow does not currently publish Python distribution artifacts. Even though the repo now has a `pyproject.toml` configuration hub, releases are still repository-centric rather than package-centric.

Instead it publishes:

- a Git source archive
- a working-tree bundle suitable for repo and Space handoff
- `release-metadata.json` with the release tag, commit SHA, Python version, and runtime references

Manual releases default to draft mode. If no manual tag is provided, the workflow falls back to `manual-<run_number>`.

Because the release workflow checks out the repository with `lfs: true`, GitHub must have the tracked LFS payloads as well as the Git history. If Actions checkout fails with LFS `404` errors, repair the repo state by fetching the objects from the Hugging Face Space remote and pushing them to the GitHub remote:

- `git lfs fetch origin --all`
- `git lfs push github --all`

### Hugging Face Space sync

The sync workflow defaults to the current public Space target:

- `th3w1zard1/Pixal3D`

You can override that target permanently in GitHub repository settings with either:

- `HF_SPACE_REPO_ID`
- or the pair `HF_SPACE_NAMESPACE` and `HF_SPACE_NAME`

Other supported repository variables:

- `HF_SPACE_SDK` to override the Space SDK, default `gradio`
- `HF_SPACE_PRIVATE=true` to create or preserve a private Space target during preflight and mirror setup
- `HF_SPACE_AUTO_SYNC=false` to disable automatic mirroring on pushes to `main`

For one-off manual runs, `sync-hf-space.yml` also accepts these workflow inputs:

- `hf_space_repo_id`, or `hf_space_namespace` plus `hf_space_name`
- `hf_space_sdk`
- `hf_space_private`
- `create_if_missing`

Required secret (for sync to run):

- `HF_TOKEN`

Behavior:

- Pushes to `main` trigger sync by default unless `HF_SPACE_AUTO_SYNC=false`.
- When `HF_TOKEN` is missing on a push, the workflow skips sync without failing CI.
- Manual `workflow_dispatch` runs still require `HF_TOKEN` and fail preflight if it is absent.
- After a successful hub-sync, the workflow polls `scripts/space_smoke.py` against the resolved Space URL until health/HTML markers pass or the retry window expires.

Recommended rollout path:

1. Add `HF_TOKEN` and any intended `HF_SPACE_*` variables.
2. Manually dispatch `sync-hf-space.yml` with `create_if_missing=false` first.
3. Confirm post-sync smoke passes, then rely on automatic main-push mirroring.

Check GitHub↔HF drift any time (exits 0 when remotes match):

```bash
python scripts/check_repo_parity.py
```

### Enabling automatic GitHub → Hugging Face sync

The sync workflow needs a Hugging Face token with write access to the Space repository.

1. Create a token at [Hugging Face Settings → Access Tokens](https://huggingface.co/settings/tokens) with **write** permission for `th3w1zard1/Pixal3D` (or use a fine-grained token scoped to that Space).
2. In GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret `HF_TOKEN` and paste the token value.
4. Manually dispatch **Sync Hugging Face Space** once with `create_if_missing=false`, or push to `main` and confirm the workflow sync job runs.
5. Verify with `python scripts/check_repo_parity.py` and `python scripts/space_smoke.py --health-only --html-check`.

When `HF_TOKEN` is absent, pushes to `main` still pass CI; the non-blocking `repo-parity` job logs drift instead.
