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

## Runtime notes

- The Space now patches the upstream `TencentARC/Pixal3D-T` pipeline config locally before model boot so it does not depend on the gated `briaai/RMBG-2.0` repo.
- Default background-removal model: `ZhengPeng7/BiRefNet`
- Default fallback model: `ZhengPeng7/BiRefNet_lite`
- Health endpoint: `/health`
- Readiness endpoint: `/ready` returns `200` only after the GPU runtime is actually primed

## Optional environment variables

- `PIXAL3D_REMBG_MODEL` to override the primary background-removal model
- `PIXAL3D_REMBG_FALLBACKS` as a comma-separated fallback list
- Hosted Spaces default to lazy GPU initialization; set `PIXAL3D_WARMUP_ON_START=1` only if you explicitly want startup warmup
- `GRADIO_SHARE=1` to enable Gradio share links outside the hosted Space runtime
- `HF_TOKEN` only if you intentionally need authenticated Hugging Face Hub access for other assets

