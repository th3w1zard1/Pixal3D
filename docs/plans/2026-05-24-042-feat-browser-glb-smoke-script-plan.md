---
title: "feat: agent-browser gallery→GLB smoke script"
type: feat
status: completed
date: 2026-05-24
origin: docs/SPACE_RECOVERY.md
---

# feat: agent-browser gallery→GLB smoke script

## Summary

Recovery is closed and CLI smoke passes, but browser gallery → GLB remains operator-only. Add `scripts/browser_glb_smoke.sh` using the existing `agent-browser` CLI to automate the default-sample path, run it against the live Space, and update recovery docs when the outcome is known.

## Requirements

- R1. Script opens the Space, selects gallery `assets/images/0_img.png`, clicks **Start Generation** at 512, and waits for GLB viewer `src` or a visible viewer-error message.
- R2. Exit 0 on GLB success; non-zero on quota/error/timeout with actionable stderr.
- R3. Document the script in `docs/post-recovery.md` and `docs/SPACE_RECOVERY.md`; do not run `verify_hosted_space.sh --generate` in the same session before browser.
- R4. No runtime Python/HTML changes unless the smoke run proves a regression.

## Scope Boundaries

- Playwright in CI
- Replacing `@gradio/client` generate smoke

## Implementation Units

- U1. Add `scripts/browser_glb_smoke.sh` with `--url` and timeout flags.
- U2. Run script against live Space; update verification docs with pass/fail/quota outcome.
- U3. Extend `verify_hosted_space.sh` footer to mention the browser script (one line).

## Verification

- `command -v agent-browser` succeeds.
- `./scripts/browser_glb_smoke.sh` exits 0 with GLB, or exits non-zero with explicit quota/error text recorded in docs.
