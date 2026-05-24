---
title: "feat: ZeroGPU default 512 resolution in hosted UI"
type: feat
status: active
date: 2026-05-24
origin: docs/plans/2026-05-24-020-feat-space-smoke-zerogpu-generate-plan.md
---

# feat: ZeroGPU default 512 resolution in hosted UI

## Summary

Add a 512 resolution option and auto-select it on ZeroGPU alongside the existing fast export default, so hosted users and agents start with quota-friendly generation settings that match `space_smoke.py`.

---

## Problem Frame

The UI defaults to 1024 resolution while ZeroGPU smoke and export fast profile use 512. Anonymous cold runs abort during warmup/generate; lower default resolution reduces work per slice after models load.

---

## Requirements

- R1. `index.html` offers 512 as a resolution choice with clear ZeroGPU-oriented label.
- R2. `applyZeroGpuHostedDefaults` selects 512 resolution once when `runtime_mode === 'zerogpu'`.
- R3. Live Space deploy and `space_smoke.py --health-only --html-check` pass.

---

## Scope Boundaries

- Changing ZeroGPU duration caps in `app.py`
- Guaranteed anonymous full generate success
- Unit tests

---

## Implementation Units

- U1. **512 resolution option and ZeroGPU default**

**Requirements:** R1, R2

**Files:** Modify `index.html`

**Verification:** On ZeroGPU cold load, resolution select becomes 512; export stays fast.

---

- U2. **Deploy and smoke verify**

**Requirements:** R3

**Dependencies:** U1

**Verification:** HF Space updated; health/HTML smoke exit 0.

---

## Sources & References

- `index.html` `applyZeroGpuHostedDefaults`
- `scripts/space_smoke.py` `ZEROGPU_SMOKE_RESOLUTION = 512`
