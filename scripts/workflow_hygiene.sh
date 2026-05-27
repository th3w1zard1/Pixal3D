#!/usr/bin/env bash
# Fast static workflow hygiene checks (no browser, no generate smoke).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

RUN_PARITY=0

usage() {
  cat <<'EOF'
Usage: scripts/workflow_hygiene.sh [--parity] [--help]

  Runs static hygiene checks (example JSON schemas, adapter policy check,
  GitHub workflow YAML). Does not call the hosted Space or agent-browser.

  Optional:
    --parity    Also run scripts/check_repo_parity.py (needs github + hf remotes)

  Typical order before shipping:
    ./scripts/workflow_hygiene.sh
    ./scripts/agent_gate.sh
EOF
}

log() {
  printf '%s\n' "$*" >&2
}

run_step() {
  log "== $*"
  "$@"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --parity) RUN_PARITY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

PYTHON="${PYTHON:-python3}"

run_step "${PYTHON}" scripts/validate_gate_json.py docs/gate-results/example.json
run_step "${PYTHON}" scripts/validate_generation_manifest.py docs/generation-manifests/example.json
run_step "${PYTHON}" scripts/validate_adapter_policy.py docs/adapters/policy.example.json
run_step "${PYTHON}" scripts/validate_generation_run_json.py docs/generation-runs/example.json
run_step "${PYTHON}" scripts/check_adapter_policy.py >/dev/null
if "${PYTHON}" -c "import yaml" 2>/dev/null; then
  run_step "${PYTHON}" scripts/check_workflow_yaml.py
else
  log "SKIP: check_workflow_yaml.py (install PyYAML, e.g. python -m pip install PyYAML==6.0.2)"
fi

if [[ "${RUN_PARITY}" -eq 1 ]]; then
  run_step "${PYTHON}" scripts/check_repo_parity.py
fi

log "Workflow hygiene static checks: OK"
