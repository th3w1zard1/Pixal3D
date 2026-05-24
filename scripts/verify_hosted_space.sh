#!/usr/bin/env bash
# Run hosted Space verification in the recommended order (parity → health/HTML → optional generate).
# Run browser E2E separately before --generate when validating both in one session (see docs/SPACE_RECOVERY.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_GENERATE=0
SPACE_URL="${PIXAL3D_SPACE_URL:-https://th3w1zard1-pixal3d.hf.space/}"

usage() {
  cat <<'EOF'
Usage: scripts/verify_hosted_space.sh [--generate] [--url URL]

  Default: parity check + live health/HTML smoke.
  --generate: also run space_smoke.py --generate (needs venv + gradio_client; uses ZeroGPU quota).

  Browser default-sample E2E is not automated here; run it before --generate in the same session.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --generate) RUN_GENERATE=1; shift ;;
    --url)
      SPACE_URL="${2:?missing URL}"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

echo "==> Repo parity (github vs HF Space)"
python3 scripts/check_repo_parity.py

echo "==> Live health + HTML smoke: ${SPACE_URL}"
python3 scripts/space_smoke.py --url "$SPACE_URL" --health-only --html-check

if [[ "$RUN_GENERATE" -eq 1 ]]; then
  echo "==> Live generate smoke (ZeroGPU quota; ~2-3 min)"
  VENV="${ROOT}/.venv"
  if [[ ! -x "${VENV}/bin/python" ]]; then
    python3 -m venv "$VENV"
    "${VENV}/bin/pip" install -q -r scripts/smoke-requirements.txt
  fi
  "${VENV}/bin/python" scripts/space_smoke.py --url "$SPACE_URL" --generate
fi

echo "OK: hosted verification complete"
