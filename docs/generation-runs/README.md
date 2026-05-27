# Generation run manifests (API)

Successful `/generate_3d` responses include a `generation_run` object with schema `pixal3d-generation-run/1`.

## Fields

| Field | Description |
|-------|-------------|
| `run_id` | UUID for this generation |
| `finished_at` | UTC timestamp when the run completed |
| `git_head` | Short git SHA at runtime (when available) |
| `session_id` | Client session id |
| `glb_path` | Deliverable GLB path when exported |
| `extract_available` | Whether Export can run on `state_path` |
| `preview_available` | Whether preview frames were rendered |
| `rembg_model` | Active rembg Hub repo |
| `requested_resolution` / `effective_resolution` | Resolution after normalization |

CLI smoke manifests use a separate schema: [generation-manifests/README.md](../generation-manifests/README.md) (`pixal3d-generation-smoke/1`).

## Validate

```bash
python3 scripts/validate_generation_run_json.py docs/generation-runs/example.json
```
