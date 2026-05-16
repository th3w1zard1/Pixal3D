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
