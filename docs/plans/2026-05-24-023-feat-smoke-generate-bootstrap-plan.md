---
title: "feat: Bootstrap gradio_client for space_smoke --generate"
type: feat
status: completed
date: 2026-05-24
origin: docs/plans/2026-05-24-020-feat-space-smoke-zerogpu-generate-plan.md
---

# feat: Bootstrap gradio_client for space_smoke --generate

## Summary

Make `scripts/space_smoke.py --generate` runnable for agents on PEP 668 hosts by documenting an optional venv bootstrap, pinning optional deps in `scripts/smoke-requirements.txt`, and improving the missing-dependency error message.

---

## Problem Frame

Plan 020 added warmup-first generate smoke, but local runs fail immediately with `No module named 'httpx'` when `gradio_client` is not installed. Health/HTML smoke works with stdlib only; generate needs an explicit optional dependency path.

---

## Requirements

- R1. Add `scripts/smoke-requirements.txt` pinning `gradio_client` (and transitive deps).
- R2. `space_smoke.py` error message includes venv + pip install one-liner when `gradio_client` is missing.
- R3. README and AGENTS.md document optional generate smoke setup.
- R4. Verify in ephemeral venv: `--generate` reaches warmup/generate (document exit code even if ZeroGPU aborts).

---

## Scope Boundaries

- Adding gradio_client to main Space requirements.txt
- CI running --generate on every PR
- Fixing ZeroGPU quota limits in app.py

---

## Implementation Units

- U1. **Optional smoke deps and clearer errors**

**Requirements:** R1, R2

**Files:** Create `scripts/smoke-requirements.txt`; modify `scripts/space_smoke.py`

**Verification:** Missing gradio_client prints install hint; venv install succeeds.

---

- U2. **Document generate smoke setup**

**Requirements:** R3

**Files:** Modify `README.md`, `AGENTS.md`

**Verification:** Docs show venv + pip + --generate command.

---

- U3. **Live generate smoke attempt**

**Requirements:** R4

**Dependencies:** U1

**Verification:** Script invokes warmup; outcome logged (OK or documented GPU abort).

---

## Sources & References

- `scripts/space_smoke.py`
- Plan 020 warmup-first generate path
