#!/usr/bin/env bash
# Browser E2E: default gallery sample -> Generate -> GLB viewer (uses agent-browser CLI).
# Run before verify_hosted_space.sh --generate in the same session (see docs/SPACE_RECOVERY.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SPACE_URL="${PIXAL3D_SPACE_URL:-https://th3w1zard1-pixal3d.hf.space/}"
SAMPLE_SELECTOR=".example-item img[src*='0_img']"
PREVIEW_WAIT_SEC="${BROWSER_SMOKE_PREVIEW_WAIT_SEC:-60}"
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

if ! ab wait ".example-item" 30000 2>/dev/null; then
  echo "browser_glb_smoke: gallery did not load (.example-item timeout)" >&2
  exit 3
fi

if ! ab click "$SAMPLE_SELECTOR" 2>/dev/null; then
  echo "browser_glb_smoke: could not click gallery sample (selector: ${SAMPLE_SELECTOR})" >&2
  exit 3
fi

echo "==> Waiting for upload preview (max ${PREVIEW_WAIT_SEC}s)"
preview_ok=0
for ((i = 0; i < PREVIEW_WAIT_SEC; i += 2)); do
  if ab_bool "document.body?.dataset?.smokeFileReady === 'true' || !!document.getElementById('source-preview')?.src"; then
    preview_ok=1
    break
  fi
  sleep 2
done

if [[ "$preview_ok" -ne 1 ]]; then
  echo "browser_glb_smoke: source preview / file-ready marker never appeared" >&2
  exit 2
fi

sleep 5

echo "==> Waiting for Generate to unlock (max 90s)"
gen_ready=0
for ((i = 0; i < 90; i += 3)); do
  if ab_bool "!document.getElementById('generate-btn')?.disabled"; then
    gen_ready=1
    break
  fi
  sleep 3
done

if [[ "$gen_ready" -ne 1 ]]; then
  echo "browser_glb_smoke: Generate stayed disabled (runtime may still be warming)" >&2
  echo "browser_glb_smoke: forcing programmatic click; if this fails, sign in for higher quota" >&2
fi

echo "==> Starting generation (max ${GENERATE_WAIT_SEC}s for GLB or error)"
if ! ab_bool "!!document.getElementById('generate-btn')"; then
  echo "browser_glb_smoke: generate button missing from DOM" >&2
  exit 2
fi
ab eval "document.getElementById('generate-btn').click(); 'started'" >/dev/null

generation_started=0
for ((i = 0; i < 45; i += 3)); do
  if ab_bool "document.getElementById('loading-overlay')?.style?.display === 'flex'"; then
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
  echo "browser_glb_smoke: Generate did not start (no loading overlay within 45s)" >&2
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
