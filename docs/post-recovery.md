# Post-recovery operator guide

Space recovery for the hosted ZeroGPU demo is **closed**. Use this page after merging recovery work on `main`.

## Primary references

| Doc | Purpose |
|-----|---------|
| [SPACE_RECOVERY.md](SPACE_RECOVERY.md) | Verification matrix, operator commands, browser checklist |
| [gate-results/README.md](gate-results/README.md) | Agent gate JSON schema, `example.json`, optional `latest.json` |
| [generation-manifests/README.md](generation-manifests/README.md) | CLI `--generate` smoke manifest schema, `example.json`, optional `latest.json` |
| [generation-runs/README.md](generation-runs/README.md) | API `generation_run` manifest on successful `/generate_3d` |
| [adapters/README.md](adapters/README.md) | Adapter policy stub (`policy.example.json`, `check_adapter_policy.py`) |
| [workflow-hygiene.md](workflow-hygiene.md) | Unified hygiene index and `pre_ship.sh` |
| [README.md](../README.md) | ImageEZGen3D direction and runtime notes |
| `docs/plans/2026-05-24-027-*` … `040-*` | Recovery implementation plans (archived on `main`) |
| `docs/plans/2026-05-24-067-*` … `075-*` | Workflow hygiene + adapter policy runtime plans |

## Verification order

1. `./scripts/pre_ship.sh` — static hygiene then agent gate (preferred).
2. Or `./scripts/workflow_hygiene.sh` then `./scripts/agent_gate.sh` separately.
3. `./scripts/agent_gate.sh` alone — when static checks already passed (stdout JSON, `schema_version: pixal3d-agent-gate/2`; parse with `2>/dev/null | jq -e .overall_ok`). Browser subprocess exit **1** with explicit ZeroGPU quota copy is a verified pass when `overall_ok` is true.
4. `./scripts/verify_hosted_space.sh --browser --summary-json` — equivalent; use when you need other `verify_hosted_space.sh` flags in the same invocation.
5. Or split: `./scripts/verify_hosted_space.sh` then `./scripts/browser_glb_smoke.sh` before any generate smoke in the same session.
6. `./scripts/verify_hosted_space.sh --generate` — only after browser, or on a fresh quota window (never combine `--browser` and `--generate`).

## What to build next

Per README, the repo is prioritizing **workflow and deployment hygiene** (manifests, validation gates, adapter licensing) before heavy model integration. New feature work should start with `/ce-brainstorm` or `/ce-plan`, not ad-hoc recovery patches.

## CI and remotes

- **Manual generate smoke:** GitHub Actions → Python CI → Run workflow → `space-generate-smoke`. The job writes `pixal3d-generation-smoke/1` JSON and uploads the `generation-smoke-manifest` artifact (present when the manifest file was written, including failed generates).
- **HF sync:** `git push origin main` when `check_repo_parity.py` reports drift and `HF_TOKEN` is not configured in Actions.
