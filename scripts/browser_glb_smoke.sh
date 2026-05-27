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

Uses ?smoke=1 and in-page await loops (agent-browser does not run async work between evals).
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
  if ab_bool "window.__pixal3dClientReady === true && typeof window.__pixal3dLoadSamplePath === 'function'"; then
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
  const path = 'assets/images/0_img.png';
  const deadline = Date.now() + ${PREVIEW_WAIT_SEC}000;
  while (Date.now() < deadline) {
    if (typeof window.__pixal3dTryGallerySampleSync === 'function' && window.__pixal3dTryGallerySampleSync(path)) {
      return 'done';
    }
    document.querySelector('.example-item img[src*=\"0_img\"]')?.closest('.example-item')?.click();
    if (typeof window.__pixal3dLoadSamplePath === 'function') void window.__pixal3dLoadSamplePath(path);
    const st = window.__pixal3dSmokeSampleStatus || document.body.dataset.smokeSampleLoad || '';
    if (st === 'done' || document.body.dataset.smokeSampleLoad === 'done') return 'done';
    if (String(st).startsWith('err:')) return st;
    await new Promise((r) => setTimeout(r, 500));
  }
  return 'timeout:sample';
})()")"
echo "browser_glb_smoke: load=${load_result}"
if [[ "$load_result" != "done" ]]; then
  echo "browser_glb_smoke: sample load failed (${load_result})" >&2
  exit 2
fi

echo "==> Generate + GLB poll in-page (max ${GENERATE_WAIT_SEC}s)"
if ! ab_bool "typeof window.__pixal3dRunGeneration === 'function'"; then
  gen_result="no-generation-hook"
else
  ab eval "window.__pixal3dRunGeneration()" >/dev/null 2>&1 || true
  gen_result="pending"
  gen_deadline=$(( $(date +%s) + GENERATE_WAIT_SEC ))
  while [[ $(date +%s) -lt $gen_deadline ]]; do
    gen_result="$(ab_text "(() => {
      if (document.getElementById('viewer-error')?.classList.contains('show')) {
        const msg = document.getElementById('viewer-error-message')?.textContent?.trim() || 'viewer-error';
        return 'error:' + msg;
      }
      if (document.body?.dataset?.smokeGlbReady === 'true') return 'glb-ready';
      const step3 = document.getElementById('step-3')?.classList.contains('active');
      const extract = document.getElementById('extract-btn');
      const extractOn = extract && (extract.style.display === 'flex' || extract.style.display === 'block');
      const viewer = document.getElementById('main-3d-viewer');
      const viewerOn = viewer && viewer.style.visibility !== 'hidden' && (viewer.src || '').length > 8;
      if (step3 && extractOn && viewerOn) return 'glb-ready';
      return 'pending';
    })()")"
    if [[ -z "$gen_result" ]]; then
      gen_result="pending"
    fi
    if [[ "$gen_result" == "glb-ready" || "$gen_result" == error:* ]]; then
      break
    fi
    sleep 5
  done
  if [[ "$gen_result" == "pending" ]]; then
    gen_result="timeout:glb"
  fi
fi

echo "browser_glb_smoke: generate=${gen_result}"
if [[ "$gen_result" == "glb-ready" ]]; then
  echo "OK: GLB ready in browser"
  exit 0
fi
if [[ "$gen_result" == error:* ]]; then
  echo "browser_glb_smoke: viewer error (${gen_result#error:})" >&2
  exit 1
fi
echo "browser_glb_smoke: failed (${gen_result})" >&2
exit 2
