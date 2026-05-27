#!/usr/bin/env bash
# Operator pre-ship: static workflow hygiene, then hosted agent gate.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: scripts/pre_ship.sh [--parity] [--url URL] [--write-summary PATH]

  1. ./scripts/workflow_hygiene.sh [--parity]
  2. ./scripts/agent_gate.sh [--url URL] [--write-summary PATH]

  Exit 0 only if both succeed (agent gate overall_ok).

  See docs/workflow-hygiene.md and AGENTS.md.
EOF
}

HYGIENE_ARGS=()
GATE_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --parity)
      HYGIENE_ARGS+=(--parity)
      shift
      ;;
    --url)
      GATE_ARGS+=(--url "$2")
      shift 2
      ;;
    --write-summary)
      GATE_ARGS+=(--write-summary "$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

"${ROOT}/scripts/workflow_hygiene.sh" "${HYGIENE_ARGS[@]}"
exec "${ROOT}/scripts/agent_gate.sh" "${GATE_ARGS[@]}"
