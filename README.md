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
- keep local development viable without CUDA, model weights, or native build friction;
- make CPU fallback explicit instead of magical;
- keep every generation run inspectable through manifests, reports, and retained outputs;
- validate inputs and exported artifacts before claiming success;
- gate heavy adapters behind license, dependency, and runtime checks instead of enabling them early.

In short, the project is prioritizing dependable workflow and deployment hygiene over chasing model capability too early.

## Runtime notes

- The Space now patches the upstream `TencentARC/Pixal3D-T` pipeline config locally before model boot so it does not depend on the gated `briaai/RMBG-2.0` repo.
- Default background-removal model: `ZhengPeng7/BiRefNet`
- Default fallback model: `ZhengPeng7/BiRefNet_lite`
- Health endpoint: `/health`
- Runtime policy endpoint: `/runtime-policy`
- Readiness endpoint: `/ready` returns `200` only after the GPU runtime is actually primed

## Runtime fallback policy

Pixal3D now carries an explicit 4-stage runtime policy in code and docs:

1. `zerogpu`
2. `space_cpu`
3. `local_gpu`
4. `local_cpu`

Why this order:

- Prefer the highest-fidelity runtime available on the current host before stepping down.
- Keep the public Hugging Face Space responsive when ZeroGPU quota is exhausted.
- Preserve a full-quality path for duplicated or self-hosted local CUDA runs.
- Keep a last-resort CPU mode for debugging and geometry-first export on machines without CUDA.

Important boundary:

- Hosted Space branch: `zerogpu -> space_cpu`
- Local branch: `local_gpu -> local_cpu`

The hosted Space cannot automatically execute work on a local machine, so the local stages are the fallback order for duplicated or self-hosted runs rather than browser failover from the public Space.

See [RUNTIME_FALLBACK_POLICY.md](RUNTIME_FALLBACK_POLICY.md) for the full rulebook.

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

- Ruff functional checks on `runtime_policy.py`, `space_bootstrap.py`, `space_runtime.py`, `scripts/`, and `tests/`
- syntax compilation for the core app and runtime files
- `python -m unittest discover tests -p "test_*.py" -v`

It intentionally does not validate:

- CUDA-only dependencies from the runtime requirements files
- heavyweight model downloads
- end-to-end inference or GPU kernels on GitHub-hosted runners

### Release behavior

The release workflow does not currently publish Python distribution artifacts. Even though the repo now has a `pyproject.toml` configuration hub, releases are still repository-centric rather than package-centric.

Instead it publishes:

- a Git source archive
- a working-tree bundle suitable for repo and Space handoff
- `release-metadata.json` with the release tag, commit SHA, Python version, and runtime references

Manual releases default to draft mode. If no manual tag is provided, the workflow falls back to `manual-<run_number>`.

### Hugging Face Space sync

The sync workflow defaults to the current public Space target:

- `th3w1zard1/Pixal3D`

You can override that target in GitHub repository settings with either:

- `HF_SPACE_REPO_ID`
- or the pair `HF_SPACE_NAMESPACE` and `HF_SPACE_NAME`

Other supported repository variables:

- `HF_SPACE_SDK` to override the Space SDK, default `gradio`
- `HF_SPACE_AUTO_SYNC=true` to allow pushes to `main` to mirror automatically

Required secret:

- `HF_TOKEN`

Recommended rollout path:

1. Add `HF_TOKEN` and any intended `HF_SPACE_*` variables.
2. Manually dispatch `sync-hf-space.yml` with `create_if_missing=false` first.
3. Enable `HF_SPACE_AUTO_SYNC=true` only after the manual run succeeds.
