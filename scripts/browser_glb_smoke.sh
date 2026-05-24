#!/usr/bin/env bash
# Browser E2E: default gallery sample -> Generate -> GLB viewer (uses agent-browser CLI).
# Run before verify_hosted_space.sh --generate in the same session (see docs/SPACE_RECOVERY.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SPACE_URL="${PIXAL3D_SPACE_URL:-https://th3w1zard1-pixal3d.hf.space/}"

CLIENT_WAIT_SEC="${BROWSER_SMOKE_CLIENT_WAIT_SEC:-120}"
GENERATE_WAIT_SEC="${BROWSER_SMOKE_GENERATE_WAIT_SEC:-300}"
HEADED=0

usage() {
  cat <<'EOF'
Usage: scripts/browser_glb_smoke.sh [--url URL] [--headed] [--generate-wait SEC]

Opens the Space with ?smoke=1&autoload=1&autogen=1 so the page loads the default
sample and starts generation in-process (agent-browser does not keep async eval alive).

Exit 0 when GLB is ready; 1 on viewer error; 2 on timeout; 3 on setup failure.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      SPACE_URL="${2:?missing URL}"
      shift 2
      ;;
    --headed) HEADED=1; shift ;;
    --generate-wait)
      GENERATE_WAIT_SEC="${2:?missing seconds}"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 3 ;;
  esac
done

append_query() {
  local key="$1"
  local val="$2"
  if [[ "$SPACE_URL" == *"${key}="* ]]; then
    return
  fi
  if [[ "$SPACE_URL" == *"?"* ]]; then
    SPACE_URL="${SPACE_URL}&${key}=${val}"
  else
    SPACE_URL="${SPACE_URL%/}?${key}=${val}"
  fi
}
append_query "smoke" "1"
append_query "autoload" "1"
append_query "autogen" "1"

if ! command -v agent-browser >/dev/null 2>&1; then
  echo "browser_glb_smoke: agent-browser not installed (see ce-setup / agent-browser docs)" >&2
  exit 3
fi

AB_OPTS=()
if [[ "$HEADED" -eq 1 ]]; then
  AB_OPTS+=(--headed)
fi

ab() {
  agent-browser "${AB_OPTS[@]}" "$@"
}

ab_bool() {
  local js="$1"
  local out
  out="$(ab eval "$js" 2>/dev/null | tr -d '\n' | sed 's/^"//;s/"$//')"
  [[ "$out" == "true" ]]
}

ab_text() {
  local js="$1"
  local out=""
  out="$(ab eval "$js" 2>/dev/null | tr -d '\n' | sed 's/^"//;s/"$//')" || true
  printf '%s' "$out"
}

glb_ready_js="(() => {
  if (document.body?.dataset?.smokeGlbReady === 'true') return true;
  const step3 = document.getElementById('step-3')?.classList.contains('active');
  const extract = document.getElementById('extract-btn');
  const extractOn = extract && (extract.style.display === 'flex' || extract.style.display === 'block');
  const viewer = document.getElementById('main-3d-viewer');
  const viewerOn = viewer && viewer.style.visibility !== 'hidden' && (viewer.src || '').length > 8;
  return !!(step3 && extractOn && viewerOn);
})()"

cleanup() {
  ab close 2>/dev/null || true
}
trap cleanup EXIT

echo "==> Browser GLB smoke: ${SPACE_URL}"
ab open "$SPACE_URL"
sleep 6

echo "==> Waiting for Gradio client (max ${CLIENT_WAIT_SEC}s)"
client_ok=0
for ((i = 0; i < CLIENT_WAIT_SEC; i += 3)); do
  if ab_bool "window.__pixal3dClientReady === true && typeof window.__pixal3dRunGeneration === 'function'"; then
    client_ok=1
    break
  fi
  sleep 3
done
if [[ "$client_ok" -ne 1 ]]; then
  echo "browser_glb_smoke: Gradio client not ready" >&2
  exit 3
fi

echo "==> Waiting for autoload + generation (max ${GENERATE_WAIT_SEC}s)"
for ((i = 0; i < GENERATE_WAIT_SEC; i += 5)); do
  load_status="$(ab_text "window.__pixal3dSmokeSampleStatus || ''")"
  if [[ "$load_status" == err:* ]]; then
    echo "browser_glb_smoke: autoload failed (${load_status})" >&2
    exit 2
  fi

  if ab_bool "document.getElementById('viewer-error')?.classList.contains('show')"; then
    err_msg="$(ab_text "document.getElementById('viewer-error-message')?.textContent?.trim() || ''")"
    echo "browser_glb_smoke: viewer error: ${err_msg}" >&2
    exit 1
  fi

  if ab_bool "$glb_ready_js"; then
    src="$(ab_text "document.getElementById('main-3d-viewer')?.src || ''")"
    marker="$(ab_text "document.body?.dataset?.smokeGlbReady || ''")"
    echo "OK: GLB ready in browser"
    [[ -n "$marker" ]] && echo "marker: data-smoke-glb-ready=${marker}"
    [[ -n "$src" ]] && echo "src: $src"
    exit 0
  fi

  if ab_bool "document.body?.dataset?.smokeGenerationActive === 'true'"; then
    echo "… generation active (${i}s)"
  elif [[ "$(ab_text "window.__pixal3dSmokeSampleStatus || ''")" == "done" ]]; then
    echo "… sample loaded, waiting for GLB (${i}s)"
  fi

  sleep 5
done

if ab_bool "document.getElementById('loading-overlay')?.style?.display === 'flex'"; then
  echo "browser_glb_smoke: generation still running (try --generate-wait 360)" >&2
else
  abort="$(ab_text "document.body?.dataset?.smokeGenerationAbort || ''")"
  [[ -n "$abort" ]] && echo "browser_glb_smoke: generation abort=${abort}" >&2
  echo "browser_glb_smoke: timed out after ${GENERATE_WAIT_SEC}s" >&2
fi
exit 2
