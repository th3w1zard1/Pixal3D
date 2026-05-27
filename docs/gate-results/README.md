# Agent gate results (optional)

The post-recovery agent gate can persist its JSON summary for auditing:

```bash
./scripts/agent_gate.sh --write-summary docs/gate-results/latest.json
```

`latest.json` is gitignored. The gate schema is `pixal3d-agent-gate/2` (`schema_version` field). Each summary includes `checked_at` (UTC) and `git_head` (short SHA). See `example.json` for the field shape.

Parse without writing a file:

```bash
./scripts/agent_gate.sh 2>/dev/null | jq .
```

Validate a saved summary:

```bash
python3 scripts/validate_gate_json.py docs/gate-results/latest.json
```

`--write-summary` runs this validator automatically after writing the file.
