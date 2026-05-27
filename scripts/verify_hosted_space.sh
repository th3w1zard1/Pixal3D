#!/usr/bin/env bash
# Run hosted Space verification in the recommended order (parity → health/HTML → optional generate).
# Run browser E2E separately before --generate when validating both in one session (see docs/SPACE_RECOVERY.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_GENERATE=0
RUN_BROWSER=0
SPACE_URL="${PIXAL3D_SPACE_URL:-https://th3w1zard1-pixal3d.hf.space/}"

usage() {
  cat <<'EOF'
Usage: scripts/verify_hosted_space.sh [--browser] [--generate] [--url URL]

  Default: parity check + live health/HTML smoke.
  --browser: run ./scripts/browser_glb_smoke.sh after health/HTML (needs agent-browser).
  --generate: also run space_smoke.py --generate (needs venv + gradio_client; uses ZeroGPU quota).

  Do not combine --browser and --generate. Run browser before --generate in the same session.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --browser) RUN_BROWSER=1; shift ;;
    --generate) RUN_GENERATE=1; shift ;;
    --url)
      SPACE_URL="${2:?missing URL}"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "$RUN_BROWSER" -eq 1 && "$RUN_GENERATE" -eq 1 ]]; then
  echo "verify_hosted_space: --browser and --generate cannot be used together" >&2
  usage >&2
  exit 2
fi

echo "==> Repo parity (github vs HF Space)"
python3 scripts/check_repo_parity.py

echo "==> Live health + HTML smoke: ${SPACE_URL}"
python3 scripts/space_smoke.py --url "$SPACE_URL" --health-only --html-check

if [[ "$RUN_BROWSER" -eq 1 ]]; then
  echo "==> Browser GLB smoke (run before --generate in the same session)"
  browser_args=(--url "$SPACE_URL")
  set +e
  "${ROOT}/scripts/browser_glb_smoke.sh" "${browser_args[@]}"
  browser_exit=$?
  set -e
  if [[ "$browser_exit" -eq 0 ]]; then
    echo "OK: browser smoke complete (GLB)"
  elif [[ "$browser_exit" -eq 1 ]]; then
    echo "OK: browser smoke complete (explicit quota/error — path verified)"
  else
    echo "verify_hosted_space: browser smoke failed (exit ${browser_exit})" >&2
    exit "$browser_exit"
  fi
fi

if [[ "$RUN_GENERATE" -eq 1 ]]; then
  echo "==> Live generate smoke (ZeroGPU quota; ~2-3 min)"
  VENV="${ROOT}/.venv"
  if [[ ! -x "${VENV}/bin/python" ]]; then
    python3 -m venv "$VENV"
    "${VENV}/bin/pip" install -q -r scripts/smoke-requirements.txt
  fi
  "${VENV}/bin/python" scripts/space_smoke.py --url "$SPACE_URL" --generate
fi

if [[ "$RUN_BROWSER" -eq 0 ]]; then
  cat <<'EOF'

Browser E2E (run before --generate in the same session):
  ./scripts/browser_glb_smoke.sh [--url URL]
  Or: ./scripts/verify_hosted_space.sh --browser [--url URL]

EOF
fi

echo "OK: hosted verification complete"
