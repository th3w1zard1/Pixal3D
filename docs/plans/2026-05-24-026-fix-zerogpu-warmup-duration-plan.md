---
title: "fix: Extend ZeroGPU warmup slice for cold model load"
type: fix
status: active
date: 2026-05-24
origin: docs/plans/2026-05-24-020-feat-space-smoke-zerogpu-generate-plan.md
---

# fix: Extend ZeroGPU warmup slice for cold model load

## Summary

Increase `ZEROGPU_WARMUP_DURATION_SECONDS` from 30 to 60 so cold `warmup_runtime` has a full ZeroGPU slice (up to 120s billed on xlarge) to finish model initialization before `generate_3d` runs in a separate slice.

---

## Problem Frame

`space_smoke.py --generate` fails during `/warmup_runtime` with `GPU task aborted` after ~60s on anonymous cold ZeroGPU. Warmup is declared at 30s (2× multiplier ≈ 60s cap); cold Pixal3D model load exceeds that window.

---

## Requirements

- R1. `ZEROGPU_WARMUP_DURATION_SECONDS` set to 60 in `app.py`.
- R2. `/health` budget payload reflects the new warmup cap.
- R3. Deploy to HF Space; re-run `--generate` smoke and document outcome.

---

## Scope Boundaries

- Changing generation or extract slice durations
- Guaranteed anonymous full GLB without sign-in
- Unit tests

---

## Implementation Units

- U1. **Raise ZeroGPU warmup duration cap**

**Requirements:** R1, R2

**Files:** Modify `app.py`

**Verification:** `/health` reports `warmup_seconds: 60`.

---

- U2. **Deploy and generate smoke verify**

**Requirements:** R3

**Dependencies:** U1

**Verification:** Live warmup succeeds or documented abort after extended slice.

---

## Sources & References

- `app.py` `ZEROGPU_WARMUP_DURATION_SECONDS`, `warmup_gpu_duration`
- Live smoke: warmup abort at ~60s with 30s declared cap
