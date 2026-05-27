# Agent gate results (optional)

The post-recovery agent gate can persist its JSON summary for auditing:

```bash
./scripts/agent_gate.sh --write-summary docs/gate-results/latest.json
```

`latest.json` is gitignored. The gate schema is `pixal3d-agent-gate/1` (`schema_version` field).

Parse without writing a file:

```bash
./scripts/agent_gate.sh 2>/dev/null | jq .
```
