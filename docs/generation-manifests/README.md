# Generation smoke manifests (optional)

After a successful `space_smoke.py --generate` run, persist a schema-stable manifest for auditing:

```bash
python scripts/space_smoke.py --generate --write-manifest docs/generation-manifests/latest.json
```

`latest.json` is gitignored. Schema: `pixal3d-generation-smoke/1` (`schema_version` field). Fields include `checked_at` (UTC), `git_head`, `url`, `generate_ok`, deliverable hints (`glb_path`, `extract_available`), and `warmup_skipped`. See `example.json` for the shape.

Validate a saved manifest:

```bash
python3 scripts/validate_generation_manifest.py docs/generation-manifests/latest.json
```

`--write-manifest` runs the validator after writing the file. Do not combine this CLI generate smoke with the browser agent gate in the same session (ZeroGPU quota).
