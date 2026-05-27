# Adapter policy (stub)

Heavy adapters are gated behind explicit policy before runtime integration. Policy files use schema `pixal3d-adapter-policy/1`.

## Files

| File | Purpose |
|------|---------|
| `policy.example.json` | Documents active rembg Hub models (`enabled: true`; matches ZeroGPU defaults) |
| `policy.local.json` | Optional local overrides (gitignored) |

## Commands

Validate policy shape:

```bash
python3 scripts/validate_adapter_policy.py docs/adapters/policy.example.json
```

Check enabled adapters declare `license_spdx` (stdout JSON summary):

```bash
python3 scripts/check_adapter_policy.py
python3 scripts/check_adapter_policy.py 2>/dev/null | jq -e .policy_ok
```

Use `--policy PATH` for a non-default file.

Included in `./scripts/workflow_hygiene.sh` (static bundle before `agent_gate.sh`).

## Runtime (opt-in)

At boot, `space_bootstrap.build_runtime_config` loads policy and exposes fields on `/health`:

- `adapter_policy_path`, `adapter_policy_ok`, `adapter_policy_enforced`, `adapter_policy_violations`, `adapter_policy_enabled_count`

Environment:

| Variable | Effect |
|----------|--------|
| `PIXAL3D_ADAPTER_POLICY` | Path to policy JSON (default: `docs/adapters/policy.example.json`) |
| `PIXAL3D_ADAPTER_POLICY_ENFORCE=1` | Fail boot when enabled adapters exist and rembg models are not listed |

With the committed example policy, `/health` reports `adapter_policy_enabled_count: 2` and `adapter_policy_ok: true` when rembg models match the listed `hub_repo` values. Boot fails only when `PIXAL3D_ADAPTER_POLICY_ENFORCE=1` and a configured rembg model is not listed on an enabled adapter.

## Adapter entry shape

Each object in `adapters` requires `id` (string), `license_spdx` (string or null), and `enabled` (boolean). Enabled adapters must set a non-empty `license_spdx`.
