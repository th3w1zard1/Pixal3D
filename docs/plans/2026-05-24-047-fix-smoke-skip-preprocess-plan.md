---
title: "fix: skip preprocess on smoke sample load"
type: fix
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# fix: skip preprocess on smoke sample load

## Summary

`__pixal3dLoadSamplePath` hangs in headless browser because background removal calls `client.predict('/preprocess')`. Skip preprocess for smoke sample loads and re-run browser GLB smoke.

## Requirements

- R1. `handleImageUpload(file, { skipPreprocess: true })` skips `runPreprocess`.
- R2. `__pixal3dLoadSamplePath` uses `skipPreprocess: true` without blocking loading overlay.
- R3. Deploy to HF; parity push; browser smoke exit 0 or explicit quota exit 1.

## Implementation Units

- U1. `index.html` skip-preprocess option.
- U2. Push `main`; run `browser_glb_smoke.sh`; update `SPACE_RECOVERY.md`.
