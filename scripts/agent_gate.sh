#!/usr/bin/env bash
# Canonical post-recovery agent gate: parity + health/HTML + browser E2E + JSON summary.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: scripts/agent_gate.sh [--url URL]

  Runs verify_hosted_space.sh --browser --summary-json.
  Progress and browser logs go to stderr; stdout is JSON only.

  Parse result:
    ./scripts/agent_gate.sh 2>/dev/null | jq -e .overall_ok

  Browser exit 1 with explicit ZeroGPU quota copy is a verified pass (overall_ok true).
  See docs/SPACE_RECOVERY.md and AGENTS.md.
EOF
}

for arg in "$@"; do
  case "$arg" in
    -h|--help) usage; exit 0 ;;
  esac
done

exec "${ROOT}/scripts/verify_hosted_space.sh" --browser --summary-json "$@"
