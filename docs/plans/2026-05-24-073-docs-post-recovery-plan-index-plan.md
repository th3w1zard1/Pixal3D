---
title: "docs: post-recovery plan index and merge PR 37"
type: docs
status: completed
date: 2026-05-24
origin: docs/post-recovery.md
---

# docs: post-recovery plan index and merge PR 37

## Problem

`post-recovery.md` still lists plans only through `040-*`. PR #37 (plan 072) is CI-green; hygiene docs should cross-link the recovery runbook.

## Requirements

- R1. `post-recovery.md` indexes workflow hygiene plans `067`–`072`.
- R2. `workflow-hygiene.md` links `SPACE_RECOVERY.md`.
- R3. Merge PR #37; `pre_ship.sh` on `main`; push `github` and `origin` `main`.

## Out of scope

- Runtime or Space deploy changes
