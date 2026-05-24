#!/usr/bin/env bash
# Browser E2E: default gallery sample -> Generate -> GLB viewer (uses agent-browser CLI).
# Run before verify_hosted_space.sh --generate in the same session (see docs/SPACE_RECOVERY.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SPACE_URL="${PIXAL3D_SPACE_URL:-https://th3w1zard1-pixal3d.hf.space/}"
if [[ "$SPACE_URL" != *smoke=1* ]]; then
  if [[ "$SPACE_URL" == *"?"* ]]; then
    SPACE_URL="${SPACE_URL}&smoke=1"
  else
    SPACE_URL="${SPACE_URL%/}?smoke=1"
  fi
fi
SAMPLE_SELECTOR=".example-item img[src*='0_img']"
CLIENT_WAIT_SEC="${BROWSER_SMOKE_CLIENT_WAIT_SEC:-120}"
PREVIEW_WAIT_SEC="${BROWSER_SMOKE_PREVIEW_WAIT_SEC:-90}"
GENERATE_WAIT_SEC="${BROWSER_SMOKE_GENERATE_WAIT_SEC:-300}"
HEADED=0

usage() {
  cat <<'EOF'
Usage: scripts/browser_glb_smoke.sh [--url URL] [--headed] [--preview-wait SEC] [--generate-wait SEC]

Automates browser gallery -> Generate -> GLB on the hosted Space (agent-browser required).
Exit 0 when GLB is ready (body data-smoke-glb-ready, or step 3 + export visible); 1 on viewer error;
2 on timeout; 3 on setup failure.

Cold ZeroGPU runs often need 300s+ wall clock. Run before verify_hosted_space.sh --generate in one session.
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
  ab eval "$js" 2>/dev/null | tr -d '\n' | sed 's/^"//;s/"$//'
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
  echo "browser_glb_smoke: Gradio client not ready (__pixal3dRunGeneration missing)" >&2
  exit 3
fi

echo "==> Waiting for ZeroGPU runtime (max ${CLIENT_WAIT_SEC}s, skip cpu→gpu reload race)"
runtime_ok=0
for ((i = 0; i < CLIENT_WAIT_SEC; i += 3)); do
  if ab_bool "document.body?.dataset?.runtimeMode === 'zerogpu'"; then
    runtime_ok=1
    break
  fi
  sleep 3
done
if [[ "$runtime_ok" -ne 1 ]]; then
  echo "browser_glb_smoke: ZeroGPU runtime not reported yet (data-runtime-mode)" >&2
  exit 3
fi

if ! ab wait ".example-item" 30000 2>/dev/null; then
  echo "browser_glb_smoke: gallery did not load (.example-item timeout)" >&2
  exit 3
fi

sample_ready_js="document.body?.dataset?.smokeSampleLoad === 'done'"

echo "==> Loading default gallery sample via smoke API"
if ab_bool "typeof window.__pixal3dLoadSamplePath === 'function'"; then
  ab eval "(async () => { try { await window.__pixal3dLoadSamplePath('assets/images/0_img.png'); return 'ok'; } catch (e) { return 'err'; } })()" >/dev/null 2>&1 || true
else
  if ! ab click "$SAMPLE_SELECTOR" 2>/dev/null; then
    echo "browser_glb_smoke: could not load default sample" >&2
    exit 3
  fi
fi

echo "==> Waiting for sample file + preview (max ${PREVIEW_WAIT_SEC}s)"
preview_ok=0
for ((i = 0; i < PREVIEW_WAIT_SEC; i += 2)); do
  load_err="$(ab_text "document.body?.dataset?.smokeLoadError || ''")"
  if [[ -n "$load_err" ]]; then
    echo "browser_glb_smoke: sample load error (${load_err})" >&2
    exit 2
  fi
  if ab_bool "$sample_ready_js"; then
    preview_ok=1
    break
  fi
  if ab_bool "document.body?.dataset?.smokeFileReady === 'true' && !!document.getElementById('source-preview')?.src"; then
    preview_ok=1
    break
  fi
  sleep 2
done

if [[ "$preview_ok" -ne 1 ]]; then
  echo "browser_glb_smoke: smoke API load slow; clicking gallery sample" >&2
  ab click "$SAMPLE_SELECTOR" 2>/dev/null || true
  for ((i = 0; i < 60; i += 2)); do
    load_err="$(ab_text "document.body?.dataset?.smokeLoadError || ''")"
    if [[ -n "$load_err" ]]; then
      echo "browser_glb_smoke: sample load error (${load_err})" >&2
      exit 2
    fi
    if ab_bool "$sample_ready_js"; then
      preview_ok=1
      break
    fi
    if ab_bool "document.body?.dataset?.smokeFileReady === 'true' && !!document.getElementById('source-preview')?.src"; then
      preview_ok=1
      break
    fi
    sleep 2
  done
fi

if [[ "$preview_ok" -ne 1 ]]; then
  echo "browser_glb_smoke: sample file not ready (data-smoke-sample-load never set)" >&2
  exit 2
fi

sleep 3

echo "==> Waiting for generation hook after upload (max 60s)"
hook_ok=0
for ((i = 0; i < 60; i += 3)); do
  if ab_bool "typeof window.__pixal3dRunGeneration === 'function'"; then
    hook_ok=1
    break
  fi
  sleep 3
done

if [[ "$hook_ok" -ne 1 ]]; then
  echo "browser_glb_smoke: generation hook missing (page may have reloaded)" >&2
  exit 3
fi

echo "==> Starting generation (max ${GENERATE_WAIT_SEC}s for GLB or error)"
ab eval "window.__pixal3dRunGeneration(); 'started'" >/dev/null

generation_started=0
for ((i = 0; i < 60; i += 3)); do
  if ab_bool "document.body?.dataset?.smokeGenerationActive === 'true'"; then
    generation_started=1
    break
  fi
  if ab_bool "$glb_ready_js"; then
    generation_started=1
    break
  fi
  sleep 3
done

if [[ "$generation_started" -ne 1 ]]; then
  if ab_bool "document.body?.dataset?.smokeGenerationRequested === 'true'"; then
    abort="$(ab_text "document.body?.dataset?.smokeGenerationAbort || 'unknown'")"
    echo "browser_glb_smoke: generation aborted before loading (${abort})" >&2
  else
    echo "browser_glb_smoke: Generate did not start (hook did not run startGeneration)" >&2
  fi
  err_hint="$(ab_text "document.getElementById('viewer-error-message')?.textContent?.trim() || ''")"
  [[ -n "$err_hint" ]] && echo "browser_glb_smoke: viewer message: ${err_hint}" >&2
  exit 2
fi

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

if ab_bool "document.getElementById('loading-overlay')?.style?.display === 'flex'"; then
  echo "browser_glb_smoke: generation still running (try --generate-wait 360 or fresh ZeroGPU quota)" >&2
else
  echo "browser_glb_smoke: timed out after ${GENERATE_WAIT_SEC}s with no GLB ready signal" >&2
fi
exit 2
