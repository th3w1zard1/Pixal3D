#!/usr/bin/env bash
# Run hosted Space verification in the recommended order (parity → health/HTML → optional generate).
# Run browser E2E separately before --generate when validating both in one session (see docs/SPACE_RECOVERY.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_GENERATE=0
RUN_BROWSER=0
SUMMARY_JSON=0
SUMMARY_WRITE_PATH=""
SPACE_URL="${PIXAL3D_SPACE_URL:-https://th3w1zard1-pixal3d.hf.space/}"
VERIFY_BROWSER_EXIT=""
VERIFY_PARITY_OK=0
VERIFY_HEALTH_OK=0

log() {
  if [[ "$SUMMARY_JSON" -eq 1 ]]; then
    echo "$@" >&2
  else
    echo "$@"
  fi
}

usage() {
  cat <<'EOF'
Usage: scripts/verify_hosted_space.sh [--browser] [--generate] [--summary-json] [--write-summary PATH] [--url URL]

  Default: parity check + live health/HTML smoke.
  --browser: run ./scripts/browser_glb_smoke.sh after health/HTML (needs agent-browser).
  --generate: also run space_smoke.py --generate (needs venv + gradio_client; uses ZeroGPU quota).
  --summary-json: write only the JSON summary to stdout (progress and browser output go to stderr).
  --write-summary PATH: also write the JSON summary to PATH (requires --summary-json). Exit 0 iff overall_ok.

  Do not combine --browser and --generate. Run browser before --generate in the same session.
  Canonical agent entrypoint: ./scripts/agent_gate.sh
EOF
}

emit_summary_json() {
  [[ "$SUMMARY_JSON" -eq 1 ]] || return 0
  export VERIFY_SPACE_URL="$SPACE_URL"
  export VERIFY_BROWSER_RAN="$RUN_BROWSER"
  export VERIFY_BROWSER_EXIT
  export VERIFY_PARITY_OK
  export VERIFY_HEALTH_OK
  local summary_tmp
  summary_tmp="$(mktemp "${TMPDIR:-/tmp}/verify-gate-summary.XXXXXX")"
  export VERIFY_GIT_HEAD="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || true)"
  python3 <<'PY' >"$summary_tmp"
import datetime
import json
import os

browser_ran = os.environ.get("VERIFY_BROWSER_RAN") == "1"
raw_exit = os.environ.get("VERIFY_BROWSER_EXIT", "")
browser_exit = int(raw_exit) if raw_exit != "" else None
parity_ok = os.environ.get("VERIFY_PARITY_OK") == "1"
health_ok = os.environ.get("VERIFY_HEALTH_OK") == "1"
overall_ok = parity_ok and health_ok and (
    not browser_ran or browser_exit in (0, 1)
)
print(
    json.dumps(
        {
            "schema_version": "pixal3d-agent-gate/1",
            "checked_at": datetime.datetime.now(datetime.timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "git_head": os.environ.get("VERIFY_GIT_HEAD") or None,
            "url": os.environ.get("VERIFY_SPACE_URL", ""),
            "parity_ok": parity_ok,
            "health_ok": health_ok,
            "browser_ran": browser_ran,
            "browser_exit": browser_exit,
            "overall_ok": overall_ok,
        },
        indent=2,
    )
)
PY
  cat "$summary_tmp"
  if [[ -n "$SUMMARY_WRITE_PATH" ]]; then
    mkdir -p "$(dirname "$SUMMARY_WRITE_PATH")"
    cp "$summary_tmp" "$SUMMARY_WRITE_PATH"
  fi
  python3 -c "import json,sys; d=json.load(open('$summary_tmp')); sys.exit(0 if d.get('overall_ok') else 1)"
  local gate_exit=$?
  rm -f "$summary_tmp"
  return "$gate_exit"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --browser) RUN_BROWSER=1; shift ;;
    --generate) RUN_GENERATE=1; shift ;;
    --summary-json) SUMMARY_JSON=1; shift ;;
    --write-summary)
      SUMMARY_WRITE_PATH="${2:?missing path}"
      shift 2
      ;;
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

if [[ -n "$SUMMARY_WRITE_PATH" && "$SUMMARY_JSON" -eq 0 ]]; then
  echo "verify_hosted_space: --write-summary requires --summary-json" >&2
  exit 2
fi

log "==> Repo parity (github vs HF Space)"
if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  python3 scripts/check_repo_parity.py >&2
else
  python3 scripts/check_repo_parity.py
fi
VERIFY_PARITY_OK=1

log "==> Live health + HTML smoke: ${SPACE_URL}"
if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  python3 scripts/space_smoke.py --url "$SPACE_URL" --health-only --html-check >&2
else
  python3 scripts/space_smoke.py --url "$SPACE_URL" --health-only --html-check
fi
VERIFY_HEALTH_OK=1

if [[ "$RUN_BROWSER" -eq 1 ]]; then
  log "==> Browser GLB smoke (run before --generate in the same session)"
  browser_args=(--url "$SPACE_URL")
  set +e
  if [[ "$SUMMARY_JSON" -eq 1 ]]; then
    "${ROOT}/scripts/browser_glb_smoke.sh" "${browser_args[@]}" >&2
  else
    "${ROOT}/scripts/browser_glb_smoke.sh" "${browser_args[@]}"
  fi
  VERIFY_BROWSER_EXIT=$?
  set -e
  if [[ "$VERIFY_BROWSER_EXIT" -eq 0 ]]; then
    log "OK: browser smoke complete (GLB)"
  elif [[ "$VERIFY_BROWSER_EXIT" -eq 1 ]]; then
    log "OK: browser smoke complete (explicit quota/error — path verified)"
  else
    echo "verify_hosted_space: browser smoke failed (exit ${VERIFY_BROWSER_EXIT})" >&2
    emit_summary_json || exit 1
    exit 1
  fi
fi

if [[ "$RUN_GENERATE" -eq 1 ]]; then
  log "==> Live generate smoke (ZeroGPU quota; ~2-3 min)"
  VENV="${ROOT}/.venv"
  if [[ ! -x "${VENV}/bin/python" ]]; then
    python3 -m venv "$VENV"
    "${VENV}/bin/pip" install -q -r scripts/smoke-requirements.txt
  fi
  if [[ "$SUMMARY_JSON" -eq 1 ]]; then
    "${VENV}/bin/python" scripts/space_smoke.py --url "$SPACE_URL" --generate >&2
  else
    "${VENV}/bin/python" scripts/space_smoke.py --url "$SPACE_URL" --generate
  fi
fi

if [[ "$RUN_BROWSER" -eq 0 ]]; then
  log ""
  log "Browser E2E (run before --generate in the same session):"
  log "  ./scripts/browser_glb_smoke.sh [--url URL]"
  log "  Or: ./scripts/agent_gate.sh  /  verify_hosted_space.sh --browser [--url URL]"
fi

emit_summary_json || exit 1
log "OK: hosted verification complete"
