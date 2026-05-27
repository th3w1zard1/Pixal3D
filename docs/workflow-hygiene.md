# Workflow hygiene index

Post-recovery shipping checks for ImageEZGen3D / Pixal3D hosted Space work. No model weights or `app.py` changes required for these gates. Recovery context: [SPACE_RECOVERY.md](SPACE_RECOVERY.md).

## Recommended order

```bash
./scripts/pre_ship.sh
```

Equivalent manual steps:

```bash
./scripts/workflow_hygiene.sh
./scripts/agent_gate.sh
```

Optional parity during static checks:

```bash
./scripts/pre_ship.sh --parity
```

Persist agent gate JSON:

```bash
./scripts/pre_ship.sh --write-summary docs/gate-results/latest.json
```

## Artifacts and schemas

| Area | Schema | Example / docs |
|------|--------|----------------|
| Agent gate | `pixal3d-agent-gate/3` | [gate-results/README.md](gate-results/README.md), [gate-results/example.json](gate-results/example.json) |
| CLI generate smoke | `pixal3d-generation-smoke/1` | [generation-manifests/README.md](generation-manifests/README.md) |
| API `/generate_3d` | `pixal3d-generation-run/1` | [generation-runs/README.md](generation-runs/README.md) (`generation_run` field) |
| Adapter policy (stub) | `pixal3d-adapter-policy/1` | [adapters/README.md](adapters/README.md) |

## Scripts

| Script | Role |
|--------|------|
| `workflow_hygiene.sh` | Static validators + adapter policy check (+ workflow YAML when PyYAML installed) |
| `agent_gate.sh` | Parity + health/HTML + browser E2E + JSON on stdout |
| `pre_ship.sh` | Runs hygiene then agent gate |
| `verify_hosted_space.sh` | Lower-level verify flags |
| `space_smoke.py` | Health/HTML; optional `--generate --write-manifest` (quota; not in pre_ship) |

## CI

- Every PR/push: `syntax-smoke` runs `./scripts/workflow_hygiene.sh` (with PyYAML).
- Manual full generate: Actions → Python CI → Run workflow → `space-generate-smoke` (uploads `generation-smoke-manifest` artifact).

## Browser notes

Agent gate browser exit **1** with explicit ZeroGPU quota copy is a verified pass when `overall_ok` is true. Do not run CLI `--generate` in the same session before the browser gate.
