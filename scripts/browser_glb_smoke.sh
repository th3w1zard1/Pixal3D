#!/usr/bin/env bash
# Browser E2E: default gallery sample -> Generate -> GLB viewer (uses agent-browser CLI).
# Run before verify_hosted_space.sh --generate in the same session (see docs/SPACE_RECOVERY.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SPACE_URL="${PIXAL3D_SPACE_URL:-https://th3w1zard1-pixal3d.hf.space/}"
CLIENT_WAIT_SEC="${BROWSER_SMOKE_CLIENT_WAIT_SEC:-120}"
PREVIEW_WAIT_SEC="${BROWSER_SMOKE_PREVIEW_WAIT_SEC:-150}"
GENERATE_WAIT_SEC="${BROWSER_SMOKE_GENERATE_WAIT_SEC:-300}"
HEADED=0

usage() {
  cat <<'EOF'
Usage: scripts/browser_glb_smoke.sh [--url URL] [--headed] [--preview-wait SEC] [--generate-wait SEC]

Uses ?smoke=1 and repeated short __pixal3dSmokeAdvance() ticks (agent-browser CDP safe).
Exit 0 when GLB ready; 1 on viewer error; 2 on timeout; 3 on setup failure.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      SPACE_URL="${2:?missing URL}"
      shift 2
      ;;
    --headed) HEADED=1; shift ;;
    --preview-wait)
      PREVIEW_WAIT_SEC="${2:?missing seconds}"
      shift 2
      ;;
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
  if ab_bool "window.__pixal3dClientReady === true && typeof window.__pixal3dSmokeAdvance === 'function'"; then
    client_ok=1
    break
  fi
  sleep 3
done
if [[ "$client_ok" -ne 1 ]]; then
  echo "browser_glb_smoke: Gradio client / smoke hooks not ready" >&2
  exit 3
fi

echo "==> Waiting for ZeroGPU runtime (max ${CLIENT_WAIT_SEC}s)"
runtime_ok=0
for ((i = 0; i < CLIENT_WAIT_SEC; i += 3)); do
  if ab_bool "document.body?.dataset?.runtimeMode === 'zerogpu'"; then
    runtime_ok=1
    break
  fi
  sleep 3
done
if [[ "$runtime_ok" -ne 1 ]]; then
  echo "browser_glb_smoke: ZeroGPU runtime not ready" >&2
  exit 3
fi

if ! ab wait ".example-item" 30000 2>/dev/null; then
  echo "browser_glb_smoke: gallery did not load" >&2
  exit 3
fi

ab eval "window.__pixal3dSmokeReset('assets/images/0_img.png', ${PREVIEW_WAIT_SEC}, ${GENERATE_WAIT_SEC})" >/dev/null 2>&1 || true

TOTAL_WAIT=$((PREVIEW_WAIT_SEC + GENERATE_WAIT_SEC + 60))
echo "==> Smoke advance ticks (max ${TOTAL_WAIT}s, preview ${PREVIEW_WAIT_SEC}s + generate ${GENERATE_WAIT_SEC}s)"
last=""
for ((i = 0; i < TOTAL_WAIT; i += 3)); do
  tick="$(ab_text "typeof window.__pixal3dSmokeAdvance === 'function' ? window.__pixal3dSmokeAdvance() : 'no-hook'")"
  if [[ -n "$tick" && "$tick" != "$last" ]]; then
    echo "browser_glb_smoke: tick=${tick} (${i}s)"
    last="$tick"
  fi

  if [[ "$tick" == "glb-ready" ]]; then
    src="$(ab_text "document.getElementById('main-3d-viewer')?.src || ''")"
    marker="$(ab_text "document.body?.dataset?.smokeGlbReady || ''")"
    echo "OK: GLB ready in browser"
    [[ -n "$marker" ]] && echo "marker: data-smoke-glb-ready=${marker}"
    [[ -n "$src" ]] && echo "src: $src"
    exit 0
  fi

  if [[ "$tick" == error:* ]]; then
    echo "browser_glb_smoke: ${tick}" >&2
    exit 1
  fi

  if [[ "$tick" == timeout:* ]]; then
    echo "browser_glb_smoke: ${tick}" >&2
    exit 2
  fi

  sleep 3
done

echo "browser_glb_smoke: timed out (last tick=${last:-none})" >&2
exit 2
