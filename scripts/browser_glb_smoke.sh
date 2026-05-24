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

Automates browser gallery -> Generate -> GLB on the hosted Space (agent-browser required).
Uses ?smoke=1 to skip cpu→zerogpu reload. Exit 0 when GLB ready; 1 viewer error; 2 timeout; 3 setup.
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

echo "==> Loading sample in-page (max ${PREVIEW_WAIT_SEC}s)"
load_result="$(ab_text "(async () => {
  if (typeof window.__pixal3dLoadSamplePath !== 'function') return 'no-hook';
  void window.__pixal3dLoadSamplePath('assets/images/0_img.png');
  const deadline = Date.now() + ${PREVIEW_WAIT_SEC}000;
  while (Date.now() < deadline) {
    const status = window.__pixal3dSmokeSampleStatus || document.body.dataset.smokeSampleLoad || '';
    if (status === 'done') break;
    if (String(status).startsWith('err:')) return status;
    const loadErr = document.body.dataset.smokeLoadError || '';
    if (loadErr) return 'err:' + loadErr;
    await new Promise((r) => setTimeout(r, 500));
  }
  if ((window.__pixal3dSmokeSampleStatus || document.body.dataset.smokeSampleLoad || '') !== 'done') {
    return 'timeout';
  }
  if (typeof window.__pixal3dRunGeneration === 'function') {
    window.__pixal3dRunGeneration();
    return 'started';
  }
  return 'no-generation-hook';
})()")"
echo "browser_glb_smoke: load/generate start result=${load_result}"
if [[ "$load_result" != "started" ]]; then
  echo "browser_glb_smoke: sample load or generate start failed (${load_result})" >&2
  exit 2
fi

echo "==> Waiting for GLB (max ${GENERATE_WAIT_SEC}s)"

for ((i = 0; i < GENERATE_WAIT_SEC; i += 5)); do
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

  sleep 5
done

echo "browser_glb_smoke: timed out after ${GENERATE_WAIT_SEC}s" >&2
exit 2
