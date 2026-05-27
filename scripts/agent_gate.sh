#!/usr/bin/env bash
# Canonical post-recovery agent gate: parity + health/HTML + browser E2E + JSON summary.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${ROOT}/scripts/verify_hosted_space.sh" --browser --summary-json "$@"
